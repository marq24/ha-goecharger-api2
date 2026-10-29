"""Entity IDs must not change by accident.

Users have dashboards, automations, statistics and renamed entities that reference these IDs.
The expected IDs are stored in `snapshots/entity_ids.json`. If an ID changes on purpose, regenerate
the file with `UPDATE_SNAPSHOT=1 python -m pytest tests/integration/test_entity_ids.py` and review the diff.
"""
import json
import os
from pathlib import Path

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.goecharger_api2 import GoeChargerBaseEntity, GoeChargerDataUpdateCoordinator
from custom_components.goecharger_api2 import const

SNAPSHOT = Path(__file__).parent / "snapshots" / "entity_ids.json"

CHARGER_LISTS = {
    "binary_sensor": const.BINARY_SENSORS, "button": const.BUTTONS, "number": const.NUMBER_SENSORS,
    "select": const.SELECT_SENSORS, "sensor": const.SENSOR_SENSORS, "switch": const.SWITCH_SENSORS,
}
CONTROLLER_LISTS = {
    "binary_sensor": const.CONTROLLER_BINARY_SENSORS, "button": const.CONTROLLER_BUTTONS,
    "number": const.CONTROLLER_NUMBER_SENSORS, "select": const.CONTROLLER_SELECT_SENSORS,
    "sensor": const.CONTROLLER_SENSOR_SENSORS, "switch": const.CONTROLLER_SWITCH_SENSORS,
}

VARIANTS = {
    "charger_lan": ({"mode": "lan", "host": "192.0.2.10"}, "charger", CHARGER_LISTS),
    "charger_wan": ({"mode": "wan", "token": "t"}, "charger", CHARGER_LISTS),
    "controller_lan": ({"mode": "lan", "host": "192.0.2.10"}, "controller", CONTROLLER_LISTS),
}


def _entities(hass, variant):
    data, intg_type, lists = VARIANTS[variant]
    entry = MockConfigEntry(domain="goecharger_api2", title="t",
                            data={**data, "id": "123456", "integration_type": intg_type})
    entry.add_to_hass(hass)
    coordinator = GoeChargerDataUpdateCoordinator(hass, entry)
    return [GoeChargerBaseEntity(platform, coordinator, description)
            for platform, descriptions in lists.items() for description in descriptions]


@pytest.mark.parametrize("variant", VARIANTS)
async def test_entity_ids_match_snapshot(hass, variant):
    actual = sorted(entity.entity_id for entity in _entities(hass, variant))
    if os.environ.get("UPDATE_SNAPSHOT"):
        stored = json.loads(SNAPSHOT.read_text()) if SNAPSHOT.exists() else {}
        stored[variant] = actual
        SNAPSHOT.parent.mkdir(exist_ok=True)
        SNAPSHOT.write_text(json.dumps(dict(sorted(stored.items())), indent=1) + "\n")
        pytest.skip("snapshot updated")
    expected = json.loads(SNAPSHOT.read_text())[variant]
    assert {"added": sorted(set(actual) - set(expected)), "removed": sorted(set(expected) - set(actual))} == \
        {"added": [], "removed": []}


@pytest.mark.parametrize("variant", VARIANTS)
async def test_entity_ids_are_unique(hass, variant):
    ids = [entity.entity_id for entity in _entities(hass, variant)]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    assert duplicates == []


@pytest.mark.parametrize("variant", VARIANTS)
async def test_unique_id_is_derived_from_the_entity_id(hass, variant):
    for entity in _entities(hass, variant):
        assert entity.unique_id == f"goecharger_api2.{entity.entity_id.split('.')[1]}"


async def test_wan_entities_are_prefixed_differently_from_lan(hass):
    lan = {e.entity_id for e in _entities(hass, "charger_lan")}
    wan = {e.entity_id for e in _entities(hass, "charger_wan")}
    assert lan.isdisjoint(wan)
    assert all(".goe_wan_123456_" in i for i in wan) and all(".goe_123456_" in i for i in lan)
