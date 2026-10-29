"""Coordinator and setup: what happens when the charger cannot be reached or answers badly.

Covers the error counter, the 2 minute pause after a connection error, the delayed restart after more
than 5 errors, writes during that pause, and the start of the config entry (ConfigEntryNotReady).
"""
import time
from collections import ChainMap
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import ClientConnectionError
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.goecharger_api2 import GoeChargerDataUpdateCoordinator, async_setup_entry
from custom_components.goecharger_api2.const import DOMAIN


def _entry(hass, password=None):
    data = {"mode": "lan", "host": "192.0.2.10", "id": "123456", "integration_type": "charger",
            "scan_interval": 30}
    if password:
        data["password"] = password
    entry = MockConfigEntry(domain=DOMAIN, title="t", data=data)
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
async def coordinator(hass):
    coordinator = GoeChargerDataUpdateCoordinator(hass, _entry(hass))
    bridge = coordinator.bridge
    coordinator.data = ChainMap(bridge._ws_states, bridge._config, bridge._states, bridge._versions)
    coordinator.trigger_restart_delayed = AsyncMock()
    return coordinator


# ----------------------------------------------------------------------------- reading

async def test_connection_error_while_reading_raises_update_failed_and_counts(coordinator):
    coordinator.bridge.read_all = AsyncMock(side_effect=ClientConnectionError("down"))
    with pytest.raises(UpdateFailed, match="ClientConnectionError"):
        await coordinator._async_update_data()
    assert coordinator._CLIENT_COMMUNICATION_ERROR_COUNT == 1


async def test_unexpected_error_while_reading_raises_update_failed(coordinator):
    coordinator.bridge.read_all = AsyncMock(side_effect=RuntimeError("boom"))
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


async def test_no_request_is_made_during_the_pause_after_a_connection_error(coordinator):
    coordinator.bridge.read_all = AsyncMock(side_effect=ClientConnectionError("down"))
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()
    coordinator.bridge.read_all.reset_mock()

    assert await coordinator._async_update_data() is coordinator.data  # pause: old data, no request
    coordinator.bridge.read_all.assert_not_awaited()


async def test_more_than_five_errors_trigger_exactly_one_restart(hass, coordinator):
    coordinator.bridge.read_all = AsyncMock(side_effect=ClientConnectionError("down"))
    for _ in range(6):
        coordinator._CLIENT_COMMUNICATION_ERROR_TS = 0  # skip the pause between the attempts
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()
        await hass.async_block_till_done()
    assert coordinator._RESTART_TRIGGERED is True
    coordinator.trigger_restart_delayed.assert_awaited_once()

    # while the restart is pending, further polls neither fail nor trigger a second restart
    for _ in range(2):
        coordinator._CLIENT_COMMUNICATION_ERROR_TS = 0
        assert await coordinator._async_update_data() is coordinator.data
        await hass.async_block_till_done()
    coordinator.trigger_restart_delayed.assert_awaited_once()


async def test_five_errors_do_not_trigger_a_restart_yet(hass, coordinator):
    coordinator.bridge.read_all = AsyncMock(side_effect=ClientConnectionError("down"))
    for _ in range(5):
        coordinator._CLIENT_COMMUNICATION_ERROR_TS = 0
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()
    await hass.async_block_till_done()
    assert coordinator._RESTART_TRIGGERED is False
    coordinator.trigger_restart_delayed.assert_not_awaited()


async def test_no_request_is_made_while_a_restart_is_pending(coordinator):
    coordinator._RESTART_TRIGGERED = True
    coordinator.bridge.read_all = AsyncMock()
    assert await coordinator._async_update_data() is coordinator.data
    coordinator.bridge.read_all.assert_not_awaited()


async def test_a_successful_read_clears_the_error_state(coordinator):
    coordinator._CLIENT_COMMUNICATION_ERROR_COUNT = 3
    coordinator._CLIENT_COMMUNICATION_ERROR_TS = 0
    coordinator.bridge.read_all = AsyncMock(return_value={"car": 1})
    assert await coordinator._async_update_data() == {"car": 1}
    assert coordinator._CLIENT_COMMUNICATION_ERROR_COUNT == 0


# ----------------------------------------------------------------------------- writing during an outage

@pytest.mark.parametrize("pause", ["error_pause", "restart_pending"])
async def test_writes_are_refused_without_touching_the_charger(coordinator, pause):
    if pause == "error_pause":
        coordinator._CLIENT_COMMUNICATION_ERROR_TS = time.time()
    else:
        coordinator._RESTART_TRIGGERED = True
    coordinator.bridge.write_value_to_key = AsyncMock()
    coordinator.bridge.write_multiple_values_to_keys = AsyncMock()

    with pytest.raises(ValueError):
        await coordinator.async_write_key("amp", 10)
    with pytest.raises(ValueError):
        await coordinator.async_write_multiple_keys({"ct": "1"}, "ct", "default")
    coordinator.bridge.write_value_to_key.assert_not_awaited()
    coordinator.bridge.write_multiple_values_to_keys.assert_not_awaited()


async def test_unexpected_write_error_becomes_value_error(coordinator):
    coordinator.bridge.write_value_to_key = AsyncMock(side_effect=RuntimeError("boom"))
    with pytest.raises(ValueError, match="RuntimeError"):
        await coordinator.async_write_key("amp", 10)


# ----------------------------------------------------------------------------- start of the config entry

async def test_setup_fails_when_the_first_poll_fails(hass):
    entry = _entry(hass)
    with patch.object(GoeChargerDataUpdateCoordinator, "_async_update_data",
                      AsyncMock(side_effect=UpdateFailed("down"))):
        with pytest.raises(ConfigEntryNotReady):
            await async_setup_entry(hass, entry)


async def test_setup_fails_when_versions_cannot_be_read(hass):
    entry = _entry(hass)
    with patch.object(GoeChargerDataUpdateCoordinator, "_async_update_data", AsyncMock(return_value={"car": 1})), \
         patch.object(GoeChargerDataUpdateCoordinator, "read_versions", AsyncMock(return_value=False)):
        with pytest.raises(ConfigEntryNotReady):
            await async_setup_entry(hass, entry)


async def test_setup_fails_when_the_websocket_delivers_no_data(hass):
    entry = _entry(hass, password="secret")
    with patch.object(GoeChargerDataUpdateCoordinator, "start_websocket_and_wait_for_first_data",
                      AsyncMock(return_value=False)):
        with pytest.raises(ConfigEntryNotReady):
            await async_setup_entry(hass, entry)


async def test_setup_fails_when_the_websocket_start_raises(hass):
    entry = _entry(hass, password="secret")
    with patch.object(GoeChargerDataUpdateCoordinator, "start_websocket_and_wait_for_first_data",
                      AsyncMock(side_effect=ConfigEntryNotReady("timeout"))):
        with pytest.raises(ConfigEntryNotReady):
            await async_setup_entry(hass, entry)
    assert entry.entry_id not in hass.data.get(DOMAIN, {})
