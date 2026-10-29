"""WebSocket connection: the paths of a login that succeeds and of the message loop afterwards.

The fake socket plays a script (see test_ws_login_failures.py for the failing logins). The handshake is
the current implementation, not an official protocol.
"""
import asyncio
import json
import logging
from types import SimpleNamespace

import aiohttp
import msgpack
import pytest

from custom_components.goecharger_api2.pygoecharger_ha import GoeChargerApiV2Bridge, TargetedEvent

from .factories import make_bridge
from .test_ws_login_failures import AUTH_OK, AUTH_REQUIRED, HELLO, FakeSession, FakeSocket, _text


class StreamSocket(FakeSocket):
    """Like FakeSocket, but `after` holds ready-made message objects."""

    def __aiter__(self):
        async def stream():
            for message in self._after:
                yield message
        return stream()


def _bridge(socket, password="secret", **kwargs):
    return GoeChargerApiV2Bridge(web_session=FakeSession(socket), intg_type="charger", host="192.0.2.10",
                                 access_password=password, **kwargs)


def _msg(kind, data):
    return SimpleNamespace(type=kind, data=data)


FULL = {"type": "fullStatus", "status": {"car": 1, "amp": 6}}


async def _run(socket, **kwargs):
    bridge = _bridge(socket)
    await bridge.ws_connect(**kwargs)
    return bridge


# ----------------------------------------------------------------------------- the handshake

@pytest.mark.parametrize("hello, expected_secured", [
    ({**HELLO, "version": "60.4", "secured": True}, True),
    ({**HELLO, "version": "beta"}, False),
    ({k: v for k, v in HELLO.items() if k != "version"}, False),
])
async def test_hello_variants_are_accepted(hello, expected_secured):
    socket = StreamSocket([hello, AUTH_REQUIRED, AUTH_OK], after=[_text(FULL)])
    bridge = _bridge(socket)
    seen = {}
    original = bridge.extract_ws_message_data

    def spy(data):
        seen.update(secured=bridge._ws_secured, serial=bridge._ws_serial, info=dict(bridge._ws_device_info))
        return original(data)

    bridge.extract_ws_message_data = spy
    await bridge.ws_connect()
    assert seen["secured"] is expected_secured and seen["serial"] == "123456" and "type" not in seen["info"]


@pytest.mark.parametrize("auth, device, expected_hash", [
    ({"type": "authRequired", "token1": "a", "token2": "b", "hash": "bcrypt"}, "go-eCharger_V4", "bcrypt"),
    ({"type": "authRequired", "token1": "a", "token2": "b"}, "go-eCharger_V4", "pbkdf2"),
    ({"type": "authRequired", "token1": "a", "token2": "b"}, "go-eCharger_Phoenix", "bcrypt"),
    ({"type": "authRequired", "token1": "a", "token2": "b"}, "go-eCharger_Core", "bcrypt"),
    ({"type": "authRequired", "token1": "a", "token2": "b", "hash": "PBKDF2"}, "go-eCharger_Phoenix", "pbkdf2"),
])
async def test_hash_type_is_taken_from_the_device_or_chosen_by_its_generation(auth, device, expected_hash):
    socket = StreamSocket([{**HELLO, "devicetype": device}, auth, AUTH_OK], after=[])
    bridge = _bridge(socket)
    used = []
    original = bridge._ws_compute_hashed_password
    bridge._ws_compute_hashed_password = lambda hash_type, pwd, serial: (used.append(hash_type), original(hash_type, pwd, serial))[1]
    await bridge.ws_connect()
    assert used == [expected_hash]


async def test_cloud_connection_sends_the_token_and_uses_the_cloud_address():
    captured = {}
    socket = StreamSocket([HELLO, AUTH_REQUIRED, AUTH_OK], after=[])

    class Session(FakeSession):
        def ws_connect(self, **kwargs):
            captured.update(kwargs)
            return super().ws_connect(**kwargs)

    bridge = GoeChargerApiV2Bridge(web_session=Session(socket), intg_type="charger", serial="123456",
                                   token="tok", access_password="secret")
    await bridge.ws_connect()
    assert captured["url"] == "wss://app.v3.go-e.io/123456" and captured["headers"] == {"Authorization": "Bearer tok"}


async def test_local_connection_sends_no_headers():
    captured = {}
    socket = StreamSocket([HELLO, AUTH_REQUIRED, AUTH_OK], after=[])

    class Session(FakeSession):
        def ws_connect(self, **kwargs):
            captured.update(kwargs)
            return super().ws_connect(**kwargs)

    bridge = GoeChargerApiV2Bridge(web_session=Session(socket), intg_type="charger", host="https://wallbox.local",
                                   access_password="secret")
    await bridge.ws_connect()
    assert captured["url"] == "wss://wallbox.local/ws" and captured["headers"] is None


# ----------------------------------------------------------------------------- the message loop

async def test_text_and_binary_messages_both_update_the_states():
    after = [_msg(aiohttp.WSMsgType.TEXT, json.dumps(FULL)),
             _msg(aiohttp.WSMsgType.BINARY, b"\x00" + msgpack.packb({"type": "deltaStatus", "status": {"amp": 10}}))]
    bridge = _bridge(StreamSocket([HELLO, AUTH_REQUIRED, AUTH_OK], after=after))
    states = {}
    original = bridge.extract_ws_message_data
    bridge.extract_ws_message_data = lambda d: (states.update(bridge._ws_states), original(d))[1]
    await bridge.ws_connect(keep_ws_states_after_close=True)
    assert bridge._ws_states == {"car": 1, "amp": 10} and bridge.ws_connected is True


async def test_new_data_marks_the_time_and_notifies_the_coordinator():
    bridge = _bridge(StreamSocket([HELLO, AUTH_REQUIRED, AUTH_OK], after=[_text(FULL)]))
    notified = []
    bridge._ws_notify_for_new_data = lambda: notified.append(bridge._ws_LAST_UPDATE)
    await bridge.ws_connect()
    assert len(notified) == 1 and notified[0] > 0


async def test_broken_binary_message_is_logged_and_the_loop_continues(caplog):
    after = [_msg(aiohttp.WSMsgType.BINARY, b"\xc1\xc1"), _text(FULL)]
    bridge = _bridge(StreamSocket([HELLO, AUTH_REQUIRED, AUTH_OK], after=after))
    notified = []
    bridge._ws_notify_for_new_data = lambda: notified.append(1)
    with caplog.at_level(logging.WARNING):
        await bridge.ws_connect()
    assert "Error processing BINARY message" in caplog.text and notified == [1]


async def test_broken_text_message_is_logged_and_the_loop_continues(caplog):
    after = [_msg(aiohttp.WSMsgType.TEXT, "{not json"), _text(FULL)]
    bridge = _bridge(StreamSocket([HELLO, AUTH_REQUIRED, AUTH_OK], after=after))
    notified = []
    bridge._ws_notify_for_new_data = lambda: notified.append(1)
    with caplog.at_level(logging.WARNING):
        await bridge.ws_connect()
    assert "Error processing TEXT message" in caplog.text and notified == [1]


@pytest.mark.parametrize("kind", [aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR])
async def test_close_or_error_message_ends_the_loop(kind):
    after = [_msg(kind, None), _text(FULL)]  # the message after the close must never be read
    bridge = _bridge(StreamSocket([HELLO, AUTH_REQUIRED, AUTH_OK], after=after))
    bridge._ws_notify_for_new_data = lambda: pytest.fail("data after close was processed")
    await bridge.ws_connect()
    assert bridge.ws_connected is False


async def test_unknown_message_type_is_logged_and_ignored(caplog):
    bridge = _bridge(StreamSocket([HELLO, AUTH_REQUIRED, AUTH_OK], after=[_msg(aiohttp.WSMsgType.PING, b"")]))
    with caplog.at_level(logging.WARNING):
        await bridge.ws_connect()
    assert "Unknown message type" in caplog.text


async def test_start_event_is_set_once_all_required_keys_have_arrived():
    keys = TargetedEvent(is_charger=True).tag_keys
    first = {"type": "fullStatus", "partial": True, "status": {keys[0]: 1}}
    rest = {"type": "deltaStatus", "status": {k: 1 for k in keys}}
    event = TargetedEvent(is_charger=True)
    bridge = _bridge(StreamSocket([HELLO, AUTH_REQUIRED, AUTH_OK], after=[_text(first), _text(rest)]))
    await bridge.ws_connect(a_event=event)
    assert event.is_set() and not event.has_errors()


# ----------------------------------------------------------------------------- how a connection ends

async def test_connection_end_clears_the_states_by_default():
    bridge = await _run(StreamSocket([HELLO, AUTH_REQUIRED, AUTH_OK], after=[_text(FULL)]))
    assert bridge._ws_states == {} and bridge.ws_connected is False and bridge._ws_connection is None


async def test_connection_end_can_keep_the_states_for_the_setup_check():
    bridge = await _run(StreamSocket([HELLO, AUTH_REQUIRED, AUTH_OK], after=[_text(FULL)]), keep_ws_states_after_close=True)
    assert bridge._ws_states == {"car": 1, "amp": 6} and bridge.ws_connected is True


@pytest.mark.parametrize("error", [asyncio.TimeoutError(), asyncio.CancelledError()])
async def test_timeout_and_cancel_are_reported_to_the_waiting_start(error):
    bridge = GoeChargerApiV2Bridge(web_session=FakeSession(error=error), intg_type="charger", host="192.0.2.10",
                                   access_password="secret")
    event = TargetedEvent(is_charger=True)
    await bridge.ws_connect(a_event=event)
    assert event.has_errors() and bridge.ws_connected is False


async def test_errors_without_a_waiting_event_do_not_raise():
    bridge = GoeChargerApiV2Bridge(web_session=FakeSession(error=aiohttp.ClientConnectionError("x")),
                                   intg_type="charger", host="192.0.2.10", access_password="secret")
    assert await bridge.ws_connect() is None


# ----------------------------------------------------------------------------- building the addresses

@pytest.mark.parametrize("host, password, expected_http, expected_ws", [
    ("wallbox.local", None, "http://wallbox.local", None),
    ("wallbox.local", "  ", "http://wallbox.local", None),
    ("wallbox.local", " secret ", "http://wallbox.local", "ws://wallbox.local/ws"),
    ("http://wallbox.local", "secret", "http://wallbox.local", "ws://wallbox.local/ws"),
    ("https://wallbox.local", "secret", "https://wallbox.local", "wss://wallbox.local/ws"),
])
async def test_local_addresses(host, password, expected_http, expected_ws):
    bridge = GoeChargerApiV2Bridge(web_session=None, intg_type="charger", host=host, access_password=password)
    assert bridge.host_url == expected_http and bridge.ws_url == expected_ws
    if password and password.strip():
        assert bridge.access_password == "secret"


@pytest.mark.parametrize("password, expected_ws", [(None, None), ("secret", "wss://app.v3.go-e.io/1234")])
async def test_cloud_addresses(password, expected_ws):
    bridge = GoeChargerApiV2Bridge(web_session=None, intg_type="charger", serial="1234", token="tok",
                                   access_password=password)
    assert bridge.host_url == "https://001234.api.v3.go-e.io" and bridge.token == "Bearer tok"
    assert bridge.ws_url == expected_ws


async def test_a_serial_without_a_token_is_not_enough():
    with pytest.raises(ValueError):
        GoeChargerApiV2Bridge(web_session=None, intg_type="charger", serial="1234")


@pytest.mark.parametrize("language, expected", [("de", "de"), ("xx", "en")])
async def test_bridge_texts_follow_the_language_with_english_fallback(language, expected):
    from custom_components.goecharger_api2.pygoecharger_ha.const import TRANSLATIONS
    bridge = GoeChargerApiV2Bridge(web_session=None, intg_type="charger", host="h", lang=language)
    assert bridge.lang_map is TRANSLATIONS[expected]


async def test_normalizing_unreadable_bytes_gives_hex_and_keeps_other_types():
    bridge = make_bridge_no_hass()
    assert bridge._ws_normalize_value(b"\xff\xfe") == "fffe"
    assert bridge._ws_normalize_value((b"a", 1)) == ("a", 1)
    assert bridge._ws_normalize_value(3.5) == 3.5
    assert bridge._ws_normalize_dict({1: b"x"}) == {"1": "x"}


def make_bridge_no_hass():
    return GoeChargerApiV2Bridge(web_session=None, intg_type="charger", host="h")
