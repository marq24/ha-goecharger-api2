"""Contract between the official go-eController key table and the integration.

Source of truth: `contract/controller_keys.json`, generated from `go-eController-API/apikeys-en.md` (see
`contract/generate_api_keys.py`). The charger contract in test_api_contract.py is built from the charger
table only, so before these tests the controller paths were not checked against any documentation.

Checks:
1. Every key a controller entity uses is documented for controllers.
2. Controller entities that write (switch, select, button) use keys the documentation marks as writable,
   and keys.py marks them as writeable as well.
3. Every key the code requests from a controller is documented. `cae`, `ecp` and `lcs` are requested but
   not documented; they are marked `needs_decision` (fails on purpose, not blocking) until someone has
   checked on a device whether they are leftovers or a documentation gap.
"""
import json
import re
from pathlib import Path

import pytest

from custom_components.goecharger_api2 import const as entity_const
from custom_components.goecharger_api2.pygoecharger_ha import const as bridge_const
from custom_components.goecharger_api2.pygoecharger_ha.keys import Tag

CONTROLLER_DOC = json.loads((Path(__file__).parent / "contract" / "controller_keys.json").read_text())["keys"]
TAGS = {tag.key: tag for tag in Tag}

# requested from a controller although the controller documentation does not list them
UNDOCUMENTED_REQUESTS = {"cae", "ecp", "lcs"}


def _keys(list_name):
    return sorted({d.key for d in getattr(entity_const, list_name)})


def _requested_keys():
    keys = set()
    for name in dir(bridge_const):
        value = getattr(bridge_const, name)
        if name.startswith("FILTER_CONTROLER_") and isinstance(value, str):
            keys |= {k for k in re.split(r"[,\s]+", value) if k}
    return keys


ENTITY_LISTS = ["CONTROLLER_BINARY_SENSORS", "CONTROLLER_BUTTONS", "CONTROLLER_NUMBER_SENSORS",
                "CONTROLLER_SELECT_SENSORS", "CONTROLLER_SENSOR_SENSORS", "CONTROLLER_SWITCH_SENSORS"]
WRITING_LISTS = ["CONTROLLER_BUTTONS", "CONTROLLER_NUMBER_SENSORS", "CONTROLLER_SELECT_SENSORS",
                 "CONTROLLER_SWITCH_SENSORS"]

ENTITY_KEYS = sorted({k for name in ENTITY_LISTS for k in _keys(name)})
WRITING_KEYS = sorted({k for name in WRITING_LISTS for k in _keys(name)})
REQUESTED = sorted(_requested_keys())


def test_contract_file_is_the_controller_table():
    assert len(CONTROLLER_DOC) == 82
    assert all(v["rw"] in ("R", "W", "R/W") for v in CONTROLLER_DOC.values())


def test_there_are_controller_entities_to_check():
    assert ENTITY_KEYS and WRITING_KEYS


@pytest.mark.parametrize("key", ENTITY_KEYS)
def test_controller_entity_key_is_documented(key):
    assert key in CONTROLLER_DOC, f"{key!r} is used by a controller entity but not in the controller key table"


@pytest.mark.parametrize("key", WRITING_KEYS)
def test_writing_controller_entity_uses_a_writable_key(key):
    assert "W" in CONTROLLER_DOC[key]["rw"], f"{key!r} is documented as {CONTROLLER_DOC[key]['rw']!r}"


@pytest.mark.parametrize("key", WRITING_KEYS)
def test_writing_controller_entity_key_is_writeable_in_keys_py(key):
    assert TAGS[key].writeable, f"{key!r} is written by a controller entity but keys.py says writeable=False"


@pytest.mark.parametrize("key", [pytest.param(k, id=k, marks=[pytest.mark.needs_decision] if k in UNDOCUMENTED_REQUESTS else [])
                                 for k in REQUESTED])
def test_key_requested_from_a_controller_is_documented(key):
    assert key in CONTROLLER_DOC, f"{key!r} is requested from controllers but not in the controller key table"


def test_undocumented_request_list_has_no_stale_entries():
    stale = sorted(k for k in UNDOCUMENTED_REQUESTS if k in CONTROLLER_DOC or k not in REQUESTED)
    assert stale == [], "documented now, or no longer requested: remove them from UNDOCUMENTED_REQUESTS"


def test_controller_does_not_get_the_temporary_current_limit():
    # answers the question in PR #177: neither `tcl` nor `cll` exist in the controller API
    assert "tcl" not in CONTROLLER_DOC and "cll" not in CONTROLLER_DOC
    assert "tcl" not in REQUESTED and "cll" not in REQUESTED
