"""Execute the blueprint's actual templates and action tree with synthetic HA data.

This is an isolated regression harness, not a Home Assistant runtime or a device
test. Registry/state helpers are doubles. Unsupported actions fail explicitly.
Template results use literal parsing as HA does for dict/bool/number results.
"""

import ast
import logging
import math
from numbers import Number
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

from jinja2 import StrictUndefined
from jinja2.sandbox import SandboxedEnvironment
import yaml

ROOT = Path(__file__).resolve().parents[2]
BLUEPRINT = ROOT / "example/blueprint/automation/go-echarger-pv-surplus-data.yaml"


class Input(str):
    pass


class Loader(yaml.SafeLoader):
    pass


Loader.add_constructor("!input", lambda loader, node: Input(loader.construct_scalar(node)))


def is_number(value):
    # Contract of HA is_number: numeric conversion must be finite.
    try:
        return math.isfinite(float(value))
    except (ValueError, TypeError, OverflowError):
        return False


class BlueprintRun:
    def __init__(self, inputs=None, states=None, target="", connected="on",
                 registry=None, entries=None, daylight=True, second=0, trigger="tick"):
        self.document = yaml.load(BLUEPRINT.read_text(encoding="utf-8"), Loader=Loader)
        self.inputs = {}
        for name, value in self.document["blueprint"]["input"].items():
            for key, field in value.get("input", {name: value}).items():
                if "default" in field:
                    self.inputs[key] = field["default"]
        self.inputs.update(car_connected_entity={"entity_id": "binary_sensor.car_a"},
                           charger_config_entry=target, grid_single_entity="sensor.grid",
                           pv_entities=["sensor.pv"])
        self.inputs.update(inputs or {})
        self.states = {"binary_sensor.car_a": connected, "binary_sensor.car_b": connected,
                       "sensor.grid": "-1200", "sensor.pv": "2000"}
        self.states.update(states or {})
        self.registry = registry if registry is not None else {
            "binary_sensor.car_a": "entry_a", "binary_sensor.car_b": "entry_b"}
        self.entries = entries if entries is not None else {
            "entry_a": "goecharger_api2", "entry_b": "goecharger_api2"}
        self.daylight, self.trigger = daylight, trigger
        self.env = SandboxedEnvironment(undefined=StrictUndefined)
        self.env.globals.update(
            states=lambda entity: self.states.get(entity, "unknown"),
            expand=self.expand,
            config_entry_id=lambda entity: self.registry.get(entity),
            config_entry_attr=lambda entry, attr: self.entries.get(entry) if attr == "domain" else None,
            is_number=is_number,
            now=lambda: SimpleNamespace(second=second),
        )
        self.variables = {}
        self.calls = []
        self.stopped = None

    def expand(self, entities):
        if isinstance(entities, str):
            entities = [entities]
        return [SimpleNamespace(entity_id=entity, state=self.states[entity])
                for entity in entities if entity in self.states]

    def render(self, value):
        if isinstance(value, Input):
            return self.inputs[value]
        if isinstance(value, dict):
            return {key: self.render(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self.render(item) for item in value]
        if isinstance(value, str) and ("{{" in value or "{%" in value):
            rendered = self.env.from_string(value).render(self.variables).strip()
            try:
                return ast.literal_eval(rendered)
            except (ValueError, SyntaxError):
                return rendered
        return value

    def condition(self, condition):
        kind = condition["condition"]
        if kind == "template":
            result = self.render(condition["value_template"])
            assert isinstance(result, bool), result
            return result
        if kind == "trigger":
            return condition["id"] == self.trigger
        if kind == "sun":
            return self.daylight
        if kind == "and":
            return all(self.condition(item) for item in condition["conditions"])
        if kind == "not":
            return not any(self.condition(item) for item in condition["conditions"])
        raise AssertionError(f"Unsupported condition: {condition}")

    def actions(self, actions):
        for action in actions:
            if self.stopped:
                return
            if "if" in action:
                branch = "then" if all(self.condition(c) for c in action["if"]) else "else"
                self.actions(action.get(branch, []))
            elif "choose" in action:
                for choice in action["choose"]:
                    if all(self.condition(c) for c in choice["conditions"]):
                        self.actions(choice["sequence"])
                        break
            elif "stop" in action:
                self.stopped = action["stop"]
            elif "condition" in action:
                if not self.condition(action):
                    self.stopped = action.get("alias", "condition failed")
            elif "variables" in action:
                for key, value in action["variables"].items():
                    self.variables[key] = self.render(value)
            elif action.get("action") == "goecharger_api2.set_pv_data":
                payload = self.render(action["data"])
                assert isinstance(payload, dict)
                self.calls.append(payload)
            else:
                raise AssertionError(f"Unsupported action: {action}")

    def run(self):
        for key, value in self.document["variables"].items():
            self.variables[key] = self.render(value)
        self.actions(self.document["actions"])
        return self.calls


def dispatch(payload, available=("entry_a", "entry_b")):
    """Run the unmodified upstream service method with fake LAN coordinators.

    AST extraction avoids importing/starting the complete HA integration. The
    production method body is used verbatim; only external types/globals are stubbed.
    """
    tree = ast.parse((ROOT / "custom_components/goecharger_api2/service.py").read_text())
    service = next(node for node in tree.body if isinstance(node, ast.ClassDef)
                   and node.name == "GoeChargerApiV2Service")
    method = next(node for node in service.body if isinstance(node, ast.AsyncFunctionDef)
                  and node.name == "set_pv_data")
    module = ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[]))
    coordinators = {
        entry: SimpleNamespace(name=entry, _serial="example", intg_type="charger", mode="LAN",
                               async_write_key=AsyncMock(return_value={})) for entry in available
    }
    namespace = {"ServiceCall": object, "Number": Number, "WAN": "WAN",
                 "INTG_TYPE": SimpleNamespace(CHARGER=SimpleNamespace(value="charger")),
                 "Tag": SimpleNamespace(IDS=SimpleNamespace(key="ids")),
                 "_LOGGER": logging.getLogger(__name__),
                 "_COORDINATOR_PER_CONFIGENTRYID_MAP": coordinators}
    exec(compile(module, "upstream/service.py", "exec"), namespace)
    # All awaited calls are immediate AsyncMocks; no event loop or sockets are needed.
    coroutine = namespace["set_pv_data"](None, SimpleNamespace(data=payload, return_response=False))
    try:
        coroutine.send(None)
    except StopIteration:
        pass
    else:
        coroutine.close()
        raise AssertionError("Unexpected asynchronous I/O in the service double")
    return {entry: obj.async_write_key.call_args_list for entry, obj in coordinators.items()}
