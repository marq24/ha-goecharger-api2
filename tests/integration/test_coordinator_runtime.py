"""Coordinator at runtime: write results, the 16 A limiter, device detection, WebSocket start, reconnect and housekeeping.

The coordinator and the bridge are the real code. Timers (`async_call_later`, `async_track_time_interval`)
and sleeps are replaced so that no test waits or leaves a timer behind.
"""
import asyncio
import logging
import time
from collections import ChainMap
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components.number import NumberDeviceClass
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr

from custom_components.goecharger_api2.const import DOMAIN
from custom_components.goecharger_api2.pygoecharger_ha import NonNullDict
from custom_components.goecharger_api2.pygoecharger_ha.keys import Tag

from .factories import make_coordinator

PKG = "custom_components.goecharger_api2"


# ----------------------------------------------------------------------------- handle_write_result

async def test_websocket_write_result_is_left_to_the_websocket_processor(hass):
    coordinator = make_coordinator(hass, data={"amp": 6}, websocket=True)
    coordinator.handle_write_result("single", 10, "amp", None, None)
    assert coordinator.data == {"amp": 6}


async def test_http_write_result_updates_the_data_and_refreshes_the_entity(hass):
    coordinator = make_coordinator(hass, data={"amp": 6})
    entity = MagicMock()
    coordinator.handle_write_result("single", 10, "amp", {"amp": 10}, entity)
    assert coordinator.data["amp"] == 10
    entity.async_schedule_update_ha_state.assert_called_once_with(force_refresh=True)


async def test_write_result_without_the_key_is_logged_as_error(hass, caplog):
    coordinator = make_coordinator(hass, data={"amp": 6})
    with caplog.at_level(logging.ERROR):
        coordinator.handle_write_result("single", 10, "amp", {"err": {"amp": "denied"}}, None)
    assert coordinator.data["amp"] == 6 and "could not write" in caplog.text


async def test_pv_data_result_rebuilds_the_data_and_notifies_listeners_without_refresh(hass):
    coordinator = make_coordinator(hass, data={})
    coordinator.async_update_listeners = MagicMock()
    entity = MagicMock()
    coordinator.handle_write_result("single", {}, Tag.IDS.key, {Tag.IDS.key: {}}, entity)
    assert isinstance(coordinator.data, ChainMap)
    coordinator.async_update_listeners.assert_called_once()
    entity.async_schedule_update_ha_state.assert_not_called()


async def test_refresh_button_result_schedules_a_delayed_update(hass):
    coordinator = make_coordinator(hass, data={})
    coordinator.request_update_in_sec = MagicMock()
    entity = MagicMock()
    key = Tag.INTERNAL_FORCE_REFRESH_ALL.key
    coordinator.handle_write_result("single", "TRIGGER", key, {key: "TRIGGER"}, entity)
    coordinator.request_update_in_sec.assert_called_once_with(2.5)
    entity.async_schedule_update_ha_state.assert_not_called()


async def test_write_result_without_entity_does_not_fail(hass):
    coordinator = make_coordinator(hass, data={})
    coordinator.handle_write_result("single", 1, "amp", {"amp": 1}, None)
    assert coordinator.data["amp"] == 1


async def test_controller_treats_pv_key_like_any_other(hass):
    coordinator = make_coordinator(hass, data={}, intg_type="controller")
    coordinator.async_update_listeners = MagicMock()
    entity = MagicMock()
    coordinator.handle_write_result("single", 1, Tag.IDS.key, {Tag.IDS.key: 1}, entity)
    coordinator.async_update_listeners.assert_not_called()
    entity.async_schedule_update_ha_state.assert_called_once()


# ----------------------------------------------------------------------------- 16 A limiter

def _current_entity(key, max_value=16, **kwargs):
    values = dict(original_device_class=NumberDeviceClass.CURRENT, capabilities={"max": max_value},
                  disabled=False, orphaned_timestamp=None, translation_key=key)
    values.update(kwargs)
    return SimpleNamespace(**values)


# ----------------------------------------------------------------------------- device detection (read_versions)

def _versions_coordinator(hass, versions, **kwargs):
    coordinator = make_coordinator(hass, data={}, **kwargs)
    coordinator.bridge.read_versions = AsyncMock(return_value=True)
    coordinator.bridge._versions = NonNullDict(versions)
    return coordinator


async def test_read_versions_fails_when_the_bridge_has_no_versions(hass):
    coordinator = make_coordinator(hass, data={})
    coordinator.bridge.read_versions = AsyncMock(return_value=False)
    assert await coordinator.read_versions() is False


async def test_read_versions_fails_for_a_plain_dictionary(hass):
    coordinator = make_coordinator(hass, data={})
    coordinator.bridge.read_versions = AsyncMock(return_value=True)
    coordinator.bridge._versions = {"typ": "x"}
    assert await coordinator.read_versions() is False


async def test_cards_object_lists_only_activated_cards(hass):
    coordinator = _versions_coordinator(hass, {"typ": "go-eCharger_V4", "cards": [{"cardId": 1}, {"cardId": 0}, {"cardId": 7}]})
    await coordinator.read_versions()
    assert coordinator._cards_as_object_present is True and coordinator.available_cards_idx == ["1", "3"]


async def test_single_card_keys_are_used_without_a_cards_object(hass):
    coordinator = _versions_coordinator(hass, {"typ": "go-eCharger_V4", "c0i": "A", "c2i": "B"})
    await coordinator.read_versions()
    assert coordinator._cards_as_object_present is False and coordinator.available_cards_idx == ["1", "3"]


async def test_no_cards_at_all_gives_an_empty_list(hass):
    coordinator = _versions_coordinator(hass, {"typ": "go-eCharger_V4"})
    await coordinator.read_versions()
    assert coordinator.available_cards_idx == []


@pytest.mark.parametrize("typ, expected", [
    ("go-eCharger_Phoenix", True), ("go-eCharger_Core", True), ("go-eCharger Gemini Pro", True),
    ("go-eCharger_V4", False)])
async def test_core_wallbox_is_recognised_by_its_type(hass, typ, expected):
    coordinator = _versions_coordinator(hass, {"typ": typ})
    await coordinator.read_versions()
    assert coordinator._is_core_wallbox is expected


async def test_type_falls_back_to_the_type_stored_at_setup(hass):
    coordinator = _versions_coordinator(hass, {}, type="go-eCharger_Phoenix [11 kW] Local")
    await coordinator.read_versions()
    assert coordinator._is_core_wallbox is True


async def test_unreadable_cable_limit_on_a_core_wallbox_limits_to_16_a(hass):
    coordinator = _versions_coordinator(hass, {"typ": "go-eCharger_Phoenix", "cll": {"cableCurrentLimit": "n/a"}})
    await coordinator.read_versions()
    assert coordinator.limit_to16a is False


async def test_unreadable_cable_limit_on_another_wallbox_uses_the_adapter_flag(hass):
    coordinator = _versions_coordinator(hass, {"typ": "go-eCharger_V4", "cll": {"cableCurrentLimit": "n/a"}, "adi": True})
    await coordinator.read_versions()
    assert coordinator.limit_to16a is False


async def test_empty_cll_object_falls_back_to_the_adapter_flag(hass):
    coordinator = _versions_coordinator(hass, {"typ": "go-eCharger_V4", "cll": {}, "adi": False})
    await coordinator.read_versions()
    assert coordinator.limit_to16a is False


async def test_load_balancer_group_is_detected(hass):
    coordinator = _versions_coordinator(hass, {"typ": "go-eCharger_V4", "log": "group-1"})
    await coordinator.read_versions()
    assert coordinator.is_loadbalancer_group_id_set is True


async def test_blank_load_balancer_group_is_not_a_group(hass):
    coordinator = _versions_coordinator(hass, {"typ": "go-eCharger_V4", "log": "  "})
    await coordinator.read_versions()
    assert coordinator.is_loadbalancer_group_id_set is False


async def test_device_info_uses_type_mode_serial_and_cleaned_firmware(hass):
    coordinator = _versions_coordinator(hass, {"typ": "go-eCharger_V4", "fwv": "60.3-beta", "var": 11}, type="V4 [11 kW] Local")
    await coordinator.read_versions()
    info = coordinator._device_info_dict
    assert info["identifiers"] == {(DOMAIN, "charger", "lan", "123456")}
    assert info["sw_version"] == "60.3" and "[16A limited]" in info["model"] and "HTTP v2 API" in info["model"]


async def test_device_info_without_firmware_and_with_websocket_label(hass):
    coordinator = _versions_coordinator(hass, {"typ": "go-eCharger_V4", "adi": False}, password="secret")
    await coordinator.read_versions()
    info = coordinator._device_info_dict
    assert info["sw_version"] == "UNKNOWN" and info["model"].endswith("WebSocket")


async def test_controller_has_no_charger_features(hass):
    coordinator = _versions_coordinator(hass, {"typ": "go-eController", "fwv": "1.1.1"}, intg_type="controller")
    await coordinator.read_versions()
    assert coordinator.limit_to16a is False
    assert coordinator._device_info_dict["identifiers"] == {(DOMAIN, "controller", "lan", "123456")}


# ----------------------------------------------------------------------------- which entities exist

@pytest.mark.parametrize("core, key, idx, expected", [
    (True, "tma", 0, False), (True, "tma", 1, False), (True, "tma", 2, True), (True, "tma", 5, True),
    (False, "tma", 0, True), (False, "tma", 1, True), (False, "tma", 2, False),
    (True, "cus", None, False), (True, "bac", None, False), (False, "cus", None, True),
    (False, "iso2ena", None, False), (True, "iso2ena", None, True), (True, "amp", None, True),
])
async def test_entity_filter_depends_on_the_wallbox_generation(hass, core, key, idx, expected):
    coordinator = make_coordinator(hass, data={})
    coordinator._is_core_wallbox = core
    description = SimpleNamespace(key=key) if idx is None else SimpleNamespace(key=key, idx=idx)
    assert coordinator.is_valid_charger_entity(description) is expected


async def test_temperature_entity_without_index_is_always_valid(hass):
    coordinator = make_coordinator(hass, data={})
    coordinator._is_core_wallbox = True
    assert coordinator.is_valid_charger_entity(SimpleNamespace(key="tma")) is True


# ----------------------------------------------------------------------------- WebSocket start

def _fake_connect(coordinator, *, set_event=True, error=None):
    async def connect(a_event=None, keep_ws_states_after_close=False):
        if error is not None:
            a_event.set_error(error)
        elif set_event:
            a_event.set()
    coordinator.bridge.ws_connect = connect


async def test_websocket_start_succeeds_when_the_first_data_arrives(hass):
    coordinator = make_coordinator(hass, password="secret")
    _fake_connect(coordinator)
    with patch(f"{PKG}.async_call_later", MagicMock()) as later:
        assert await coordinator.start_websocket_and_wait_for_first_data() is True
    later.assert_called_once()


async def test_websocket_start_reports_errors_from_the_connection(hass):
    coordinator = make_coordinator(hass, password="secret")
    _fake_connect(coordinator, error=Exception("Authentication failed"))
    with patch(f"{PKG}.async_call_later", MagicMock()):
        assert await coordinator.start_websocket_and_wait_for_first_data() is False


async def test_websocket_start_times_out_without_data(hass):
    coordinator = make_coordinator(hass, password="secret")
    _fake_connect(coordinator, set_event=False)
    real_timeout = asyncio.timeout
    with patch(f"{PKG}.asyncio.timeout", lambda _: real_timeout(0.01)):
        with pytest.raises(ConfigEntryNotReady):
            await coordinator.start_websocket_and_wait_for_first_data()


@pytest.mark.parametrize("versions, expected", [
    (AsyncMock(return_value=True), True),
    (AsyncMock(return_value=False), False),
    (AsyncMock(side_effect=RuntimeError("boom")), False),
])
async def test_websocket_start_at_setup_also_needs_the_versions(hass, versions, expected):
    coordinator = make_coordinator(hass, password="secret")
    _fake_connect(coordinator)
    coordinator.read_versions = versions
    with patch(f"{PKG}.async_call_later", MagicMock()):
        assert await coordinator.start_websocket_and_wait_for_first_data(is_integration_init=True) is expected


# ----------------------------------------------------------------------------- forced reconnect

async def test_forced_reconnect_is_ignored_shortly_after_integration_start(hass):
    coordinator = make_coordinator(hass, password="secret")
    coordinator.start_websocket_and_wait_for_first_data = AsyncMock()
    await coordinator.force_async_update_now()
    coordinator.start_websocket_and_wait_for_first_data.assert_not_awaited()


async def test_forced_reconnect_is_ignored_shortly_after_a_fresh_connection(hass):
    coordinator = make_coordinator(hass, password="secret")
    coordinator._integration_start = time.time() - 1000
    coordinator.bridge.ws_connection_start = time.time()
    coordinator.start_websocket_and_wait_for_first_data = AsyncMock()
    await coordinator.force_async_update_now()
    coordinator.start_websocket_and_wait_for_first_data.assert_not_awaited()


@pytest.mark.parametrize("reconnect_ok", [True, False])
async def test_forced_reconnect_restarts_the_websocket(hass, reconnect_ok):
    coordinator = make_coordinator(hass, password="secret")
    coordinator._integration_start = time.time() - 1000
    coordinator.start_websocket_and_wait_for_first_data = AsyncMock(return_value=reconnect_ok)
    with patch(f"{PKG}.asyncio.sleep", AsyncMock()) as sleep:
        await coordinator.force_async_update_now()
    sleep.assert_awaited_once_with(2)
    coordinator.start_websocket_and_wait_for_first_data.assert_awaited_once_with(is_integration_init=False)


# ----------------------------------------------------------------------------- watchdog

async def test_watchdog_starts_a_connection_when_there_is_none(hass):
    coordinator = make_coordinator(hass, password="secret")
    _fake_connect(coordinator)
    with patch(f"{PKG}.async_call_later", MagicMock()) as later:
        await coordinator._async_watchdog_check()
        await asyncio.sleep(0)
    assert coordinator._ws_start_task is not None and later.called


async def test_watchdog_leaves_a_healthy_connection_alone(hass):
    coordinator = make_coordinator(hass, password="secret", websocket=True)
    coordinator.bridge._ws_LAST_UPDATE = time.time()
    coordinator._ws_start_task = None
    await coordinator._async_watchdog_check()
    assert coordinator._ws_start_task is None


async def test_watchdog_cancels_a_connection_without_data(hass):
    coordinator = make_coordinator(hass, password="secret", websocket=True)
    coordinator.bridge._ws_LAST_UPDATE = time.time() - 120
    task = asyncio.create_task(asyncio.sleep(3600))
    coordinator._ws_start_task = task
    with patch(f"{PKG}.async_call_later", MagicMock()):
        await coordinator._async_watchdog_check()
        await asyncio.sleep(0)
    assert task.cancelled() and coordinator._ws_start_task is None


async def test_start_watchdog_checks_once_and_registers_the_timer(hass):
    coordinator = make_coordinator(hass, password="secret", websocket=True)
    coordinator.bridge._ws_LAST_UPDATE = time.time()
    unsubscribe = MagicMock()
    with patch(f"{PKG}.async_track_time_interval", MagicMock(return_value=unsubscribe)) as track, \
         patch(f"{PKG}.async_call_later", MagicMock()):
        await coordinator.start_watchdog()
        coordinator.stop_watchdog()
    track.assert_called_once()
    unsubscribe.assert_called_once()


async def test_stop_watchdog_without_a_timer_does_nothing(hass):
    coordinator = make_coordinator(hass, password="secret")
    coordinator._watchdog = None
    coordinator.stop_watchdog()


async def test_running_connection_task_is_cancelled_and_forgotten(hass):
    coordinator = make_coordinator(hass, password="secret")
    task = asyncio.create_task(asyncio.sleep(3600))
    coordinator._ws_start_task = task
    coordinator._check_for_ws_task_and_cancel_if_running()
    await asyncio.sleep(0)
    assert task.cancelled() and coordinator._ws_start_task is None


async def test_finished_connection_task_is_left_alone(hass):
    coordinator = make_coordinator(hass, password="secret")
    task = asyncio.create_task(asyncio.sleep(0))
    await task
    coordinator._ws_start_task = task
    coordinator._check_for_ws_task_and_cancel_if_running()
    assert coordinator._ws_start_task is task


async def test_failing_cancel_is_logged_not_raised(hass):
    coordinator = make_coordinator(hass, password="secret")
    task = MagicMock()
    task.done.return_value = False
    task.cancel.side_effect = RuntimeError("boom")
    coordinator._ws_start_task = task
    coordinator._check_for_ws_task_and_cancel_if_running()
    assert coordinator._ws_start_task is None


# ----------------------------------------------------------------------------- device registry label

async def _device_for(hass, coordinator):
    entry = coordinator._config_entry
    coordinator.config_entry = entry
    coordinator._device_info_dict = {"identifiers": {(DOMAIN, "charger", "lan", "123456")}}
    coordinator._device_info_model_raw = "model"
    return dr.async_get(hass).async_get_or_create(config_entry_id=entry.entry_id, identifiers={(DOMAIN, "charger", "lan", "123456")})


async def test_device_label_shows_a_working_websocket(hass):
    coordinator = make_coordinator(hass, password="secret", websocket=True)
    device = await _device_for(hass, coordinator)
    coordinator.bridge._ws_LAST_UPDATE = time.time()
    await coordinator.call_later_update_device_registry(None)
    assert dr.async_get(hass).async_get(device.id).model == "model ✅"


async def test_device_label_shows_a_broken_websocket(hass):
    coordinator = make_coordinator(hass, password="secret")
    device = await _device_for(hass, coordinator)
    await coordinator.call_later_update_device_registry(None)
    assert dr.async_get(hass).async_get(device.id).model == "model ⛔"


async def test_device_label_is_skipped_without_identifiers(hass):
    coordinator = make_coordinator(hass, password="secret")
    coordinator._device_info_dict = {}
    await coordinator.call_later_update_device_registry(None)


async def test_device_label_is_skipped_in_polling_mode(hass):
    coordinator = make_coordinator(hass)
    device = await _device_for(hass, coordinator)
    await coordinator.call_later_update_device_registry(None)
    assert dr.async_get(hass).async_get(device.id).model is None


async def test_device_label_ignores_a_device_that_is_not_registered(hass):
    coordinator = make_coordinator(hass, password="secret")
    coordinator.config_entry = coordinator._config_entry
    coordinator._device_info_dict = {"identifiers": {(DOMAIN, "charger", "lan", "000000")}}
    await coordinator.call_later_update_device_registry(None)


# ----------------------------------------------------------------------------- housekeeping

async def test_delayed_update_refreshes_the_coordinator(hass):
    coordinator = make_coordinator(hass, data={})
    coordinator.async_refresh = AsyncMock()
    coordinator.request_update_in_sec(0)
    await coordinator._debounced_update_task
    coordinator.async_refresh.assert_awaited_once()


async def test_a_new_delayed_update_replaces_the_pending_one(hass):
    coordinator = make_coordinator(hass, data={})
    coordinator.async_refresh = AsyncMock()
    coordinator.request_update_in_sec(3600)
    first = coordinator._debounced_update_task
    coordinator.request_update_in_sec(3600)
    await asyncio.sleep(0)
    assert first.cancelled()
    coordinator.cancel_existing_debouncer()


async def test_clear_data_resets_errors_and_empties_the_data(hass):
    coordinator = make_coordinator(hass, data={"a": 1})
    coordinator._CLIENT_COMMUNICATION_ERROR_COUNT = 3
    coordinator._CLIENT_COMMUNICATION_ERROR_TS = 5
    coordinator._RESTART_TRIGGERED = True
    coordinator.clear_data()
    assert coordinator.data == {} and coordinator._CLIENT_COMMUNICATION_ERROR_COUNT == 0
    assert coordinator._CLIENT_COMMUNICATION_ERROR_TS == 0 and coordinator._RESTART_TRIGGERED is False


async def test_delayed_restart_reloads_the_config_entry(hass):
    coordinator = make_coordinator(hass, data={})
    with patch(f"{PKG}.asyncio.sleep", AsyncMock()), \
         patch.object(hass.config_entries, "async_reload", AsyncMock()) as reload:
        await coordinator.trigger_restart_delayed()
    reload.assert_awaited_once_with(coordinator._config_entry.entry_id)


async def test_event_callback_accepts_any_event(hass):
    coordinator = make_coordinator(hass, data={})
    assert coordinator(SimpleNamespace()) is True
    assert coordinator.cards_as_object_present() is False
