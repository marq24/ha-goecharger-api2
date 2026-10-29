"""Bridge, writing: every path from a value to the charger and back (HTTP and WebSocket).

HTTP is mocked with `aioclient_mock`, the WebSocket connection is a fake object. A write must either
return the written value, an error object, or an empty result, never raise for a bad answer.
"""
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import aiohttp
import pytest

from custom_components.goecharger_api2.pygoecharger_ha import GoeChargerApiV2Bridge
from custom_components.goecharger_api2.pygoecharger_ha.keys import IS_TRIGGER, Tag

from .factories import make_bridge

SET = "http://192.0.2.10/api/set"
SLEEP = "custom_components.goecharger_api2.pygoecharger_ha.asyncio.sleep"


# ----------------------------------------------------------------------------- one key, over HTTP

async def test_force_config_read_button_rereads_the_configuration(hass, aioclient_mock):
    bridge = make_bridge(hass)
    bridge.force_config_update = AsyncMock()
    key = Tag.INTERNAL_FORCE_CONFIG_READ.key
    assert await bridge.write_value_to_key(key, IS_TRIGGER) == {key: IS_TRIGGER}
    bridge.force_config_update.assert_awaited_once()
    assert aioclient_mock.call_count == 0


async def test_force_refresh_button_resets_the_timers(hass, aioclient_mock):
    bridge = make_bridge(hass)
    bridge.reset_stored_update_ts = AsyncMock()
    key = Tag.INTERNAL_FORCE_REFRESH_ALL.key
    assert await bridge.write_value_to_key(key, IS_TRIGGER) == {key: IS_TRIGGER}
    bridge.reset_stored_update_ts.assert_awaited_once()


async def test_any_other_trigger_does_nothing_and_sends_nothing(hass, aioclient_mock):
    bridge = make_bridge(hass)
    assert await bridge.write_value_to_key("other", IS_TRIGGER) == {"other": IS_TRIGGER}
    assert aioclient_mock.call_count == 0


async def test_websocket_flag_without_open_connection_falls_back_to_http(hass, aioclient_mock):
    aioclient_mock.get(SET, json={"amp": True})
    bridge = make_bridge(hass)
    bridge.ws_connected = True
    bridge._ws_connection = None
    assert await bridge.write_value_to_key("amp", 10) == {"amp": 10}
    assert aioclient_mock.call_count == 1


async def test_websocket_send_that_reports_failure_gives_an_empty_result(hass):
    bridge = make_bridge(hass, websocket=True)
    bridge._ws_send_command = AsyncMock(return_value=False)
    assert await bridge.write_value_to_key("amp", 10) == {}


# ----------------------------------------------------------------------------- several keys

async def test_multiple_keys_over_websocket_are_sent_one_after_the_other(hass):
    bridge = make_bridge(hass, websocket=True)
    bridge._ws_LAST_NEW_DATA_NOTIFY = 5
    with patch(SLEEP, AsyncMock()) as sleep:
        result = await bridge.write_multiple_values_to_keys({"ct": "x", "mca": 6}, "ct", "default")
    sent = [(c.args[0]["key"], c.args[0]["value"]) for c in bridge._ws_connection.send_json.await_args_list]
    assert sent == [("ct", "x"), ("mca", 6)] and sleep.await_count == 2 and result == {}
    assert bridge._ws_LAST_NEW_DATA_NOTIFY == 0


async def test_multiple_keys_over_http_are_encoded_by_type(hass, aioclient_mock):
    aioclient_mock.get(SET, json={"ct": True})
    bridge = make_bridge(hass)
    args = {"acp": True, "mca": 6, "x": 1.5, "name": "abc", "obj": {"a": 1}, "ignored": [1, 2]}
    assert await bridge.write_multiple_values_to_keys(args, "ct", "default") == {"ct": "default"}
    query = dict(aioclient_mock.mock_calls[0][1].query)
    assert query == {"acp": "true", "mca": "6", "x": "1.5", "name": '"abc"', "obj": '{"a":1}'}


# ----------------------------------------------------------------------------- the answer of the charger

async def test_charger_answer_with_the_key_resets_the_read_timers(hass, aioclient_mock):
    aioclient_mock.get(SET, json={"amp": True})
    bridge = make_bridge(hass)
    bridge._LAST_CONFIG_UPDATE_TS = bridge._LAST_FULL_STATE_UPDATE_TS = 9
    await bridge.write_value_to_key("amp", 6)
    assert bridge._LAST_CONFIG_UPDATE_TS == 0 and bridge._REQUEST_IDS_DATA is False


async def test_pv_data_answer_keeps_the_timers_and_asks_for_pv_values_for_a_charger(hass, aioclient_mock):
    aioclient_mock.get(SET, json={"ids": True})
    bridge = make_bridge(hass)
    bridge._LAST_CONFIG_UPDATE_TS = 9
    await bridge.write_value_to_key("ids", {"pGrid": 0})
    assert bridge._LAST_CONFIG_UPDATE_TS == 9 and bridge._REQUEST_IDS_DATA is True


async def test_pv_data_answer_for_a_controller_does_not_set_the_flag(hass, aioclient_mock):
    aioclient_mock.get(SET, json={"ids": True})
    bridge = make_bridge(hass, intg_type="controller")
    await bridge.write_value_to_key("ids", {"pGrid": 0})
    assert bridge._REQUEST_IDS_DATA is False


async def test_answer_without_the_key_is_an_error_object(hass, aioclient_mock):
    aioclient_mock.get(SET, json={"other": True})
    assert await make_bridge(hass).write_value_to_key("amp", 6) == {"err": {"other": True}}


async def test_answer_that_denies_the_key_with_false_is_an_error_object(hass, aioclient_mock):
    aioclient_mock.get(SET, json={"amp": False})
    assert await make_bridge(hass).write_value_to_key("amp", 6) == {"err": {"amp": False}}


async def test_empty_answer_gives_an_empty_result(hass, aioclient_mock):
    aioclient_mock.get(SET, json={})
    assert await make_bridge(hass).write_value_to_key("amp", 6) == {}


async def test_answer_that_is_not_json_gives_an_empty_result(hass, aioclient_mock):
    aioclient_mock.get(SET, text="not json", headers={"Content-Type": "application/json"})
    assert await make_bridge(hass).write_value_to_key("amp", 6) == {}


async def test_answer_with_the_wrong_content_type_gives_an_empty_result(hass, aioclient_mock):
    aioclient_mock.get(SET, text="<html>", headers={"Content-Type": "text/html"})
    assert await make_bridge(hass).write_value_to_key("amp", 6) == {}


@pytest.mark.parametrize("status", [403, 404, 422, 503])
async def test_other_statuses_give_an_empty_result(hass, aioclient_mock, status):
    aioclient_mock.get(SET, status=status, json={"amp": True})
    assert await make_bridge(hass).write_value_to_key("amp", 6) == {}


async def test_a_lost_connection_while_writing_is_raised_for_the_coordinator_to_handle(hass, aioclient_mock):
    aioclient_mock.get(SET, exc=aiohttp.ClientConnectionError("down"))
    with pytest.raises(aiohttp.ClientConnectionError):
        await make_bridge(hass).write_value_to_key("amp", 6)


async def test_cloud_write_sends_the_bearer_token(hass, aioclient_mock):
    from homeassistant.helpers.aiohttp_client import async_get_clientsession
    aioclient_mock.get("https://001234.api.v3.go-e.io/api/set", json={"amp": True})
    bridge = GoeChargerApiV2Bridge(web_session=async_get_clientsession(hass), intg_type="charger",
                                   serial="1234", token="tok")
    assert await bridge.write_value_to_key("amp", 6) == {"amp": 6}
    assert aioclient_mock.mock_calls[0][3] == {"Authorization": "Bearer tok"}
