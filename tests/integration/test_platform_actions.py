"""Platform entities, writing and switch/binary-sensor states.

Writing: what an entity sends to the coordinator when a user changes it, and that a failing write never
raises into Home Assistant. Reading: how switches and binary sensors turn raw values into on/off.
"""
from unittest.mock import AsyncMock

import pytest

from custom_components.goecharger_api2.binary_sensor import GoeChargerApiV2BinarySensor
from custom_components.goecharger_api2.button import GoeChargerApiV2Button
from custom_components.goecharger_api2.const import (
    ExtBinarySensorEntityDescription as BinaryDesc,
    ExtButtonEntityDescription as ButtonDesc,
    ExtSelectEntityDescription as SelectDesc,
    ExtSwitchEntityDescription as SwitchDesc,
)
from custom_components.goecharger_api2.select import GoeChargerSelect
from custom_components.goecharger_api2.switch import GoeChargerSwitch

from .factories import make_coordinator


def _select(hass, data, **description):
    coordinator = make_coordinator(hass, data=data)
    coordinator.available_cards_idx = []
    coordinator.async_write_key = AsyncMock()
    coordinator.async_write_multiple_keys = AsyncMock()
    return GoeChargerSelect(coordinator, SelectDesc(options=["0", "1"], **description)), coordinator


# ----------------------------------------------------------------------------- select: writing

async def test_select_writes_an_integer(hass):
    select, coordinator = _select(hass, {"lmo": "3"}, key="lmo")
    await select.async_select_option("4")
    coordinator.async_write_key.assert_awaited_once_with("lmo", 4, select)


async def test_select_null_option_writes_none(hass):
    select, coordinator = _select(hass, {"trx": 1}, key="trx")
    await select.async_select_option("null")
    coordinator.async_write_key.assert_awaited_once_with("trx", None, select)


async def test_select_with_idx_writes_the_whole_object(hass):
    select, coordinator = _select(hass, {"x": {"control": "a", "other": 1}}, key="x", idx="control")
    await select.async_select_option("b")
    coordinator.async_write_key.assert_awaited_once_with("x", {"control": "b", "other": 1}, select)


async def test_select_with_idx_and_null_writes_none_into_the_object(hass):
    select, coordinator = _select(hass, {"x": {"control": "a"}}, key="x", idx="control")
    await select.async_select_option("null")
    coordinator.async_write_key.assert_awaited_once_with("x", {"control": None}, select)


async def test_select_with_idx_and_missing_key_writes_nothing(hass):
    select, coordinator = _select(hass, {}, key="x", idx="control")
    assert await select.async_select_option("b") == "unavailable"
    coordinator.async_write_key.assert_not_awaited()


async def test_select_schedule_writes_an_integer_and_removes_the_seconds(hass):
    obj = {"control": 0, "ranges": [{"begin": {"hour": 1, "second": 0}, "end": {"hour": 2, "second": 0}},
                                    {"begin": {"hour": 3}, "end": {"hour": 4}}]}
    select, coordinator = _select(hass, {"sch_week": obj}, key="sch_week", idx="control")
    await select.async_select_option("2")
    written = coordinator.async_write_key.await_args.args[1]
    assert written["control"] == 2
    assert all("second" not in r["begin"] and "second" not in r["end"] for r in written["ranges"])


@pytest.mark.parametrize("option, expected", [
    ("default", {"ct": "default", "mca": 6, "acp": True, "su": False, "psm": 0, "mcpd": 0}),
    ("renaultzoe", {"ct": "renaultZoe", "mca": 10, "acp": True, "su": True, "psm": 0, "mcpd": 0}),
    ("vwid3_2", {"ct": "vwID3_2", "mca": 6, "acp": False, "su": False, "psm": 0, "mcpd": 0}),
    ("daciaspring", {"ct": "daciaSpring", "mca": 6, "acp": True, "su": False, "psm": 1, "mcpd": 0}),
    ("ssangyong", {"ct": "ssangyong", "mca": 6, "acp": True, "su": False, "psm": 0, "mcpd": 0}),
    ("fordexplorer", {"ct": "fordExplorer", "mca": 6, "acp": True, "su": True, "psm": 0, "mcpd": 120000}),
    ("cuprabornalternative", {"ct": "cupraBornAlternative", "mca": 6, "acp": True, "su": True, "psm": 0, "mcpd": 120000}),
    ("kiasoul", {"ct": "kiaSoul", "mca": 6, "acp": True, "su": True, "psm": 0, "mcpd": 0}),
])
async def test_select_car_type_writes_the_whole_profile(hass, option, expected):
    select, coordinator = _select(hass, {"ct": "default"}, key="ct")
    await select.async_select_option(option)
    coordinator.async_write_multiple_keys.assert_awaited_once()
    attr = coordinator.async_write_multiple_keys.await_args.kwargs["attr"]
    assert attr == expected


async def test_select_swallows_write_errors(hass):
    select, coordinator = _select(hass, {"lmo": "3"}, key="lmo")
    coordinator.async_write_key.side_effect = ValueError("down")
    assert await select.async_select_option("4") == "unavailable"


# ----------------------------------------------------------------------------- switch

def _switch(hass, data, **description):
    coordinator = make_coordinator(hass, data=data)
    coordinator.async_write_key = AsyncMock()
    return GoeChargerSwitch(coordinator, SwitchDesc(**description)), coordinator


@pytest.mark.parametrize("description, turn_on, expected", [
    (dict(key="bac"), True, True),
    (dict(key="bac"), False, False),
    (dict(key="bac", is_zero_or_one=True), True, 1),
    (dict(key="bac", is_zero_or_one=True), False, 0),
])
async def test_switch_writes_boolean_or_number(hass, description, turn_on, expected):
    switch, coordinator = _switch(hass, {"bac": 1}, **description)
    await (switch.async_turn_on() if turn_on else switch.async_turn_off())
    coordinator.async_write_key.assert_awaited_once_with("bac", expected, switch)
    assert type(coordinator.async_write_key.await_args.args[1]) is type(expected)


@pytest.mark.parametrize("turn_on, flag, expected", [
    (True, None, True), (False, None, False), (True, True, 1), (False, True, 0)])
async def test_switch_with_idx_writes_the_whole_object(hass, turn_on, flag, expected):
    switch, coordinator = _switch(hass, {"x": {"a": 5, "b": None}}, key="x", idx="b", is_zero_or_one=flag)
    await (switch.async_turn_on() if turn_on else switch.async_turn_off())
    coordinator.async_write_key.assert_awaited_once_with("x", {"a": 5, "b": expected}, switch)


@pytest.mark.parametrize("turn_on", [True, False])
async def test_switch_with_idx_and_missing_key_writes_nothing(hass, turn_on):
    switch, coordinator = _switch(hass, {}, key="x", idx="b")
    assert await (switch.async_turn_on() if turn_on else switch.async_turn_off()) == "unavailable"
    coordinator.async_write_key.assert_not_awaited()


@pytest.mark.parametrize("turn_on", [True, False])
async def test_switch_swallows_write_errors(hass, turn_on):
    switch, coordinator = _switch(hass, {"bac": 1}, key="bac")
    coordinator.async_write_key.side_effect = ValueError("down")
    assert await (switch.async_turn_on() if turn_on else switch.async_turn_off()) == "unavailable"


STATE_CASES = [
    ("bool true", {"x": True}, dict(key="x"), True),
    ("bool false", {"x": False}, dict(key="x"), False),
    ("positive integer", {"x": 3}, dict(key="x"), True),
    ("zero", {"x": 0}, dict(key="x"), False),
    ("text on", {"x": "ON"}, dict(key="x"), True),
    ("text other", {"x": "off"}, dict(key="x"), False),
    ("null", {"x": None}, dict(key="x"), False),
    ("empty text", {"x": ""}, dict(key="x"), False),
    ("missing key", {"y": 1}, dict(key="x"), False),
    ("idx", {"x": [0, 1]}, dict(key="x", idx=1), True),
    ("wrong idx", {"x": {}}, dict(key="x", idx=1), False),
    ("list value", {"x": [1]}, dict(key="x"), False),
]


@pytest.mark.parametrize("data, description, expected", [c[1:] for c in STATE_CASES], ids=[c[0] for c in STATE_CASES])
async def test_switch_is_on(hass, data, description, expected):
    switch, _ = _switch(hass, data, **description)
    assert switch.is_on is expected


async def test_switch_without_data_and_with_idx_on_null_have_no_state(hass):
    switch, coordinator = _switch(hass, {"x": None}, key="x", idx=0)
    assert switch.is_on is None and switch.state is None


async def test_switch_state_and_icon(hass):
    switch, _ = _switch(hass, {"x": False}, key="x", icon="mdi:on", icon_off="mdi:off")
    assert switch.state == "off" and switch.icon == "mdi:off"
    switch.coordinator.data["x"] = True
    assert switch.state == "on" and switch.icon == "mdi:on"


# ----------------------------------------------------------------------------- binary sensor

def _binary(hass, data, **description):
    return GoeChargerApiV2BinarySensor(make_coordinator(hass, data=data), BinaryDesc(**description))


BINARY_CASES = [
    ("bool", {"x": True}, dict(key="x"), True),
    ("text on", {"x": "on"}, dict(key="x"), True),
    ("text other", {"x": "no"}, dict(key="x"), False),
    ("integer is not on", {"x": 5}, dict(key="x"), False),
    ("null", {"x": None}, dict(key="x"), False),
    ("empty", {"x": ""}, dict(key="x"), False),
    ("missing key", {"y": 1}, dict(key="x"), False),
    ("idx", {"x": [False, True]}, dict(key="x", idx=1), True),
    ("car connected above idle", {"car": 2}, dict(key="car", idx=0), True),
    ("car idle is not connected", {"car": 1}, dict(key="car", idx=0), False),
    ("tuple idx", {"x": {"a": {"b": True}}}, dict(key="x", tuple_idx=["a", "b"]), True),
    ("idx out of range", {"x": [True]}, dict(key="x", idx=4), False),
    ("tuple idx out of range", {"x": [[True]]}, dict(key="x", tuple_idx=[0, 3]), False),
    ("wrong key in tuple idx", {"x": {"a": {}}}, dict(key="x", tuple_idx=["a", "b"]), False),
    ("single tuple idx is ignored", {"x": 1}, dict(key="x", tuple_idx=["a"]), False),
]


@pytest.mark.parametrize("data, description, expected", [c[1:] for c in BINARY_CASES], ids=[c[0] for c in BINARY_CASES])
async def test_binary_sensor_is_on(hass, data, description, expected):
    assert _binary(hass, data, **description).is_on is expected


async def test_binary_sensor_with_wrong_type_has_no_state(hass):
    assert _binary(hass, {"x": None}, key="x", idx=0).is_on is None


async def test_binary_sensor_icon_follows_the_state(hass):
    sensor = _binary(hass, {"x": False}, key="x", icon="mdi:on", icon_off="mdi:off")
    assert sensor.icon == "mdi:off"
    sensor.coordinator.data["x"] = True
    assert sensor.icon == "mdi:on"


# ----------------------------------------------------------------------------- button

async def test_button_press_sends_its_payload(hass):
    coordinator = make_coordinator(hass, data={})
    coordinator.async_write_key = AsyncMock()
    button = GoeChargerApiV2Button(coordinator, ButtonDesc(key="zfocore", payload="TRIGGER"))
    await button.async_press()
    coordinator.async_write_key.assert_awaited_once_with("zfocore", "TRIGGER", button)


async def test_button_press_swallows_write_errors(hass):
    coordinator = make_coordinator(hass, data={})
    coordinator.async_write_key = AsyncMock(side_effect=ValueError("down"))
    button = GoeChargerApiV2Button(coordinator, ButtonDesc(key="zfocore", payload="TRIGGER"))
    assert await button.async_press() == "unavailable"
