"""Bridge, WebSocket path: message handling, password hashing and message signing.

The WebSocket protocol is not part of the official go-e documentation. These tests pin the behaviour
of the current implementation so that refactorings do not change it unnoticed; they are not a
statement about what the charger firmware really does.
"""
import hashlib
import hmac
import json
import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock

import bcrypt
import msgpack
import pytest

from custom_components.goecharger_api2.pygoecharger_ha import (
    GoeChargerApiV2Bridge,
    TargetedEvent,
    bcryptjs_base64_encode_serial,
)
from custom_components.goecharger_api2.pygoecharger_ha.const import API_KEYS_TO_IGNORE_FROM_WS

BCRYPT_ALPHABET = set("./ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")


@pytest.fixture
def bridge():
    return GoeChargerApiV2Bridge(web_session=None, intg_type="charger", host="192.0.2.10",
                                 access_password="secret")


# ----------------------------------------------------------------------------- incoming messages

def test_full_status_replaces_all_states(bridge):
    bridge._ws_states = {"a": 1}
    assert bridge.extract_ws_message_data({"type": "fullStatus", "status": {"a": 2, "b": 3}}) is True
    assert bridge._ws_states == {"a": 2, "b": 3}


def test_full_status_keeps_keys_that_are_missing_in_the_message(bridge):
    bridge._ws_states = {"a": 1, "z": 9}
    bridge.extract_ws_message_data({"type": "fullStatus", "status": {"a": 2}})
    assert bridge._ws_states == {"a": 2, "z": 9}


def test_partial_full_status_is_merged(bridge):
    bridge._ws_states = {"a": 1}
    bridge.extract_ws_message_data({"type": "fullStatus", "partial": True, "status": {"b": 3}})
    assert bridge._ws_states == {"a": 1, "b": 3}


def test_delta_status_updates_values(bridge):
    bridge._ws_states = {"a": 1}
    assert bridge.extract_ws_message_data({"type": "deltaStatus", "status": {"a": 5}}) is True
    assert bridge._ws_states == {"a": 5}


def test_delta_status_ignores_configured_keys(bridge):
    ignored = API_KEYS_TO_IGNORE_FROM_WS[0]
    assert bridge.extract_ws_message_data({"type": "deltaStatus", "status": {ignored: 1}}) is False
    assert ignored not in bridge._ws_states


def test_successful_response_updates_states(bridge):
    assert bridge.extract_ws_message_data(
        {"type": "response", "success": True, "requestId": 1, "status": {"frc": 1}}) is True
    assert bridge._ws_states == {"frc": 1}


def test_failed_response_is_logged_and_changes_nothing(bridge, caplog):
    bridge._ws_request_storage.set("7", {"key": "amp", "value": 99})
    with caplog.at_level(logging.WARNING):
        result = bridge.extract_ws_message_data(
            {"type": "response", "success": False, "requestId": "7", "message": "denied"})
    assert result is False
    assert bridge._ws_states == {}
    assert "Command failed" in caplog.text and "amp" in caplog.text


@pytest.mark.parametrize("message", [
    {"type": "hello"},
    {"type": "fullStatus", "status": {}},
    {"type": "deltaStatus"},
    {},
])
def test_other_messages_report_no_new_data(bridge, message):
    assert bridge.extract_ws_message_data(message) is False


def test_decode_accepts_json_text_and_msgpack_with_or_without_prefix(bridge):
    payload = {"type": "hello", "serial": "123456"}
    assert bridge._ws_decode_message(json.dumps(payload)) == payload
    assert bridge._ws_decode_message(msgpack.packb(payload)) == payload
    assert bridge._ws_decode_message(b"\x00" + msgpack.packb(payload)) == payload


def test_normalize_turns_bytes_into_strings(bridge):
    assert bridge._ws_normalize_dict({b"serial": b"123456", "list": [b"a", {b"k": b"v"}]}) == \
        {"serial": "123456", "list": ["a", {"k": "v"}]}


# ----------------------------------------------------------------------------- password hashing

def test_pbkdf2_hash_is_32_bytes_and_follows_the_documented_steps(bridge):
    expected = hashlib.pbkdf2_hmac("sha512", b"secret", b"123456", 100000, 256)
    import base64
    result = bridge._ws_compute_hashed_password("pbkdf2", "secret", "123456")
    assert len(result) == 32
    assert result == base64.b64encode(expected)[:32]


def test_bcrypt_hash_is_deterministic_and_verifiable(bridge):
    first = bridge._ws_compute_hashed_password("bcrypt", "secret", "123456")
    second = bridge._ws_compute_hashed_password("bcrypt", "secret", "123456")
    assert first == second and len(first) == 31
    salt = f"$2a$08${bcryptjs_base64_encode_serial('123456', 16)}"
    assert bcrypt.hashpw(hashlib.sha256(b"secret").hexdigest().encode(), salt.encode()).endswith(first)


def test_unknown_hash_type_returns_none(bridge):
    assert bridge._ws_compute_hashed_password("md5", "secret", "123456") is None


def test_bcrypt_salt_encoding_has_22_valid_characters():
    encoded = bcryptjs_base64_encode_serial("123456", 16)
    assert len(encoded) == 22 and set(encoded) <= BCRYPT_ALPHABET


def test_bcrypt_salt_encoding_rejects_non_numeric_serial():
    with pytest.raises(ValueError):
        bcryptjs_base64_encode_serial("12AB56", 16)


def test_auth_hash_follows_challenge_response_formula(bridge):
    hashed = b"hashed-password"
    inner = hashlib.sha256(b"token1" + hashed).hexdigest()
    expected = hashlib.sha256(("token3" + "token2" + inner).encode()).hexdigest()
    assert bridge._ws_compute_auth_hash("token1", "token2", "token3", hashed) == expected


# ----------------------------------------------------------------------------- outgoing commands

async def test_plain_command_has_documented_shape(bridge):
    bridge._ws_connection = SimpleNamespace(send_json=AsyncMock())
    await bridge._ws_send_command("amp", 10)
    first = bridge._ws_connection.send_json.await_args.args[0]
    assert first == {"type": "setValue", "requestId": 1, "key": "amp", "value": 10}
    await bridge._ws_send_command("frc", 1)
    assert bridge._ws_connection.send_json.await_args.args[0]["requestId"] == 2


async def test_secured_command_is_signed_with_hmac_sha256(bridge):
    bridge._ws_connection = SimpleNamespace(send_json=AsyncMock())
    bridge._ws_secured = True
    bridge._ws_hashed_password = b"hashed-password"
    await bridge._ws_send_command("frc", 1)
    message = bridge._ws_connection.send_json.await_args.args[0]
    assert message["type"] == "securedMsg" and message["requestId"] == "1sm"
    assert json.loads(message["data"]) == {"type": "setValue", "requestId": 1, "key": "frc", "value": 1}
    assert message["hmac"] == hmac.new(b"hashed-password", message["data"].encode(), hashlib.sha256).hexdigest()


async def test_command_sets_flag_and_returns_requested_value_over_websocket(bridge):
    bridge.ws_connected = True
    bridge._ws_connection = SimpleNamespace(send_json=AsyncMock())
    bridge._ws_LAST_NEW_DATA_NOTIFY = 123.0
    assert await bridge.write_value_to_key("frc", 1) == {"frc": 1}
    assert bridge._ws_LAST_NEW_DATA_NOTIFY == 0


async def test_button_press_is_ignored_over_websocket(bridge):
    bridge.ws_connected = True
    bridge._ws_connection = SimpleNamespace(send_json=AsyncMock())
    assert await bridge.write_value_to_key("zfocore", "TRIGGER") == {"zfocore": "TRIGGER"}
    bridge._ws_connection.send_json.assert_not_awaited()


# ----------------------------------------------------------------------------- start condition

def test_targeted_event_waits_for_the_required_charger_keys():
    event = TargetedEvent(is_charger=True)
    assert "hai" not in event.tag_keys and "cll" not in event.tag_keys
    assert event.check_and_set({"typ": 1}) is False and not event.is_set()
    assert event.check_and_set({key: 1 for key in event.tag_keys}) is True and event.is_set()


def test_targeted_event_for_controller_needs_different_keys():
    charger, controller = TargetedEvent(is_charger=True), TargetedEvent(is_charger=False)
    assert set(charger.tag_keys) != set(controller.tag_keys)
    assert "fwv" in controller.tag_keys
