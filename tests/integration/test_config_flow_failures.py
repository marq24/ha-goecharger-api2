"""Config flow: wrong or unreachable devices must end the flow with a clear reason and create no entry."""
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType

from custom_components.goecharger_api2 import config_flow
from custom_components.goecharger_api2.const import DOMAIN

LAN_STATUS = "http://192.0.2.10/api/status"
CLOUD_STATUS = "https://123456.api.v3.go-e.io/api/status"
GOOD_STATUS = {"sse": "123456", "typ": "go-eCharger_V4", "var": 11, "fwv": "59.4"}

LAN_INPUT = {"integration_type": "charger", "host": "192.0.2.10", "scan_interval": 30,
             "delay": False, "limit_to_11kw": False}
WAN_INPUT = {"integration_type": "charger", "id": "123456", "token": "token", "scan_interval": 120,
             "delay": False}


async def _start(hass, system):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] == FlowResultType.FORM and result["step_id"] == "user"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"stype": system})
    assert result["type"] == FlowResultType.FORM
    return result


# ----------------------------------------------------------------------------- positive control

async def test_valid_lan_device_creates_an_entry(hass, aioclient_mock):
    aioclient_mock.get(LAN_STATUS, json=GOOD_STATUS)
    result = await _start(hass, "lan")
    with patch("custom_components.goecharger_api2.async_setup_entry", AsyncMock(return_value=True)):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], LAN_INPUT)
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "go-eCharger API v2 [123456] Local"
    assert result["data"]["id"] == "123456" and result["data"]["mode"] == "lan"


# ----------------------------------------------------------------------------- failures

@pytest.mark.parametrize("status", [403, 404, 500])
async def test_lan_device_that_answers_with_an_error_is_rejected(hass, aioclient_mock, status):
    aioclient_mock.get(LAN_STATUS, status=status)
    result = await _start(hass, "lan")
    result = await hass.config_entries.flow.async_configure(result["flow_id"], LAN_INPUT)
    assert result["type"] == FlowResultType.ABORT and result["reason"] == "auth_lan"
    assert hass.config_entries.async_entries(DOMAIN) == []


async def test_lan_device_with_an_empty_answer_is_rejected(hass, aioclient_mock):
    aioclient_mock.get(LAN_STATUS, json={})
    result = await _start(hass, "lan")
    result = await hass.config_entries.flow.async_configure(result["flow_id"], LAN_INPUT)
    assert result["type"] == FlowResultType.ABORT and result["reason"] == "auth_lan"


async def test_unreachable_lan_device_is_rejected(hass, aioclient_mock):
    from aiohttp import ClientConnectionError
    aioclient_mock.get(LAN_STATUS, exc=ClientConnectionError("no route"))
    result = await _start(hass, "lan")
    result = await hass.config_entries.flow.async_configure(result["flow_id"], LAN_INPUT)
    assert result["type"] == FlowResultType.ABORT and result["reason"] == "auth_lan"


async def test_failed_websocket_check_falls_back_to_http_and_then_rejects(hass, aioclient_mock):
    aioclient_mock.get(LAN_STATUS, status=403)
    result = await _start(hass, "lan")
    with patch.object(config_flow.GoeChargerApiV2FlowHandler, "_check_ws_connection_and_flags",
                      AsyncMock(return_value=False)) as ws_check:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {**LAN_INPUT, "password": "wrong"})
    ws_check.assert_awaited_once()
    assert result["type"] == FlowResultType.ABORT and result["reason"] == "auth_lan"


async def test_cloud_device_with_a_wrong_token_is_rejected(hass, aioclient_mock):
    aioclient_mock.get(CLOUD_STATUS, status=403)
    result = await _start(hass, "wan")
    result = await hass.config_entries.flow.async_configure(result["flow_id"], WAN_INPUT)
    assert result["type"] == FlowResultType.ABORT and result["reason"] == "auth_wan"
    assert hass.config_entries.async_entries(DOMAIN) == []
