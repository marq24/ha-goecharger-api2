"""Platform entities, reading: how raw charger values become sensor, number, select, switch and binary sensor states.

Each case builds an entity description by hand (so exactly one feature is exercised), puts a raw value
into the coordinator data and checks the state. Failure cases (missing key, wrong type, wrong index)
must give an empty state and no exception.
"""
from datetime import datetime, time

import pytest
from homeassistant.components.sensor import SensorDeviceClass

from custom_components.goecharger_api2.binary_sensor import GoeChargerApiV2BinarySensor
from custom_components.goecharger_api2.const import (
    ExtBinarySensorEntityDescription as BinaryDesc,
    ExtNumberEntityDescription as NumberDesc,
    ExtSelectEntityDescription as SelectDesc,
    ExtSensorEntityDescription as SensorDesc,
    ExtSwitchEntityDescription as SwitchDesc,
)
from custom_components.goecharger_api2.number import GoeChargerNumber
from custom_components.goecharger_api2.select import GoeChargerSelect
from custom_components.goecharger_api2.sensor import GoeChargerSensor
from custom_components.goecharger_api2.switch import GoeChargerSwitch

from .factories import make_coordinator


def _sensor(hass, data, cards_as_object=True, **description):
    coordinator = make_coordinator(hass, data=data)
    coordinator._cards_as_object_present = cards_as_object
    return GoeChargerSensor(coordinator, SensorDesc(**description)), coordinator


# ----------------------------------------------------------------------------- sensor

SENSOR_CASES = [
    ("plain", {"amp": 16}, dict(key="amp"), 16),
    ("empty string", {"amp": ""}, dict(key="amp"), None),
    ("null", {"amp": None}, dict(key="amp"), None),
    ("missing key", {}, dict(key="amp"), None),
    ("idx", {"nrg": [230, 231, 232]}, dict(key="nrg", idx=1), 231),
    ("idx out of range", {"nrg": [230]}, dict(key="nrg", idx=5), None),
    ("idx on null", {"nrg": None}, dict(key="nrg", idx=0), None),
    ("tuple idx", {"x": {"a": {"b": 3}}}, dict(key="x", tuple_idx=["a", "b"]), 3),
    ("tuple idx missing", {"x": {"a": {}}}, dict(key="x", tuple_idx=["a", "b"]), None),
    ("cards as object", {"cards": [{"name": "A", "energy": 5}]}, dict(key="cards", tuple_idx=[0, "energy"]), 5),
    ("factor", {"x": 1000}, dict(key="x", factor=10), 100),
    ("factor zero ignored", {"x": 1000}, dict(key="x", factor=0), 1000),
    ("differential base", {"x": 100, "rbt": 150}, dict(key="x", differential_base_key="rbt"), 50),
    ("differential base zero", {"x": 100, "rbt": 0}, dict(key="x", differential_base_key="rbt"), 100),
    ("differential and factor", {"x": 100, "rbt": 1150}, dict(key="x", differential_base_key="rbt", factor=10), 105),
    ("differential base missing", {"x": 100}, dict(key="x", differential_base_key="rbt"), None),
    ("datetime", {"x": datetime(2026, 10, 29, 8, 30, 45)}, dict(key="x"), "2026-10-29 08:30"),
    ("time", {"x": time(7, 5, 9)}, dict(key="x"), "07:05"),
    ("bool true", {"x": True}, dict(key="x"), "on"),
    ("bool false", {"x": False}, dict(key="x"), "off"),
    ("string unchanged", {"x": "text"}, dict(key="x"), "text"),
]


@pytest.mark.parametrize("data, description, expected", [c[1:] for c in SENSOR_CASES], ids=[c[0] for c in SENSOR_CASES])
async def test_sensor_native_value(hass, data, description, expected):
    sensor, _ = _sensor(hass, data, **description)
    assert sensor.native_value == expected


async def test_sensor_without_data_has_no_value(hass):
    sensor, coordinator = _sensor(hass, {}, key="amp")
    coordinator.data = None
    assert sensor.native_value is None


@pytest.mark.parametrize("sub_key, key, expected", [
    ("energy", "c1e", 77), ("name", "c1n", "Anna"), ("cardId", "c1i", "A1B2")])
async def test_sensor_card_values_of_firmware_60_use_single_keys(hass, sub_key, key, expected):
    data = {"c1e": 77, "c1n": "Anna", "c1i": "A1B2"}
    sensor, _ = _sensor(hass, data, cards_as_object=False, key="cards", tuple_idx=[1, sub_key])
    assert sensor.native_value == expected


async def test_sensor_unknown_card_sub_key_gives_no_value(hass):
    sensor, _ = _sensor(hass, {"c1e": 77}, cards_as_object=False, key="cards", tuple_idx=[1, "colour"])
    assert sensor.native_value is None


async def test_sensor_card_key_missing_gives_no_value(hass):
    sensor, _ = _sensor(hass, {}, cards_as_object=False, key="cards", tuple_idx=[1, "energy"])
    assert sensor.native_value is None


async def test_sensor_lookup_translates_the_value(hass):
    sensor, coordinator = _sensor(hass, {"car": 2}, key="car", lookup=True)
    assert sensor.native_value == coordinator.lang_map["car"][2]


async def test_sensor_lookup_without_translation_keeps_the_raw_value(hass, caplog):
    sensor, _ = _sensor(hass, {"zzz": 5}, key="zzz", lookup=True)
    assert sensor.native_value == 5
    assert "not found in translations" in caplog.text


async def test_sensor_lookup_with_unknown_code_gives_no_value(hass):
    sensor, _ = _sensor(hass, {"car": 99}, key="car", lookup=True)
    assert sensor.native_value is None


async def test_sensor_cll_object_becomes_readable_text(hass):
    data = {"cll": {"cableCurrentLimit": 32, "unknownLimit": 1}}
    sensor, coordinator = _sensor(hass, data, key="cll")
    value = sensor.native_value
    first = coordinator.lang_map.get("cll_cablecurrentlimit", "cable_current_limit")
    assert value.startswith(f"{first}: 32") and value.endswith("unknown_limit: 1")


async def test_sensor_camel_case_is_converted_to_snake_case():
    assert GoeChargerSensor._camel_to_snake("cableCurrentLimit") == "cable_current_limit"
    assert GoeChargerSensor._camel_to_snake("Max-Value 2") == "max_value_2"


async def test_sensor_date_state_is_unknown_without_value(hass):
    sensor, _ = _sensor(hass, {"x": None}, key="x", device_class=SensorDeviceClass.DATE)
    assert sensor.state == "unknown"


async def test_sensor_date_state_passes_the_value_through(hass):
    sensor, _ = _sensor(hass, {"x": "2026-10-29"}, key="x", device_class=SensorDeviceClass.DATE)
    assert sensor.state == "2026-10-29"


# ----------------------------------------------------------------------------- number

def _number(hass, data, **description):
    coordinator = make_coordinator(hass, data=data)
    return GoeChargerNumber(coordinator, NumberDesc(**description)), coordinator


NUMBER_CASES = [
    ("plain", {"amp": 16}, dict(key="amp"), 16),
    ("null is unknown", {"amp": None}, dict(key="amp"), "unknown"),
    ("empty is unknown", {"amp": ""}, dict(key="amp"), "unknown"),
    ("missing key is unknown", {}, dict(key="amp"), "unknown"),
    ("idx", {"lop": [1, 2, 3]}, dict(key="lop", idx=2), 3),
    ("idx on null gives none", {"lop": None}, dict(key="lop", idx=0), None),
    ("float", {"x": 5}, dict(key="x", handle_as_float=True), 5.0),
    ("float with factor", {"x": 150}, dict(key="x", handle_as_float=True, factor=100), 1.5),
    ("integer with factor", {"x": 150}, dict(key="x", factor=10), 15),
]


@pytest.mark.parametrize("data, description, expected", [c[1:] for c in NUMBER_CASES], ids=[c[0] for c in NUMBER_CASES])
async def test_number_native_value(hass, data, description, expected):
    number, _ = _number(hass, data, **description)
    assert number.native_value == expected


WRITE_CASES = [
    ("integer", {"amp": 6}, dict(key="amp"), 10, ("amp", 10)),
    ("float value is cut to integer", {"amp": 6}, dict(key="amp"), 10.9, ("amp", 10)),
    ("zero as null", {"x": 5}, dict(key="x", write_zero_as_null=True), 0, ("x", None)),
    ("zero stays zero", {"x": 5}, dict(key="x"), 0, ("x", 0)),
    ("factor", {"x": 5}, dict(key="x", factor=100), 1.5, ("x", 150)),
    ("float", {"x": 5}, dict(key="x", handle_as_float=True), 2, ("x", 2.0)),
]


@pytest.mark.parametrize("data, description, value, expected", [c[1:] for c in WRITE_CASES], ids=[c[0] for c in WRITE_CASES])
async def test_number_set_value_writes_the_converted_value(hass, data, description, value, expected):
    from unittest.mock import AsyncMock
    number, coordinator = _number(hass, data, **description)
    coordinator.async_write_key = AsyncMock()
    await number.async_set_native_value(value)
    coordinator.async_write_key.assert_awaited_once_with(expected[0], expected[1], number, require_ack=False)


IDX_WRITE_CASES = [
    ("integer", dict(idx=1), 9, [1, 9, 3]),
    ("zero as null", dict(idx=1, write_zero_as_null=True), 0, [1, None, 3]),
    ("factor", dict(idx=1, factor=10), 2, [1, 20, 3]),
    ("float", dict(idx=1, handle_as_float=True), 4, [1, 4.0, 3]),
]


@pytest.mark.parametrize("description, value, expected", [c[1:] for c in IDX_WRITE_CASES], ids=[c[0] for c in IDX_WRITE_CASES])
async def test_number_set_value_writes_the_whole_list(hass, description, value, expected):
    from unittest.mock import AsyncMock
    number, coordinator = _number(hass, {"lop": [1, 2, 3]}, key="lop", **description)
    coordinator.async_write_key = AsyncMock()
    await number.async_set_native_value(value)
    coordinator.async_write_key.assert_awaited_once_with("lop", expected, number, require_ack=False)


async def test_number_set_value_swallows_write_errors(hass):
    from unittest.mock import AsyncMock
    number, coordinator = _number(hass, {"amp": 6}, key="amp")
    coordinator.async_write_key = AsyncMock(side_effect=ValueError("down"))
    assert await number.async_set_native_value(10) == "unavailable"


# ----------------------------------------------------------------------------- number: limits of amp

def _amp(value):
    from types import SimpleNamespace
    return SimpleNamespace(_attr_native_max_value=32, _attr_native_min_value=6, native_value=value,
                           entity_id="number.goe_123456_amp")


LIMIT_CASES = [
    ("max below amp lowers amp", "ama", 10, 20, 10),
    ("max above amp changes nothing", "ama", 32, 20, None),
    ("min above amp raises amp", "mca", 25, 20, 25),
    ("min below amp changes nothing", "mca", 6, 20, None),
    ("max equal to stored max changes nothing", "ama", 32, 40, None),
]


@pytest.mark.parametrize("key, value, amp_value, expected", [c[1:] for c in LIMIT_CASES], ids=[c[0] for c in LIMIT_CASES])
async def test_number_amp_limits_adjust_amp_entity(hass, key, value, amp_value, expected):
    from pytest_homeassistant_custom_component.common import async_mock_service
    calls = async_mock_service(hass, "number", "set_value")
    number, coordinator = _number(hass, {key: value}, key=key)
    number.hass = hass
    coordinator.entities["amp"] = _amp(amp_value)
    number.check_amp_min_max(value)
    await hass.async_block_till_done()
    assert [c.data["value"] for c in calls] == ([] if expected is None else [expected])


async def test_number_without_amp_entity_ignores_limits(hass):
    number, _ = _number(hass, {"ama": 10}, key="ama")
    number.check_amp_min_max(10)  # no amp entity registered: must not raise


# ----------------------------------------------------------------------------- select

def _select(hass, data, **description):
    coordinator = make_coordinator(hass, data=data)
    coordinator.available_cards_idx = ["1", "2"]
    return GoeChargerSelect(coordinator, SelectDesc(options=["0", "1", "2"], **description)), coordinator


SELECT_CASES = [
    ("string", {"lmo": "3"}, dict(key="lmo"), "3"),
    ("integer becomes text", {"lmo": 3}, dict(key="lmo"), "3"),
    ("idx", {"x": ["a", "b"]}, dict(key="x", idx=1), "b"),
    ("idx with missing key", {}, dict(key="x", idx=0), "unavailable"),
    ("missing key is unknown", {}, dict(key="lmo"), "unknown"),
    ("empty is unknown", {"lmo": ""}, dict(key="lmo"), "unknown"),
    ("transaction without card is null", {"trx": None}, dict(key="trx"), "null"),
    ("car type without value is default", {"ct": None}, dict(key="ct"), "default"),
    ("car type is lower case", {"ct": "VWID5"}, dict(key="ct"), "vwid5"),
    ("wrong index is unknown", {"x": {}}, dict(key="x", idx=1), "unknown"),
    ("index on null gives none", {"x": None}, dict(key="x", idx=0), None),
]


@pytest.mark.parametrize("data, description, expected", [c[1:] for c in SELECT_CASES], ids=[c[0] for c in SELECT_CASES])
async def test_select_current_option(hass, data, description, expected):
    select, _ = _select(hass, data, **description)
    assert select.current_option == expected


async def test_select_transaction_offers_the_active_cards(hass):
    select, _ = _select(hass, {}, key="trx")
    assert select.options == ["null", "0", "1", "2"]
