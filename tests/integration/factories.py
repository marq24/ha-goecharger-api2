"""Shared builders for the tests: config entries, coordinators and fake WebSocket connections."""
from collections import ChainMap
from types import SimpleNamespace
from unittest.mock import AsyncMock

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.goecharger_api2 import GoeChargerDataUpdateCoordinator
from custom_components.goecharger_api2.const import DOMAIN


def make_entry(hass, serial="123456", intg_type="charger", mode="lan", password=None, **extra):
    data = {"mode": mode, "id": serial, "integration_type": intg_type, "scan_interval": 30, **extra}
    if mode == "lan":
        data.setdefault("host", "192.0.2.10")
    else:
        data.setdefault("token", "token")
    if password:
        data["password"] = password
    entry = MockConfigEntry(domain=DOMAIN, title=f"go-e {serial}", data=data)
    entry.add_to_hass(hass)
    return entry


def make_coordinator(hass, data=None, websocket=False, **entry_kwargs):
    """Real coordinator and bridge. `data` becomes coordinator.data (a plain dict, as the entities only read it)."""
    coordinator = GoeChargerDataUpdateCoordinator(hass, make_entry(hass, **entry_kwargs))
    bridge = coordinator.bridge
    coordinator.data = data if data is not None else ChainMap(
        bridge._ws_states, bridge._config, bridge._states, bridge._versions)
    if websocket:
        bridge.ws_connected = True
        bridge._ws_connection = SimpleNamespace(send_json=AsyncMock())
    return coordinator


def make_bridge(hass, intg_type="charger", password=None, websocket=False):
    from homeassistant.helpers.aiohttp_client import async_get_clientsession
    from custom_components.goecharger_api2.pygoecharger_ha import GoeChargerApiV2Bridge
    bridge = GoeChargerApiV2Bridge(web_session=async_get_clientsession(hass), intg_type=intg_type,
                                   host="192.0.2.10", access_password=password)
    if websocket:
        bridge.ws_connected = True
        bridge._ws_connection = SimpleNamespace(send_json=AsyncMock())
    return bridge
