"""Config flow: successful setups, the value rules, reconfiguration and the WebSocket check.

The charger is mocked: HTTP with `aioclient_mock`, the WebSocket check with a fake connection.
"""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.goecharger_api2 import config_flow
from custom_components.goecharger_api2.const import DOMAIN
from custom_components.goecharger_api2.pygoecharger_ha import GoeChargerApiV2Bridge, TargetedEvent

LAN_STATUS = "http://192.0.2.10/api/status"
CLOUD_STATUS = "https://123456.api.v3.go-e.io/api/status"
CHARGER = {"sse": "123456", "typ": "go-eCharger_V4", "var": 22, "fwv": "59.4"}
CONTROLLER = {"sse": "654321", "typ": "go-eController", "fwv": "1.1.1"}
SETUP = "custom_components.goecharger_api2.async_setup_entry"


async def _start(hass, system):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    return await hass.config_entries.flow.async_configure(result["flow_id"], {"stype": system})


def _lan(**extra):
    return {"integration_type": "charger", "host": "192.0.2.10", "scan_interval": 30, "delay": False,
            "limit_to_11kw": False, **extra}


def _wan(**extra):
    return {"integration_type": "charger", "id": "123456", "token": "tok", "scan_interval": 120, "delay": False, **extra}


async def _create(hass, system, data):
    result = await _start(hass, system)
    with patch(SETUP, AsyncMock(return_value=True)):
        return await hass.config_entries.flow.async_configure(result["flow_id"], data)


# ----------------------------------------------------------------------------- creating entries

async def test_cloud_charger_is_created_with_its_title_and_a_minimum_interval(hass, aioclient_mock):
    aioclient_mock.get(CLOUD_STATUS, json=CHARGER)
    result = await _create(hass, "wan", _wan(scan_interval=10))
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "go-eCharger API v2 [123456] Cloud"
    assert result["data"]["mode"] == "wan" and result["data"]["scan_interval"] == 30
    assert result["data"]["type"].endswith("Cloud") and "password" not in result["data"]


async def test_local_charger_gets_at_least_five_seconds_and_keeps_its_model(hass, aioclient_mock):
    aioclient_mock.get(LAN_STATUS, json=CHARGER)
    result = await _create(hass, "lan", _lan(scan_interval=1))
    assert result["data"]["scan_interval"] == 5 and result["data"]["model"] == "22"
    assert result["data"]["type"] == "go-eCharger V4 [22 kW] Local"


async def test_local_controller_is_created_with_its_own_title(hass, aioclient_mock):
    aioclient_mock.get(LAN_STATUS, json=CONTROLLER)
    result = await _create(hass, "lan", _lan(integration_type="controller"))
    assert result["title"] == "go-eController API v2 [654321] Local"
    assert result["data"]["type"] == "go-eController Local" and result["data"]["model"] == "eControl"


async def test_cloud_controller_is_created_with_its_own_title(hass, aioclient_mock):
    aioclient_mock.get(CLOUD_STATUS, json={**CONTROLLER, "sse": "123456"})
    result = await _create(hass, "wan", _wan(integration_type="controller"))
    assert result["title"] == "go-eController API v2 [123456] Cloud"


def _ws_found(states):
    async def check(self, client):
        client._ws_states = dict(states)
        client.ws_connected = True
        return True
    return check


@pytest.mark.parametrize("flags", [
    {"hai": True, "cae": True}, {"hai": False, "cae": False}, {}])
async def test_websocket_login_creates_the_entry_with_the_password(hass, flags):
    states = {**CHARGER, **flags}
    with patch.object(config_flow.GoeChargerApiV2FlowHandler, "_check_ws_connection_and_flags", _ws_found(states)):
        result = await _create(hass, "lan", _lan(password=" secret "))
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"]["password"] == " secret " and result["data"]["id"] == "123456"


async def test_websocket_check_for_the_cloud_also_keeps_the_password(hass):
    with patch.object(config_flow.GoeChargerApiV2FlowHandler, "_check_ws_connection_and_flags", _ws_found(CHARGER)):
        result = await _create(hass, "wan", _wan(password="secret"))
    assert result["data"]["password"] == "secret" and result["data"]["mode"] == "wan"


# ----------------------------------------------------------------------------- reconfiguring

async def _reconfigure(hass, data):
    entry = MockConfigEntry(domain=DOMAIN, title="t", data=data, version=2, minor_version=1)
    entry.add_to_hass(hass)
    return entry, await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_RECONFIGURE, "entry_id": entry.entry_id})


async def test_reconfigure_a_local_charger_shows_the_stored_values(hass):
    entry, result = await _reconfigure(hass, {"mode": "lan", "host": "192.0.2.10", "id": "123456",
                                              "integration_type": "charger", "scan_interval": 45, "limit_to_11kw": True})
    assert result["type"] == FlowResultType.FORM and result["step_id"] == "user_lan"
    defaults = {str(k): k.default() if callable(k.default) else None for k in result["data_schema"].schema}
    assert defaults["host"] == "192.0.2.10" and defaults["scan_interval"] == 45 and defaults["limit_to_11kw"] is True


async def test_reconfigure_a_cloud_charger_shows_the_cloud_form(hass):
    entry, result = await _reconfigure(hass, {"mode": "wan", "id": "123456", "token": "tok",
                                              "integration_type": "charger", "scan_interval": 90})
    assert result["type"] == FlowResultType.FORM and result["step_id"] == "user_wan"


async def test_reconfigure_with_a_working_device_updates_and_reloads_the_entry(hass, aioclient_mock):
    aioclient_mock.get(LAN_STATUS, json=CHARGER)
    entry, result = await _reconfigure(hass, {"mode": "lan", "host": "192.0.2.10", "id": "123456",
                                              "integration_type": "charger", "scan_interval": 45})
    with patch.object(hass.config_entries, "async_reload", AsyncMock()):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], _lan(scan_interval=60))
    assert result["type"] == FlowResultType.ABORT and result["reason"] == "reconfigure_successful"
    assert entry.data["scan_interval"] == 60


async def test_reconfigure_with_a_working_cloud_device_updates_the_entry(hass, aioclient_mock):
    aioclient_mock.get(CLOUD_STATUS, json=CHARGER)
    entry, result = await _reconfigure(hass, {"mode": "wan", "id": "123456", "token": "tok",
                                              "integration_type": "charger", "scan_interval": 90})
    with patch.object(hass.config_entries, "async_reload", AsyncMock()):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], _wan(scan_interval=200))
    assert result["reason"] == "reconfigure_successful" and entry.data["scan_interval"] == 200


async def test_the_first_step_offers_local_and_cloud(hass):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] == FlowResultType.FORM and result["step_id"] == "user"


# ----------------------------------------------------------------------------- the WebSocket check

def _handler(hass):
    handler = config_flow.GoeChargerApiV2FlowHandler()
    handler.hass = hass
    return handler


def _client(connect):
    client = GoeChargerApiV2Bridge(web_session=None, intg_type="charger", host="192.0.2.10", access_password="secret")
    client.ws_connect = connect
    return client


async def test_check_reports_success_when_the_first_data_arrives(hass):
    async def connect(a_event=None, keep_ws_states_after_close=False):
        a_event.set()
    client = _client(connect)
    with patch.object(config_flow.asyncio, "sleep", AsyncMock()):
        assert await _handler(hass)._check_ws_connection_and_flags(client) is True


async def test_check_reports_failure_for_errors_from_the_connection(hass):
    async def connect(a_event=None, keep_ws_states_after_close=False):
        a_event.set_error(Exception("Authentication failed"))
    with patch.object(config_flow.asyncio, "sleep", AsyncMock()):
        assert await _handler(hass)._check_ws_connection_and_flags(_client(connect)) is False


@pytest.mark.parametrize("error", [asyncio.TimeoutError(), asyncio.CancelledError()])
async def test_check_reports_failure_when_the_wait_ends_without_data(hass, error):
    async def connect(a_event=None, keep_ws_states_after_close=False):
        await asyncio.sleep(3600)
    real_wait_for = asyncio.wait_for
    calls = []

    async def wait_for(awaitable, timeout):
        calls.append(timeout)
        if len(calls) == 1:
            awaitable.close() if hasattr(awaitable, "close") else None
            raise error
        return await real_wait_for(awaitable, 0.5)

    with patch.object(config_flow.asyncio, "wait_for", wait_for), patch.object(config_flow.asyncio, "sleep", AsyncMock()):
        assert await _handler(hass)._check_ws_connection_and_flags(_client(connect)) is False
