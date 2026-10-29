"""Services (set_pv_data, stop_charging), the multi-charger registry and unloading of entries.

Tests marked `xfail(strict=True)` describe behaviour that is wrong today. They turn the run red
(XPASS) as soon as the bug is fixed, so the marker must then be removed. All other tests pin
behaviour that works. The bridge is real; only the WebSocket connection object is faked.
"""
import logging
from collections import ChainMap
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.goecharger_api2 import (
    ACTIVE_CHARGER_COUNTER,
    GoeChargerDataUpdateCoordinator,
    async_unload_entry,
)
from custom_components.goecharger_api2 import service as service_module
from custom_components.goecharger_api2.const import DOMAIN, SERVICE_SET_PV_DATA, SERVICE_STOP_CHARGING
from custom_components.goecharger_api2.service import (
    GoeChargerApiV2Service,
    add_config_entry_to_service,
    remove_config_entry_from_service,
)
from custom_components.goecharger_api2.pygoecharger_ha.keys import Tag

BRIDGE_SLEEP = "custom_components.goecharger_api2.pygoecharger_ha.asyncio.sleep"
SERVICE_SLEEP = "custom_components.goecharger_api2.service.asyncio.sleep"


def _entry(hass, serial="123456", intg_type="charger"):
    entry = MockConfigEntry(domain=DOMAIN, title=f"go-e {serial}", data={
        "mode": "lan", "host": "192.0.2.10", "id": serial, "integration_type": intg_type,
        "scan_interval": 30})
    entry.add_to_hass(hass)
    return entry


def _coordinator(hass, entry, websocket):
    coordinator = GoeChargerDataUpdateCoordinator(hass, entry)
    bridge = coordinator.bridge
    coordinator.data = ChainMap(bridge._ws_states, bridge._config, bridge._states, bridge._versions)
    if websocket:
        bridge.ws_connected = True
        bridge._ws_connection = SimpleNamespace(send_json=AsyncMock())
    return coordinator


def _sent(coordinator):
    """(key, value) of every setValue message that was sent over the fake WebSocket."""
    calls = coordinator.bridge._ws_connection.send_json.await_args_list
    return [(c.args[0]["key"], c.args[0]["value"]) for c in calls]


def _call(**data):
    return SimpleNamespace(data=data, return_response=True)


@pytest.fixture(autouse=True)
def clean_registry():
    service_module._COORDINATOR_PER_CONFIG_ENTRY_ID_MAP = {}
    yield
    service_module._COORDINATOR_PER_CONFIG_ENTRY_ID_MAP = {}


# --------------------------------------------------------------------------- stop_charging

async def test_stop_charging_in_websocket_mode_sends_lock_and_unlock(hass):
    """The reported TypeError is gone: frc=1, wait, frc=0."""
    coordinator = _coordinator(hass, _entry(hass), websocket=True)
    service = GoeChargerApiV2Service(hass, coordinator._config_entry, coordinator)
    with patch(SERVICE_SLEEP, AsyncMock()):
        result = await service.stop_charging(_call())
    assert result["success"] == "true"
    assert _sent(coordinator) == [(Tag.FRC.key, 1), (Tag.FRC.key, 0)]
    assert service._stop_in_progress is False


@pytest.mark.xfail(strict=True, reason="stop_charging does not reset _stop_in_progress when the first write fails (service.py)")
async def test_failed_lock_write_blocks_later_stop_requests(hass):
    """a ValueError on the first write leaves _stop_in_progress True forever."""
    coordinator = _coordinator(hass, _entry(hass), websocket=True)
    service = GoeChargerApiV2Service(hass, coordinator._config_entry, coordinator)
    coordinator.async_write_key = AsyncMock(side_effect=ValueError("charger unreachable"))
    await service.stop_charging(_call())
    assert service._stop_in_progress is False


@pytest.mark.xfail(strict=True, reason="stop_charging does not reset _stop_in_progress when the unlock write fails (service.py)")
async def test_failed_unlock_write_leaves_flag_stuck(hass):
    """if frc=0 cannot be written after the wait, the charger stays locked
    and the flag blocks every later stop_charging call."""
    coordinator = _coordinator(hass, _entry(hass), websocket=True)
    service = GoeChargerApiV2Service(hass, coordinator._config_entry, coordinator)
    coordinator.async_write_key = AsyncMock(side_effect=[{Tag.FRC.key: 1}, ValueError("down")])
    with patch(SERVICE_SLEEP, AsyncMock()):
        await service.stop_charging(_call())
    assert service._stop_in_progress is False


# --------------------------------------------------------------------------- WebSocket write results

@pytest.mark.xfail(strict=True, reason="write_multiple_values_to_keys returns {} over WebSocket; handle_write_result only skips on None")
async def test_websocket_multi_write_logs_no_error_on_success(hass, caplog):
    """a successful multi-key write in WebSocket mode is logged as an ERROR."""
    coordinator = _coordinator(hass, _entry(hass), websocket=True)
    with patch(BRIDGE_SLEEP, AsyncMock()), caplog.at_level(logging.ERROR):
        await coordinator.async_write_multiple_keys({"ct": "1", "mca": 6}, "ct", "default")
    assert [k for k, _ in _sent(coordinator)] == ["ct", "mca"]
    errors = [r.message for r in caplog.records if r.levelno >= logging.ERROR]
    assert errors == []


async def test_websocket_single_write_stores_requested_value_before_confirmation(hass):
    """Characterisation: the requested value is stored at once, not after the device's answer.
    If the charger rejects the command, this value stays until the device reports the key again."""
    coordinator = _coordinator(hass, _entry(hass), websocket=True)
    await coordinator.async_write_key("amp", 10)
    assert coordinator.data["amp"] == 10


# --------------------------------------------------------------------------- multi-charger registry

async def test_second_charger_is_reachable_by_configid(hass):
    a = _coordinator(hass, _entry(hass, "111111"), websocket=False)
    b = _coordinator(hass, _entry(hass, "222222"), websocket=False)
    service = GoeChargerApiV2Service(hass, a._config_entry, a)
    add_config_entry_to_service(b._config_entry, b)
    _, found = service.get_coordinator(_call(configid=b._config_entry.entry_id))
    assert found is b


async def test_reloaded_charger_replaces_stale_coordinator(hass):
    a = _coordinator(hass, _entry(hass, "111111"), websocket=False)
    b = _coordinator(hass, _entry(hass, "222222"), websocket=False)
    service = GoeChargerApiV2Service(hass, a._config_entry, a)
    add_config_entry_to_service(b._config_entry, b)

    remove_config_entry_from_service(a._config_entry)             # unload of A
    new_a = _coordinator(hass, a._config_entry, websocket=False)  # reload of A
    add_config_entry_to_service(a._config_entry, new_a)

    _, found = service.get_coordinator(_call(configid=a._config_entry.entry_id))
    assert found is new_a


@pytest.mark.xfail(strict=True, reason="a reloaded entry is appended behind the others, so the default charger changes")
async def test_default_charger_does_not_change_after_reload(hass):
    """without configid the first registered charger is used. After A is reloaded it
    is appended behind B, so the default silently switches from A to B."""
    a = _coordinator(hass, _entry(hass, "111111"), websocket=False)
    b = _coordinator(hass, _entry(hass, "222222"), websocket=False)
    service = GoeChargerApiV2Service(hass, a._config_entry, a)
    add_config_entry_to_service(b._config_entry, b)
    _, before = service.get_coordinator(_call())

    remove_config_entry_from_service(a._config_entry)
    add_config_entry_to_service(a._config_entry, a)
    _, after = service.get_coordinator(_call())
    assert after is before


# --------------------------------------------------------------------------- unload counting

def _register_services(hass):
    async def _noop(call):
        return None
    hass.services.async_register(DOMAIN, SERVICE_SET_PV_DATA, _noop)
    hass.services.async_register(DOMAIN, SERVICE_STOP_CHARGING, _noop)


@pytest.mark.xfail(strict=True, reason="ACTIVE_CHARGER_COUNTER is raised for chargers only but lowered for every entry")
async def test_unloading_a_controller_keeps_the_charger_services(hass):
    """the active-charger counter is only raised for chargers but lowered for every
    entry, so unloading a controller removes the services of a still-running charger."""
    controller = _entry(hass, "999999", intg_type="controller")
    hass.data[DOMAIN] = {controller.entry_id: MagicMock(), ACTIVE_CHARGER_COUNTER: 1}  # one charger
    _register_services(hass)
    with patch.object(hass.config_entries, "async_unload_platforms", AsyncMock(return_value=True)):
        await async_unload_entry(hass, controller)
    assert hass.services.has_service(DOMAIN, SERVICE_SET_PV_DATA)


@pytest.mark.xfail(strict=True, reason="ACTIVE_CHARGER_COUNTER key does not exist when only controllers are configured")
async def test_unloading_a_controller_without_any_charger_does_not_raise(hass):
    """with only controllers configured the counter key does not exist."""
    controller = _entry(hass, "999999", intg_type="controller")
    hass.data[DOMAIN] = {controller.entry_id: MagicMock()}
    with patch.object(hass.config_entries, "async_unload_platforms", AsyncMock(return_value=True)):
        assert await async_unload_entry(hass, controller) is True
