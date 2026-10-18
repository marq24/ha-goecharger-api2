"""Input failures must not become plausible surplus or incomplete power sums."""
from collections import Counter

import pytest

from harness import BlueprintRun


BAD_VALUES = ["unknown", "unavailable", "not a number", "", "NaN", "inf", "-inf", "1e999"]


@pytest.mark.parametrize("bad", BAD_VALUES)
@pytest.mark.parametrize("source", ["sensor.grid", "sensor.pv", "sensor.battery"])
def test_bad_used_source_skips_whole_update(source, bad):
    run = BlueprintRun(inputs={"battery_entities": ["sensor.battery"]},
                       states={"sensor.battery": "0", source: bad})
    assert run.run() == []
    assert "measurement is invalid" in run.stopped


@pytest.mark.parametrize("input_name,value", [
    ("grid_single_entity", "sensor.missing"), ("pv_entities", ["sensor.missing"]),
    ("battery_entities", ["sensor.missing"]),
])
def test_missing_entity(input_name, value):
    assert BlueprintRun(inputs={input_name: value}).run() == []


@pytest.mark.parametrize("grid", ["0", "1200", "-1200"])
def test_real_zero_import_and_export(grid):
    payload = BlueprintRun(states={"sensor.grid": grid, "sensor.pv": "0"}).run()[0]
    assert payload == {"pgrid": int(grid), "ppv": 0, "pakku": 0}


def dual_inputs():
    return {"grid_single_entity": None, "grid_consumption_entity": "sensor.import",
            "grid_feedin_entity": "sensor.export"}


@pytest.mark.parametrize("missing", ["sensor.import", "sensor.export"])
def test_dual_missing_input_cannot_become_export(missing):
    states = {"sensor.import": "1500", "sensor.export": "1000", missing: "unavailable"}
    assert BlueprintRun(inputs=dual_inputs(), states=states).run() == []


def test_dual_valid():
    payload = BlueprintRun(inputs=dual_inputs(), states={
        "sensor.import": "1500", "sensor.export": "1000"}).run()[0]
    assert payload["pgrid"] == 500


@pytest.mark.parametrize("missing", ["grid_consumption_entity", "grid_feedin_entity"])
def test_incomplete_dual_does_not_fall_back_to_phases(missing):
    inputs = dict(dual_inputs(), grid_phase_entities=["sensor.l1", "sensor.l2", "sensor.l3"])
    inputs[missing] = None
    assert BlueprintRun(inputs=inputs, states={
        "sensor.l1": "-1000", "sensor.l2": "-1000", "sensor.l3": "-1000"}).run() == []


@pytest.mark.parametrize("missing_phase", ["sensor.l1", "sensor.l2", "sensor.l3"])
def test_missing_phase_never_yields_partial_sum(missing_phase):
    states = {"sensor.l1": "-1000", "sensor.l2": "-2000", "sensor.l3": "500",
              missing_phase: "unavailable"}
    run = BlueprintRun(inputs={"grid_single_entity": None,
        "grid_phase_entities": ["sensor.l1", "sensor.l2", "sensor.l3"]}, states=states)
    assert run.run() == []


@pytest.mark.parametrize("phases", [[], ["sensor.l1"], ["sensor.l1", "sensor.l2"],
    ["sensor.l1", "sensor.l2", "sensor.l3", "sensor.l4"], ["sensor.l1"] * 3])
def test_phase_method_requires_three_distinct_entities(phases):
    assert BlueprintRun(inputs={"grid_single_entity": None, "grid_phase_entities": phases},
                        states={f"sensor.l{i}": "0" for i in range(1, 5)}).run() == []


def test_three_phases_and_inversion():
    payload = BlueprintRun(inputs={"grid_single_entity": None,
        "grid_phase_entities": ["sensor.l1", "sensor.l2", "sensor.l3"],
        "grid_phases_invert": True}, states={
        "sensor.l1": "1000", "sensor.l2": "2000", "sensor.l3": "-500"}).run()[0]
    assert payload["pgrid"] == -2500


def test_unused_grid_inputs_do_not_block_selected_single():
    assert len(BlueprintRun(inputs={"grid_consumption_entity": "sensor.missing",
                                   "grid_phase_entities": ["sensor.missing"]}).run()) == 1


def test_failed_single_does_not_fall_back_to_healthy_dual():
    inputs = dict(dual_inputs(), grid_single_entity="sensor.missing")
    assert BlueprintRun(inputs=inputs, states={"sensor.import": "0", "sensor.export": "1000"}).run() == []


@pytest.mark.parametrize("enabled,entities", [(False, ["sensor.missing"]), (True, []), (False, [])])
def test_intentionally_absent_battery(enabled, entities):
    payload = BlueprintRun(inputs={"battery_enabled": enabled, "battery_entities": entities}).run()[0]
    assert payload["pakku"] == 0


@pytest.mark.parametrize("source_list", ["pv_entities", "battery_entities"])
def test_multiple_sources_must_all_be_available(source_list):
    assert BlueprintRun(inputs={source_list: ["sensor.first", "sensor.missing"]},
                        states={"sensor.first": "1200"}).run() == []


def test_empty_pv_is_invalid():
    assert BlueprintRun(inputs={"pv_entities": []}).run() == []


def test_multiple_sources_inversion_and_kw_conversion():
    payload = BlueprintRun(inputs={"power_multiplier": 1000,
        "grid_single_invert": True, "pv_entities": ["sensor.pv1", "sensor.pv2"],
        "pv_invert": True, "battery_entities": ["sensor.b1", "sensor.b2"],
        "battery_invert": True}, states={"sensor.grid": "1.25", "sensor.pv1": "-2",
        "sensor.pv2": "-0.75", "sensor.b1": "0.25", "sensor.b2": "0.5"}).run()[0]
    assert payload == {"pgrid": -1250, "ppv": 2750, "pakku": -750}


def test_rounding_after_conversion():
    payload = BlueprintRun(inputs={"power_multiplier": 1000}, states={
        "sensor.grid": "-0.1234", "sensor.pv": "0.5678"}).run()[0]
    assert payload["pgrid"] == -123
    assert payload["ppv"] == 568


@pytest.mark.parametrize("multiplier", [0, -1, "invalid", "NaN", "inf"])
def test_invalid_multiplier(multiplier):
    assert BlueprintRun(inputs={"power_multiplier": multiplier}).run() == []


@pytest.mark.parametrize("source", ["grid", "pv", "battery"])
def test_overflow_after_unit_conversion(source):
    assert BlueprintRun(inputs={"power_multiplier": 1000, "battery_entities": ["sensor.battery"]},
        states={"sensor.battery": "0", f"sensor.{source}": "1e308"}).run() == []


def test_overflow_of_sum():
    assert BlueprintRun(inputs={"pv_entities": ["sensor.first", "sensor.second"]},
                        states={"sensor.first": "1e308", "sensor.second": "1e308"}).run() == []


@pytest.mark.parametrize("target,entity", [("", "car_a"), ("entry_a", "car_a"), ("entry_b", "car_b")])
@pytest.mark.parametrize("trigger,connected", [("tick", "on"), ("sunset", "off")])
@pytest.mark.parametrize("bad", ["unavailable", "NaN", "inf"])
def test_night_and_sunset_zeros_survive_invalid_measurements(target, entity, trigger, connected, bad):
    run = BlueprintRun(target=target, daylight=False, trigger=trigger, connected=connected,
                       inputs={"car_connected_entity": {"entity_id": f"binary_sensor.{entity}"}},
                       states={"sensor.grid": bad, "sensor.pv": bad})
    payload = run.run()[0]
    assert (payload["pgrid"], payload["ppv"], payload["pakku"]) == (0, 0, 0)
    assert payload.get("configid", "") == target


def test_recovers_on_next_valid_tick():
    assert BlueprintRun(states={"sensor.grid": "unavailable"}).run() == []
    assert BlueprintRun(states={"sensor.grid": "-500"}).run()[0]["pgrid"] == -500


def test_validation_and_arithmetic_use_one_sample_per_source():
    run = BlueprintRun(inputs={"pv_entities": ["sensor.pv", "sensor.pv"]})
    reads = Counter()

    def changing_state(entity):
        reads[entity] += 1
        return run.states.get(entity, "unknown") if reads[entity] == 1 else "unavailable"

    run.env.globals["states"] = changing_state
    payload = run.run()[0]
    assert payload["pgrid"] == -1200
    assert payload["ppv"] == 4000  # Existing sum semantics are unchanged.
    assert reads == {"sensor.grid": 1, "sensor.pv": 1}
