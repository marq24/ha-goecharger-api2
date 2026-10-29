"""Bridge, HTTP path: what is requested from the charger and how answers are interpreted.

The HTTP layer is mocked with Home Assistant's `aioclient_mock`; the bridge is the real code.
The expected requests follow the official go-e HTTP API v2 documentation (http-en.md, cloudapi-en.md).
"""
import pytest
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.goecharger_api2.pygoecharger_ha import GoeChargerApiV2Bridge, NonNullDict

LAN_STATUS = "http://192.0.2.10/api/status"
LAN_SET = "http://192.0.2.10/api/set"


def _lan(hass):
    return GoeChargerApiV2Bridge(web_session=async_get_clientsession(hass), intg_type="charger",
                                 host="192.0.2.10")


def _cloud(hass, serial="1234"):
    return GoeChargerApiV2Bridge(web_session=async_get_clientsession(hass), intg_type="charger",
                                 serial=serial, token="secret-token")


def _query(aioclient_mock, index=-1):
    return dict(aioclient_mock.mock_calls[index][1].query)


# ----------------------------------------------------------------------------- reading

async def test_read_filtered_sends_comma_separated_filter(hass, aioclient_mock):
    aioclient_mock.get(LAN_STATUS, json={"car": 1, "amp": 16})
    result = await _lan(hass)._read_filtered_data("car,amp", "test")
    assert _query(aioclient_mock) == {"filter": "car,amp"}
    assert result == {"car": 1, "amp": 16}
    assert isinstance(result, NonNullDict)


@pytest.mark.parametrize("status", [403, 404, 500])
async def test_read_filtered_returns_empty_for_error_status(hass, aioclient_mock, status):
    aioclient_mock.get(LAN_STATUS, status=status, json={"error": "x"})
    assert await _lan(hass)._read_filtered_data("car", "test") == {}


async def test_read_filtered_returns_empty_for_invalid_json(hass, aioclient_mock):
    aioclient_mock.get(LAN_STATUS, text="not json")
    assert await _lan(hass)._read_filtered_data("car", "test") == {}


async def test_none_null_get_treats_json_null_as_missing(hass, aioclient_mock):
    aioclient_mock.get(LAN_STATUS, json={"car": None})
    result = await _lan(hass)._read_filtered_data("car", "test")
    assert result.none_null_get("car", 7) == 7


# ----------------------------------------------------------------------------- cloud addressing

async def test_cloud_url_pads_serial_and_sends_bearer_token(hass, aioclient_mock):
    aioclient_mock.get("https://001234.api.v3.go-e.io/api/status", json={"car": 1})
    await _cloud(hass)._read_filtered_data("car", "test")
    headers = aioclient_mock.mock_calls[0][3]
    assert headers == {"Authorization": "Bearer secret-token"}


async def test_lan_requests_send_no_authorization_header(hass, aioclient_mock):
    aioclient_mock.get(LAN_STATUS, json={"car": 1})
    await _lan(hass)._read_filtered_data("car", "test")
    assert aioclient_mock.mock_calls[0][3] is None


# ----------------------------------------------------------------------------- writing

@pytest.mark.parametrize("value, expected", [
    (16, "16"),
    (True, "true"),
    (False, "false"),
    (3.5, "3.5"),
    ("my charger", '"my charger"'),
    ({"pGrid": -500.0, "pPv": 1500.0}, '{"pGrid":-500.0,"pPv":1500.0}'),
])
async def test_write_encodes_value_as_json_query_parameter(hass, aioclient_mock, value, expected):
    aioclient_mock.get(LAN_SET, json={"x": True})
    await _lan(hass).write_value_to_key("x", value)
    assert _query(aioclient_mock) == {"x": expected}


async def test_write_none_is_sent_as_null(hass, aioclient_mock):
    aioclient_mock.get(LAN_SET, json={"dwo": True})
    await _lan(hass).write_value_to_key("dwo", None)
    assert str(aioclient_mock.mock_calls[0][1]).endswith("/api/set?dwo=null")


async def test_write_success_returns_key_and_value(hass, aioclient_mock):
    aioclient_mock.get(LAN_SET, json={"amp": True})
    assert await _lan(hass).write_value_to_key("amp", 10) == {"amp": 10}


@pytest.mark.xfail(strict=True, reason=(
    "http-en.md: the answer holds 'true for success, or a string error message' per key. The bridge "
    "tests the value for truthiness, so an error string counts as success. Not verified on a real charger."))
async def test_write_rejected_by_charger_returns_err(hass, aioclient_mock):
    aioclient_mock.get(LAN_SET, json={"amp": "value out of range"})
    result = await _lan(hass).write_value_to_key("amp", 99)
    assert result == {"err": {"amp": "value out of range"}}


async def test_write_ids_sets_flag_to_read_pv_values_in_hibernation(hass, aioclient_mock):
    aioclient_mock.get(LAN_SET, json={"ids": True})
    bridge = _lan(hass)
    await bridge.write_value_to_key("ids", {"pGrid": 0, "pPv": 0, "pAkku": 0})
    assert bridge._REQUEST_IDS_DATA is True


async def test_write_other_key_forces_config_and_state_refresh(hass, aioclient_mock):
    aioclient_mock.get(LAN_SET, json={"amp": True})
    bridge = _lan(hass)
    bridge._LAST_CONFIG_UPDATE_TS = bridge._LAST_FULL_STATE_UPDATE_TS = 123.0
    await bridge.write_value_to_key("amp", 10)
    assert bridge._LAST_CONFIG_UPDATE_TS == 0 and bridge._LAST_FULL_STATE_UPDATE_TS == 0


@pytest.mark.xfail(strict=True, reason=(
    "Official cloud docs: /api/set answers HTTP 202 on success; the bridge only accepts 200. "
    "Not verified against the real cloud. Remove the marker when the behaviour is clarified."))
async def test_cloud_write_accepts_http_202(hass, aioclient_mock):
    aioclient_mock.get("https://001234.api.v3.go-e.io/api/set", status=202, json={"amp": True})
    assert await _cloud(hass).write_value_to_key("amp", 10) == {"amp": 10}
