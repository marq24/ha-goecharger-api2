"""Bridge.read_versions: the same device answer must lead to the same `_versions` via HTTP and via WebSocket.

Background is issue #176: on a charger with firmware 59.4 the `cll` object contained `cableCurrentLimit`
when read via the HTTP API, but not when read via the WebSocket. The bridge only passes the data on, so
these tests pin that it does not change the content depending on the transport. They cannot show what a
real charger sends over each transport; that needs a read-only comparison on the device.
"""
import pytest

from custom_components.goecharger_api2.pygoecharger_ha import NonNullDict
from custom_components.goecharger_api2.pygoecharger_ha.const import FILTER_VERSIONS

from .factories import make_bridge

STATUS = "http://192.0.2.10/api/status"

PAYLOADS = [
    pytest.param({"typ": "go-eCharger_V4", "fwv": "59.4", "var": 22,
                  "cll": {"cableCurrentLimit": 32, "currentLimitMax": 32}}, id="cll_with_cable_limit"),
    pytest.param({"typ": "go-eCharger_V4", "fwv": "59.4", "var": 22,
                  "cll": {"currentLimitMax": 32, "requestedCurrent": 16}}, id="cll_without_cable_limit"),
    pytest.param({"typ": "go-eCharger_V4", "fwv": "59.4", "var": 22}, id="no_cll"),
]


def test_cll_is_part_of_the_versions_filter():
    assert "cll" in FILTER_VERSIONS.split(",")


@pytest.mark.parametrize("payload", PAYLOADS)
async def test_versions_are_identical_via_http_and_websocket(hass, aioclient_mock, payload):
    aioclient_mock.get(STATUS, json=payload)
    via_http = make_bridge(hass)
    await via_http.read_versions()

    via_ws = make_bridge(hass, websocket=True)
    via_ws._ws_states = {**payload, "unrelated": 1}
    await via_ws.read_versions()

    assert isinstance(via_http._versions, NonNullDict) and isinstance(via_ws._versions, NonNullDict)
    assert dict(via_http._versions) == dict(via_ws._versions) == payload
