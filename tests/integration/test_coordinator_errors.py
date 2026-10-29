"""Coordinator: connection errors while writing must be counted and reported as ValueError."""
from unittest.mock import AsyncMock

import pytest
from aiohttp import ClientConnectionError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.goecharger_api2 import GoeChargerDataUpdateCoordinator

DOMAIN = "goecharger_api2"


@pytest.fixture
async def coordinator(hass):
    entry = MockConfigEntry(domain=DOMAIN, title="test", data={
        "mode": "lan", "host": "192.0.2.10", "id": "123456", "integration_type": "charger",
        "scan_interval": 30})
    entry.add_to_hass(hass)
    return GoeChargerDataUpdateCoordinator(hass, entry)


async def test_write_key_connection_error_is_counted(coordinator):
    coordinator.bridge.write_value_to_key = AsyncMock(side_effect=ClientConnectionError("down"))
    with pytest.raises(ValueError, match="ClientConnectionError while writing amp"):
        await coordinator.async_write_key("amp", 16)
    assert coordinator._CLIENT_COMMUNICATION_ERROR_COUNT == 1


async def test_write_multiple_keys_connection_error_is_counted(coordinator):
    coordinator.bridge.write_multiple_values_to_keys = AsyncMock(side_effect=ClientConnectionError("down"))
    with pytest.raises(ValueError, match="ClientConnectionError while writing multiple ct"):
        await coordinator.async_write_multiple_keys({"ct": "1"}, "ct", "default")
    assert coordinator._CLIENT_COMMUNICATION_ERROR_COUNT == 1
