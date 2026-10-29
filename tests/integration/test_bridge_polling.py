"""Bridge, polling: the read cycle (hibernation, configuration refresh, versions) and the state housekeeping.

Behaviour is derived from the code and the README (hibernation mode). The HTTP layer is mocked; time
is controlled by setting the bridge's "last update" timestamps.
"""
import asyncio
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from custom_components.goecharger_api2.pygoecharger_ha import NonNullDict
from custom_components.goecharger_api2.pygoecharger_ha.const import (
    FILTER_CARDS_ID_CLASSIC,
    FILTER_CARDS_ID_FWV60,
    FILTER_CONTROLER_ALL_STATES,
    FILTER_CONTROLER_MIN_STATES,
    FILTER_IDS_ADDON,
    FILTER_MIN_STATES,
    FILTER_TIMES_ADDON,
)

from .factories import make_bridge, make_coordinator

STATUS = "http://192.0.2.10/api/status"
SLEEP = "custom_components.goecharger_api2.pygoecharger_ha.asyncio.sleep"


def _filters(aioclient_mock):
    return [dict(c[1].query).get("filter") for c in aioclient_mock.mock_calls]


# ----------------------------------------------------------------------------- states: hibernation

async def test_first_read_requests_all_states_and_stores_the_time(hass, aioclient_mock):
    aioclient_mock.get(STATUS, json={"car": 1, "amp": 6})
    bridge = make_bridge(hass)
    await bridge.read_all_states()
    assert bridge._states == {"car": 1, "amp": 6}
    assert bridge._LAST_FULL_STATE_UPDATE_TS > 0
    assert len(_filters(aioclient_mock)) == 1 and "alw" in _filters(aioclient_mock)[0]


async def test_idle_charger_reads_only_the_minimal_states(hass, aioclient_mock):
    aioclient_mock.get(STATUS, json={"car": 1, "nrg": [1]})
    bridge = make_bridge(hass)
    bridge._states = {"car": 1}
    bridge._LAST_FULL_STATE_UPDATE_TS = time.time()
    await bridge.read_all_states()
    expected = FILTER_MIN_STATES + FILTER_TIMES_ADDON
    assert _filters(aioclient_mock) == [expected]
    assert bridge._states["nrg"] == [1]


async def test_idle_charger_also_reads_pv_values_after_pv_data_was_sent(hass, aioclient_mock):
    aioclient_mock.get(STATUS, json={"car": 1})
    bridge = make_bridge(hass)
    bridge._states = {"car": 1}
    bridge._LAST_FULL_STATE_UPDATE_TS = time.time()
    bridge._REQUEST_IDS_DATA = True
    await bridge.read_all_states()
    assert _filters(aioclient_mock) == [FILTER_MIN_STATES + FILTER_IDS_ADDON + FILTER_TIMES_ADDON]
    assert bridge._REQUEST_IDS_DATA is False


async def test_idle_charger_reads_everything_after_five_minutes(hass, aioclient_mock):
    aioclient_mock.get(STATUS, json={"car": 1, "amp": 6})
    bridge = make_bridge(hass)
    bridge._states = {"car": 1}
    bridge._LAST_FULL_STATE_UPDATE_TS = time.time() - 301
    await bridge.read_all_states()
    assert "alw" in _filters(aioclient_mock)[0]


async def test_charger_that_starts_charging_triggers_a_full_read(hass, aioclient_mock):
    aioclient_mock.get(STATUS, json={"car": 2, "amp": 6})
    bridge = make_bridge(hass)
    bridge._states = {"car": 1}
    bridge._LAST_FULL_STATE_UPDATE_TS = time.time()
    await bridge.read_all_states()
    filters = _filters(aioclient_mock)
    assert len(filters) == 2 and filters[0].startswith("car,modelStatus") and "alw" in filters[1]


async def test_charger_that_is_not_idle_reads_everything_every_time(hass, aioclient_mock):
    aioclient_mock.get(STATUS, json={"car": 2})
    bridge = make_bridge(hass)
    bridge._states = {"car": 2}
    bridge._LAST_FULL_STATE_UPDATE_TS = time.time()
    await bridge.read_all_states()
    assert "alw" in _filters(aioclient_mock)[0]


async def test_empty_minimal_answer_changes_nothing(hass, aioclient_mock):
    aioclient_mock.get(STATUS, status=404)
    bridge = make_bridge(hass)
    bridge._states = {"car": 1, "nrg": [5]}
    bridge._LAST_FULL_STATE_UPDATE_TS = time.time()
    await bridge.read_all_states()
    assert bridge._states == {"car": 1, "nrg": [5]}


async def test_failed_full_read_keeps_the_previous_states(hass, aioclient_mock):
    """Characterisation (arc42 R20): an empty answer does not clear the old values, and the 'last full
    update' time is renewed although nothing was read."""
    aioclient_mock.get(STATUS, status=403)
    bridge = make_bridge(hass)
    bridge._states = {"car": 2, "amp": 6}
    await bridge.read_all_states()
    assert bridge._states == {"car": 2, "amp": 6}
    assert bridge._LAST_FULL_STATE_UPDATE_TS > 0


async def test_controller_reads_minimal_states_within_five_minutes(hass, aioclient_mock):
    aioclient_mock.get(STATUS, json={"usv": [1]})
    bridge = make_bridge(hass, intg_type="controller")
    bridge._LAST_FULL_STATE_UPDATE_TS = time.time()
    await bridge.read_all_states()
    assert _filters(aioclient_mock)[0].startswith(FILTER_CONTROLER_MIN_STATES)


async def test_controller_reads_everything_after_five_minutes(hass, aioclient_mock):
    aioclient_mock.get(STATUS, json={"usv": [1]})
    bridge = make_bridge(hass, intg_type="controller")
    await bridge.read_all_states()
    assert _filters(aioclient_mock) == [FILTER_CONTROLER_ALL_STATES]


async def test_websocket_connection_reads_states_from_memory_not_from_http(hass, aioclient_mock):
    bridge = make_bridge(hass, websocket=True)
    bridge._ws_states = {"car": 2, "alw": True, "amp": 16, "zzz": 1}
    await bridge.read_all_states()
    assert aioclient_mock.call_count == 0
    assert bridge._states == {"car": 2, "alw": True}  # amp is configuration, zzz is not requested


async def test_websocket_idle_charger_uses_the_minimal_filter_from_memory(hass, aioclient_mock):
    bridge = make_bridge(hass, websocket=True)
    bridge._ws_states = {"car": 1, "nrg": [1], "amp": 6}
    bridge._states = {"car": 1}
    bridge._LAST_FULL_STATE_UPDATE_TS = time.time()
    await bridge.read_all_states()
    assert aioclient_mock.call_count == 0
    assert bridge._states == {"car": 1, "nrg": [1]}


# ----------------------------------------------------------------------------- configuration

async def test_config_read_stores_values_and_time(hass, aioclient_mock):
    aioclient_mock.get(STATUS, json={"amp": 10, "frc": 0})
    bridge = make_bridge(hass)
    await bridge.read_all_config()
    assert bridge._config == {"amp": 10, "frc": 0} and bridge._LAST_CONFIG_UPDATE_TS > 0


async def test_failed_config_read_waits_five_minutes_before_the_next_try(hass, aioclient_mock):
    aioclient_mock.get(STATUS, status=500)
    bridge = make_bridge(hass)
    before = time.time()
    await bridge.read_all_config()
    # next regular refresh (one hour after the stored time) is due in about 300 seconds
    assert before + 280 < bridge._LAST_CONFIG_UPDATE_TS + 3600 < before + 320


async def test_config_read_replaces_websocket_values_that_differ(hass, aioclient_mock):
    aioclient_mock.get(STATUS, json={"frc": 1, "amp": 10})
    bridge = make_bridge(hass)
    bridge._ws_states = {"frc": 0, "amp": 10, "car": 1}
    await bridge.read_all_config()
    assert "frc" not in bridge._ws_states and bridge._ws_states["amp"] == 10 and bridge._ws_states["car"] == 1


async def test_config_read_over_websocket_uses_memory(hass, aioclient_mock):
    bridge = make_bridge(hass, websocket=True)
    bridge._ws_states = {"amp": 16, "unrelated": 1}
    await bridge.read_all_config()
    assert aioclient_mock.call_count == 0 and bridge._config == {"amp": 16}


async def test_config_read_without_filter_does_nothing(hass, aioclient_mock):
    bridge = make_bridge(hass)
    bridge._FILTER_ALL_CONFIG = ""
    await bridge.read_all_config()
    assert aioclient_mock.call_count == 0 and bridge._LAST_CONFIG_UPDATE_TS == 0


async def test_force_config_update_resets_the_timers_and_reads_again(hass, aioclient_mock):
    aioclient_mock.get(STATUS, json={"amp": 10})
    bridge = make_bridge(hass)
    bridge._LAST_FULL_STATE_UPDATE_TS = 123.0
    await bridge.force_config_update()
    assert bridge._LAST_FULL_STATE_UPDATE_TS == 0 and bridge._config == {"amp": 10}


async def test_force_config_update_over_websocket_still_works(hass, aioclient_mock):
    bridge = make_bridge(hass, websocket=True)
    bridge._ws_states = {"amp": 16}
    await bridge.force_config_update()
    assert bridge._config == {"amp": 16}


# ----------------------------------------------------------------------------- read_all

async def test_read_all_returns_a_merged_view_with_websocket_values_first(hass, aioclient_mock):
    aioclient_mock.get(STATUS, json={"car": 1, "amp": 6})
    bridge = make_bridge(hass)
    bridge._LAST_CONFIG_UPDATE_TS = time.time()
    bridge._ws_states = {"amp": 99}
    bridge._versions = {"fwv": "60.3"}
    merged = await bridge.read_all()
    assert merged["amp"] == 99 and merged["car"] == 1 and merged["fwv"] == "60.3"


async def test_read_all_reads_the_configuration_only_every_hour(hass, aioclient_mock):
    aioclient_mock.get(STATUS, json={"car": 1})
    bridge = make_bridge(hass)
    bridge._LAST_CONFIG_UPDATE_TS = time.time()
    await bridge.read_all()
    assert len(_filters(aioclient_mock)) == 1  # states only
    aioclient_mock.clear_requests()
    aioclient_mock.get(STATUS, json={"car": 1})
    bridge._LAST_CONFIG_UPDATE_TS = time.time() - 3601
    await bridge.read_all()
    assert len(_filters(aioclient_mock)) == 2  # states and configuration


async def test_read_all_over_websocket_returns_the_websocket_dictionary(hass, aioclient_mock):
    bridge = make_bridge(hass, websocket=True)
    bridge._ws_states = {"car": 1}
    bridge._LAST_CONFIG_UPDATE_TS = time.time()
    assert await bridge.read_all() is bridge._ws_states


# ----------------------------------------------------------------------------- versions and system

async def test_read_versions_over_websocket_uses_memory(hass, aioclient_mock):
    bridge = make_bridge(hass, websocket=True)
    bridge._ws_states = {"fwv": "60.3", "typ": "x", "cards": [{"cardId": 1}], "amp": 6}
    assert await bridge.read_versions() is True
    assert "amp" not in bridge._versions and bridge._versions["fwv"] == "60.3"
    assert aioclient_mock.call_count == 0


async def test_read_versions_without_any_data_fails(hass):
    bridge = make_bridge(hass, websocket=True)
    assert await bridge.read_versions() is False


async def test_read_versions_retries_until_data_arrives(hass):
    bridge = make_bridge(hass)
    bridge._read_filtered_data = AsyncMock(side_effect=[{}, NonNullDict({"fwv": "59.4", "cards": [1]})])
    with patch(SLEEP, AsyncMock()) as sleep:
        assert await bridge.read_versions() is True
    assert bridge._versions["fwv"] == "59.4" and bridge._read_filtered_data.await_count == 2 and sleep.await_count == 1


async def test_read_versions_gives_up_after_five_attempts(hass, aioclient_mock):
    aioclient_mock.get(STATUS, status=500)
    bridge = make_bridge(hass)
    with patch(SLEEP, AsyncMock()) as sleep:
        assert await bridge.read_versions() is False
    assert aioclient_mock.call_count == 5 and sleep.await_count == 4


async def test_firmware_with_cards_object_keeps_the_classic_card_filter(hass, aioclient_mock):
    aioclient_mock.get(STATUS, json={"fwv": "60.3", "cards": [{"cardId": 1}]})
    bridge = make_bridge(hass)
    await bridge.read_versions()
    assert FILTER_CARDS_ID_CLASSIC in bridge._FILTER_ALL_CONFIG and "c0i" not in bridge._FILTER_ALL_CONFIG


async def test_firmware_without_cards_object_switches_to_single_card_keys(hass, aioclient_mock):
    aioclient_mock.get(STATUS, json={"fwv": "60.0-beta"})
    bridge = make_bridge(hass)
    await bridge.read_versions()
    assert FILTER_CARDS_ID_FWV60 in bridge._FILTER_ALL_CONFIG


async def test_controller_versions_do_not_touch_the_card_filters(hass, aioclient_mock):
    aioclient_mock.get(STATUS, json={"fwv": "1.1.1"})
    bridge = make_bridge(hass, intg_type="controller")
    before = bridge._FILTER_ALL_CONFIG
    assert await bridge.read_versions() is True and bridge._FILTER_ALL_CONFIG == before


async def test_read_system_over_http_and_websocket(hass, aioclient_mock):
    aioclient_mock.get(STATUS, json={"sse": "123456", "typ": "x"})
    assert await make_bridge(hass).read_system() == {"sse": "123456", "typ": "x"}
    ws_bridge = make_bridge(hass, websocket=True)
    ws_bridge._ws_states = {"sse": "1", "other": 2}
    assert await ws_bridge.read_system() == {"sse": "1"}


# ----------------------------------------------------------------------------- read everything at once

async def test_read_all_data_returns_the_whole_status(hass, aioclient_mock):
    aioclient_mock.get(STATUS, json={"a": 1})
    assert await make_bridge(hass)._read_all_data() == {"a": 1}


@pytest.mark.parametrize("response", [dict(status=403), dict(status=404), dict(text="no json"), dict(json={})])
async def test_read_all_data_gives_nothing_for_errors(hass, aioclient_mock, response):
    aioclient_mock.get(STATUS, **response)
    assert await make_bridge(hass)._read_all_data() == {}


async def test_read_all_data_sends_the_cloud_token(hass, aioclient_mock):
    from homeassistant.helpers.aiohttp_client import async_get_clientsession
    from custom_components.goecharger_api2.pygoecharger_ha import GoeChargerApiV2Bridge
    aioclient_mock.get("https://001234.api.v3.go-e.io/api/status", json={"a": 1})
    bridge = GoeChargerApiV2Bridge(web_session=async_get_clientsession(hass), intg_type="charger",
                                   serial="1234", token="tok")
    await bridge._read_all_data()
    assert aioclient_mock.mock_calls[0][3] == {"Authorization": "Bearer tok"}


# ----------------------------------------------------------------------------- housekeeping

async def test_clear_data_resets_everything_and_cancels_the_pending_update(hass):
    bridge = make_bridge(hass)
    bridge._states, bridge._config, bridge._versions, bridge._ws_states = {"a": 1}, {"b": 2}, {"c": 3}, {"d": 4}
    bridge._LAST_CONFIG_UPDATE_TS = bridge._LAST_FULL_STATE_UPDATE_TS = 5
    task = asyncio.create_task(asyncio.sleep(3600))
    bridge._ws_debounced_update_task = task
    bridge.clear_data()
    await asyncio.sleep(0)
    assert task.cancelled()
    assert (bridge._states, bridge._config, bridge._versions, bridge._ws_states) == ({}, {}, {}, {})
    assert bridge._LAST_CONFIG_UPDATE_TS == 0 and bridge.available_fields() == 0


async def test_reset_timestamps_over_http_only_resets(hass):
    bridge = make_bridge(hass)
    bridge._LAST_CONFIG_UPDATE_TS = bridge._LAST_FULL_STATE_UPDATE_TS = 5
    await bridge.reset_stored_update_ts()
    assert bridge._LAST_CONFIG_UPDATE_TS == bridge._LAST_FULL_STATE_UPDATE_TS == 0


async def test_reset_timestamps_over_websocket_asks_the_coordinator_to_reconnect(hass):
    bridge = make_bridge(hass, websocket=True)
    bridge.coordinator = SimpleNamespace(force_async_update_now=AsyncMock())
    await bridge.reset_stored_update_ts()
    bridge.coordinator.force_async_update_now.assert_awaited_once()


async def test_reset_timestamps_over_websocket_without_coordinator_does_not_fail(hass):
    bridge = make_bridge(hass, websocket=True)
    await bridge.reset_stored_update_ts()


async def test_websocket_update_reaches_the_coordinator_after_the_debounce(hass):
    bridge = make_bridge(hass)
    bridge.coordinator = SimpleNamespace(_ws_data_update_notify_interval_in_seconds=1, async_set_updated_data=lambda d: received.append(d))
    received = []
    bridge._ws_states = {"a": 1}
    bridge._ws_LAST_NEW_DATA_NOTIFY = time.time()
    with patch(SLEEP, AsyncMock()):
        bridge._ws_notify_for_new_data()
        await bridge._ws_debounced_update_task
    assert received and received[0]["a"] == 1 and bridge._ws_LAST_NEW_DATA_NOTIFY > 0


async def test_websocket_update_without_wait_when_the_last_one_is_old(hass):
    bridge = make_bridge(hass)
    received = []
    bridge.coordinator = SimpleNamespace(_ws_data_update_notify_interval_in_seconds=1, async_set_updated_data=received.append)
    bridge._ws_LAST_NEW_DATA_NOTIFY = 0
    with patch(SLEEP, AsyncMock()) as sleep:
        bridge._ws_notify_for_new_data()
        await bridge._ws_debounced_update_task
    sleep.assert_not_awaited()
    assert len(received) == 1


async def test_a_second_websocket_update_cancels_the_first_pending_one(hass):
    bridge = make_bridge(hass)
    bridge.coordinator = SimpleNamespace(_ws_data_update_notify_interval_in_seconds=60, async_set_updated_data=lambda d: None)
    bridge._ws_LAST_NEW_DATA_NOTIFY = time.time()
    bridge._ws_notify_for_new_data()
    first = bridge._ws_debounced_update_task
    bridge._ws_notify_for_new_data()
    await asyncio.sleep(0)
    assert first.cancelled() and bridge._ws_debounced_update_task is not first
    bridge._ws_debounced_update_task.cancel()


async def test_websocket_silence_is_detected_after_fifty_seconds(hass):
    bridge = make_bridge(hass)
    bridge._ws_LAST_UPDATE = time.time() - 10
    assert bridge.ws_check_last_update() is True
    bridge._ws_LAST_UPDATE = time.time() - 60
    assert bridge.ws_check_last_update() is False


async def test_ws_close_handles_missing_and_failing_connections(hass):
    bridge = make_bridge(hass)
    bridge.ws_connected = True
    await bridge.ws_close(None)
    assert bridge.ws_connected is False
    failing = SimpleNamespace(close=AsyncMock(side_effect=RuntimeError("boom")))
    await bridge.ws_close(failing)
    bridge._ws_serial = "123456"
    ok = SimpleNamespace(close=AsyncMock())
    await bridge.ws_close(ok)
    ok.close.assert_awaited_once()


async def test_expiring_store_forgets_old_entries():
    from custom_components.goecharger_api2.pygoecharger_ha import ExpiringStore
    store = ExpiringStore(ttl=0)
    store.set("1", {"a": 1})
    time.sleep(0.01)
    assert store.get("1") is None and len(store) == 0
    store = ExpiringStore(ttl=60)
    store.set("1", {"a": 1})
    assert store.get("1") == {"a": 1} and store.get("2") is None and len(store) == 1
    store._store["1"]["expires_at"] = 0
    assert store.get("1") is None


async def test_nonnull_dict_returns_default_for_null(hass):
    data = NonNullDict({"a": None, "b": 1})
    assert data.none_null_get("a", 7) == 7 and data.none_null_get("b", 7) == 1 and data.none_null_get("c") is None
