"""WebSocket login: every way the handshake can fail must end cleanly.

"Cleanly" means: the waiting start code is told about the error (TargetedEvent), the connection is
reported as not connected, no data is kept and no command is sent. The handshake follows the
current implementation (hello -> auth required -> auth -> auth result); it is not officially documented.
A positive control (`test_successful_login_...`) makes sure the fake server really lets a valid login pass.
"""
import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import aiohttp
import pytest

from custom_components.goecharger_api2.pygoecharger_ha import GoeChargerApiV2Bridge, TargetedEvent

WAIT_FOR = "custom_components.goecharger_api2.pygoecharger_ha.asyncio.wait_for"
HELLO = {"type": "hello", "serial": "123456", "version": "59.4", "secured": False}
AUTH_REQUIRED = {"type": "authRequired", "token1": "t1", "token2": "t2", "hash": "pbkdf2"}
AUTH_OK = {"type": "authSuccess"}


def _text(payload):
    return SimpleNamespace(type=aiohttp.WSMsgType.TEXT, data=json.dumps(payload))


class FakeSocket:
    """Plays a script: the first receive() calls answer the handshake, `after` is streamed afterwards."""

    def __init__(self, handshake, after=()):
        self._handshake = list(handshake)
        self._after = list(after)
        self.send_json = AsyncMock()

    async def receive(self):
        item = self._handshake.pop(0)
        if item == "hang":
            await asyncio.sleep(3600)
        return _text(item)

    def __aiter__(self):
        async def stream():
            for payload in self._after:
                yield _text(payload)
        return stream()

    async def close(self):
        return None


class FakeSession:
    def __init__(self, socket=None, error=None):
        self._socket, self._error = socket, error

    def ws_connect(self, **kwargs):
        session = self

        class _Ctx:
            async def __aenter__(self):
                if session._error:
                    raise session._error
                return session._socket

            async def __aexit__(self, *exc):
                return False
        return _Ctx()


def _bridge(session, password="secret"):
    return GoeChargerApiV2Bridge(web_session=session, intg_type="charger", host="192.0.2.10",
                                 access_password=password)


async def _login(bridge):
    event = TargetedEvent(is_charger=True)
    result = await bridge.ws_connect(a_event=event)
    return event, result


def _assert_clean_failure(bridge, event, socket, message):
    assert event.is_set() and event.has_errors()
    assert message in str(event._error)
    assert bridge.ws_connected is False
    assert bridge._ws_states == {}
    if socket is not None:
        socket.send_json.assert_awaited_once()  # at most the auth answer, never a setValue command
        assert socket.send_json.await_args.args[0].get("type") != "setValue"


async def test_successful_login_reports_data_and_resets_state_afterwards():
    """Positive control for the fake server."""
    status = {"type": "fullStatus", "status": {key: 1 for key in TargetedEvent(is_charger=True).tag_keys}}
    socket = FakeSocket([HELLO, AUTH_REQUIRED, AUTH_OK], after=[status])
    bridge = _bridge(FakeSession(socket))
    event, _ = await _login(bridge)
    assert event.is_set() and not event.has_errors()
    assert socket.send_json.await_args.args[0]["type"] == "auth"
    assert bridge.ws_connected is False  # the stream ended, so the connection is closed again


async def test_no_password_means_no_websocket_url():
    bridge = _bridge(FakeSession(FakeSocket([])), password=None)
    event, _ = await _login(bridge)
    _assert_clean_failure(bridge, event, None, "WebSocket URL not configured")


async def test_hello_without_serial_fails():
    socket = FakeSocket([{"type": "hello"}])
    bridge = _bridge(FakeSession(socket))
    event, _ = await _login(bridge)
    assert event.has_errors() and "No serial" in str(event._error)
    assert bridge.ws_connected is False
    socket.send_json.assert_not_awaited()


async def test_device_reports_offline():
    socket = FakeSocket([HELLO, {"type": "offline"}])
    bridge = _bridge(FakeSession(socket))
    event, _ = await _login(bridge)
    assert event.has_errors() and "offline" in str(event._error)
    assert bridge.ws_connected is False
    socket.send_json.assert_not_awaited()


async def test_unsupported_hash_type_fails():
    socket = FakeSocket([HELLO, {**AUTH_REQUIRED, "hash": "rot13"}])
    bridge = _bridge(FakeSession(socket))
    event, _ = await _login(bridge)
    assert event.has_errors() and "Unsupported authentication hash type" in str(event._error)
    socket.send_json.assert_not_awaited()


@pytest.mark.parametrize("missing", ["token1", "token2"])
async def test_missing_challenge_token_fails(missing):
    challenge = {k: v for k, v in AUTH_REQUIRED.items() if k != missing}
    socket = FakeSocket([HELLO, challenge])
    bridge = _bridge(FakeSession(socket))
    event, _ = await _login(bridge)
    assert event.has_errors() and "Missing authentication tokens" in str(event._error)
    socket.send_json.assert_not_awaited()


@pytest.mark.parametrize("answer", [
    {"type": "authError", "message": "wrong password"},
    {"type": "response", "success": False},
])
async def test_wrong_password_fails(answer):
    socket = FakeSocket([HELLO, AUTH_REQUIRED, answer])
    bridge = _bridge(FakeSession(socket))
    event, _ = await _login(bridge)
    _assert_clean_failure(bridge, event, socket, "Authentication failed")


async def test_no_answer_to_the_auth_message_times_out():
    socket = FakeSocket([HELLO, AUTH_REQUIRED, "hang"])
    bridge = _bridge(FakeSession(socket))
    real_wait_for = asyncio.wait_for
    with patch(WAIT_FOR, lambda coro, timeout: real_wait_for(coro, 0.01)):
        event, _ = await _login(bridge)
    _assert_clean_failure(bridge, event, socket, "Authentication TIMEOUT")


async def test_unreachable_device_reports_the_connection_error():
    error = aiohttp.ClientConnectionError("no route to host")
    bridge = _bridge(FakeSession(error=error))
    event, _ = await _login(bridge)
    assert event.has_errors() and event._error is error
    assert bridge.ws_connected is False and bridge._ws_states == {}


async def test_unexpected_error_during_handshake_is_reported_not_raised():
    error = RuntimeError("boom")
    bridge = _bridge(FakeSession(error=error))
    event, result = await _login(bridge)
    assert result is None and event._error is error
    assert bridge.ws_connected is False


async def test_connection_that_drops_after_login_resets_the_state():
    socket = FakeSocket([HELLO, AUTH_REQUIRED, AUTH_OK],
                        after=[{"type": "fullStatus", "status": {"car": 1}}])
    bridge = _bridge(FakeSession(socket))
    await bridge.ws_connect()
    assert bridge.ws_connected is False
    assert bridge._ws_states == {} and bridge._ws_connection is None
