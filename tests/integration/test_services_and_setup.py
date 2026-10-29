"""Services (PV data, stop charging, charger lookup) and the start and end of a config entry.

Setup and unload run the real functions of the integration; only the platform loading, the data
polling and the WebSocket start are replaced.
"""
import inspect
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryDisabler
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import CoreState
from homeassistant.exceptions import ServiceValidationError

from custom_components.goecharger_api2 import (
    ACTIVE_CHARGER_COUNTER,
    GoeChargerDataUpdateCoordinator,
    async_migrate_entry,
    async_setup,
    async_setup_entry,
    async_unload_entry,
    entry_update_listener,
)
from custom_components.goecharger_api2 import service as service_module
from custom_components.goecharger_api2.const import DOMAIN, SERVICE_SET_PV_DATA, SERVICE_STOP_CHARGING
from custom_components.goecharger_api2.service import GoeChargerApiV2Service, add_config_entry_to_service
from custom_components.goecharger_api2.pygoecharger_ha import NonNullDict
from custom_components.goecharger_api2.pygoecharger_ha.keys import Tag

from .factories import make_coordinator, make_entry

PKG = "custom_components.goecharger_api2"


@pytest.fixture(autouse=True)
def clean_registry():
    service_module._COORDINATOR_PER_CONFIG_ENTRY_ID_MAP = {}
    yield
    service_module._COORDINATOR_PER_CONFIG_ENTRY_ID_MAP = {}


def _call(return_response=True, **data):
    return MagicMock(data=data, return_response=return_response)


def _service(hass, mode="lan", car=2, **kwargs):
    coordinator = make_coordinator(hass, data={Tag.CAR_CONNECTED.key: car}, mode=mode, **kwargs)
    coordinator.async_write_key = AsyncMock(return_value={Tag.IDS.key: True})
    return GoeChargerApiV2Service(hass, coordinator._config_entry, coordinator), coordinator


# ----------------------------------------------------------------------------- set_pv_data

async def test_cloud_charger_without_a_car_gets_no_pv_data(hass):
    service, coordinator = _service(hass, mode="wan", car=1)
    result = await service.set_pv_data(_call(pgrid=-500))
    assert "No CAR CONNECTED" in result["error"]
    coordinator.async_write_key.assert_not_awaited()


async def test_cloud_charger_without_a_car_returns_nothing_when_no_answer_is_wanted(hass):
    service, coordinator = _service(hass, mode="wan", car=0)
    assert await service.set_pv_data(_call(return_response=False, pgrid=-500)) is None
    coordinator.async_write_key.assert_not_awaited()


async def test_cloud_charger_with_a_car_gets_pv_data(hass):
    service, coordinator = _service(hass, mode="wan", car=2)
    result = await service.set_pv_data(_call(pgrid=-500))
    assert result["success"] == "true"
    coordinator.async_write_key.assert_awaited_once()


async def test_cloud_charger_with_unreadable_car_state_still_gets_pv_data(hass):
    service, coordinator = _service(hass, mode="wan", car="n/a")
    await service.set_pv_data(_call(pgrid=0))
    coordinator.async_write_key.assert_awaited_once()


async def test_cloud_charger_without_car_information_gets_no_pv_data(hass):
    coordinator = make_coordinator(hass, data={}, mode="wan")
    coordinator.async_write_key = AsyncMock()
    service = GoeChargerApiV2Service(hass, coordinator._config_entry, coordinator)
    result = await service.set_pv_data(_call(pgrid=0))
    assert "error" in result and coordinator.async_write_key.await_count == 0


async def test_missing_grid_power_is_an_error(hass):
    service, coordinator = _service(hass)
    result = await service.set_pv_data(_call(ppv=100))
    assert "No Grid Power" in result["error"]
    coordinator.async_write_key.assert_not_awaited()


async def test_missing_grid_power_without_wanted_answer_returns_nothing(hass):
    service, _ = _service(hass)
    assert await service.set_pv_data(_call(return_response=False, ppv=100)) is None


async def test_successful_pv_data_returns_nothing_when_no_answer_is_wanted(hass):
    service, coordinator = _service(hass)
    assert await service.set_pv_data(_call(return_response=False, pgrid=-1, ppv=2, pakku=3)) is None
    coordinator.async_write_key.assert_awaited_once_with(Tag.IDS.key, {"pGrid": -1.0, "pPv": 2.0, "pAkku": 3.0})


@pytest.mark.parametrize("error", [ValueError("down"), TypeError("odd")])
@pytest.mark.parametrize("wanted", [True, False])
async def test_failed_pv_write_is_reported_not_raised(hass, error, wanted):
    service, coordinator = _service(hass)
    coordinator.async_write_key.side_effect = error
    result = await service.set_pv_data(_call(return_response=wanted, pgrid=0))
    assert (result is None) if not wanted else ("error" in result and str(error) in result["error"])


# ----------------------------------------------------------------------------- stop_charging

async def test_stop_charging_reports_when_the_lock_was_not_confirmed(hass):
    service, coordinator = _service(hass)
    coordinator.async_write_key.return_value = {}
    result = await service.stop_charging(_call())
    assert "could not be send" in result["error"] and service._stop_in_progress is False


async def test_stop_charging_without_wanted_answer_returns_nothing(hass):
    service, coordinator = _service(hass)
    coordinator.async_write_key.return_value = {}
    assert await service.stop_charging(_call(return_response=False)) is None


async def test_stop_charging_locks_waits_and_unlocks(hass):
    service, coordinator = _service(hass)
    coordinator.async_write_key.side_effect = [{Tag.FRC.key: 1}, {Tag.FRC.key: 0}]
    with patch(f"{PKG}.service.asyncio.sleep", AsyncMock()) as sleep:
        result = await service.stop_charging(_call())
    sleep.assert_awaited_once_with(300)
    assert result["success"] == "true"
    assert [c.args for c in coordinator.async_write_key.await_args_list] == [(Tag.FRC.key, 1), (Tag.FRC.key, 0)]


async def test_stop_charging_without_wanted_answer_still_unlocks(hass):
    service, coordinator = _service(hass)
    coordinator.async_write_key.side_effect = [{Tag.FRC.key: 1}, {Tag.FRC.key: 0}]
    with patch(f"{PKG}.service.asyncio.sleep", AsyncMock()):
        assert await service.stop_charging(_call(return_response=False)) is None
    assert coordinator.async_write_key.await_count == 2


async def test_second_stop_request_is_refused_while_one_runs(hass):
    service, _ = _service(hass)
    service._stop_in_progress = True
    assert "already in progress" in (await service.stop_charging(_call()))["error"]
    assert await service.stop_charging(_call(return_response=False)) is None


@pytest.mark.parametrize("wanted", [True, False])
async def test_stop_charging_reports_write_errors(hass, wanted):
    service, coordinator = _service(hass)
    coordinator.async_write_key.side_effect = ValueError("down")
    result = await service.stop_charging(_call(return_response=wanted))
    assert (result is None) if not wanted else ("down" in result["error"])


# ----------------------------------------------------------------------------- choosing the charger

async def test_without_configid_the_first_registered_charger_is_used(hass):
    service, coordinator = _service(hass)
    assert service.get_coordinator(_call())[1] is coordinator


# since 4702213 a call without configid is only answered when exactly one charger is registered
REFUSES_GUESSING = "zero (or multiple)" in inspect.getsource(GoeChargerApiV2Service.get_coordinator)


async def test_with_an_empty_registry_no_charger_can_be_chosen(hass):
    service, _ = _service(hass)
    service_module._COORDINATOR_PER_CONFIG_ENTRY_ID_MAP.clear()
    expected = ServiceValidationError if REFUSES_GUESSING else (StopIteration, RuntimeError)
    with pytest.raises(expected):
        service.get_coordinator(_call())


@pytest.mark.skipif(not REFUSES_GUESSING, reason="this version still picks the first registered charger")
async def test_without_configid_and_with_two_chargers_no_charger_is_guessed(hass):
    service, _ = _service(hass)
    other = make_coordinator(hass, serial="222222")
    add_config_entry_to_service(other._config_entry, other)
    with pytest.raises(ServiceValidationError, match="zero \\(or multiple\\)"):
        service.get_coordinator(_call())


async def test_configid_of_a_registered_enabled_charger_is_accepted(hass):
    service, coordinator = _service(hass)
    config_id = coordinator._config_entry.entry_id
    assert service.get_coordinator(_call(configid=config_id)) == (config_id, coordinator)


async def test_unknown_configid_is_refused(hass):
    service, _ = _service(hass)
    with pytest.raises(ServiceValidationError, match="disabled or invalid"):
        service.get_coordinator(_call(configid="does-not-exist"))


async def test_configid_of_a_disabled_entry_is_refused(hass):
    service, coordinator = _service(hass)
    entry = coordinator._config_entry
    await hass.config_entries.async_set_disabled_by(entry.entry_id, ConfigEntryDisabler.USER)
    with pytest.raises(ServiceValidationError, match="disabled or invalid"):
        service.get_coordinator(_call(configid=entry.entry_id))


async def test_configid_of_an_entry_missing_in_the_registry_is_refused(hass):
    service, _ = _service(hass)
    other = make_entry(hass, serial="999999")
    with pytest.raises(ServiceValidationError, match="not in the internal"):
        service.get_coordinator(_call(configid=other.entry_id))


async def test_registry_helpers_ignore_unknown_entries(hass):
    entry = make_entry(hass, serial="777777")
    service_module.remove_config_entry_from_service(entry)
    assert entry.entry_id not in service_module._COORDINATOR_PER_CONFIG_ENTRY_ID_MAP


# ----------------------------------------------------------------------------- start of an entry

@pytest.fixture
def setup_patches():
    with patch.object(GoeChargerDataUpdateCoordinator, "_async_update_data", AsyncMock(return_value={"car": 1})), \
         patch.object(GoeChargerDataUpdateCoordinator, "read_versions", AsyncMock(return_value=True)), \
         patch.object(GoeChargerDataUpdateCoordinator, "check_for_16a_limit", AsyncMock()) as limiter, \
         patch.object(GoeChargerDataUpdateCoordinator, "start_websocket_and_wait_for_first_data", AsyncMock(return_value=True)) as ws_start, \
         patch.object(GoeChargerDataUpdateCoordinator, "start_watchdog", AsyncMock()) as watchdog:
        yield SimpleNamespace_(limiter=limiter, ws_start=ws_start, watchdog=watchdog)


class SimpleNamespace_:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


async def _setup(hass, entry, limit=False):
    with patch.object(hass.config_entries, "async_forward_entry_setups", AsyncMock()) as forward:
        result = await async_setup_entry(hass, entry)
    return result, forward


async def test_polling_charger_starts_registers_services_and_counts(hass, setup_patches):
    entry = make_entry(hass)
    result, forward = await _setup(hass, entry)
    assert result is True
    assert isinstance(hass.data[DOMAIN][entry.entry_id], GoeChargerDataUpdateCoordinator)
    assert hass.data[DOMAIN][ACTIVE_CHARGER_COUNTER] == 1
    assert hass.services.has_service(DOMAIN, SERVICE_SET_PV_DATA) and hass.services.has_service(DOMAIN, SERVICE_STOP_CHARGING)
    forward.assert_awaited_once()
    setup_patches.ws_start.assert_not_awaited()
    setup_patches.watchdog.assert_not_awaited()


async def test_second_charger_shares_the_services_and_joins_the_registry(hass, setup_patches):
    first, second = make_entry(hass, serial="111111"), make_entry(hass, serial="222222")
    await _setup(hass, first)
    await _setup(hass, second)
    assert hass.data[DOMAIN][ACTIVE_CHARGER_COUNTER] == 2
    assert set(service_module._COORDINATOR_PER_CONFIG_ENTRY_ID_MAP) == {first.entry_id, second.entry_id}


async def test_controller_does_not_register_charger_services(hass, setup_patches):
    entry = make_entry(hass, intg_type="controller")
    await _setup(hass, entry)
    assert not hass.services.has_service(DOMAIN, SERVICE_SET_PV_DATA)
    assert ACTIVE_CHARGER_COUNTER not in hass.data[DOMAIN]


async def test_websocket_charger_starts_the_connection_and_the_watchdog(hass, setup_patches):
    entry = make_entry(hass, password="secret")
    await _setup(hass, entry)
    setup_patches.ws_start.assert_awaited_once_with(is_integration_init=True)
    setup_patches.watchdog.assert_awaited_once()


async def test_watchdog_waits_for_home_assistant_to_finish_starting(hass, setup_patches):
    entry = make_entry(hass, password="secret")
    hass.set_state(CoreState.starting)
    await _setup(hass, entry)
    setup_patches.watchdog.assert_not_awaited()
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()
    setup_patches.watchdog.assert_awaited_once()


async def test_limited_charger_starts_the_16_a_task(hass, setup_patches):
    async def limited(self):
        self.limit_to16a = True
        return True

    entry = make_entry(hass)
    with patch.object(GoeChargerDataUpdateCoordinator, "read_versions", limited):
        await _setup(hass, entry)
        await hass.async_block_till_done()
    setup_patches.limiter.assert_awaited_once()


async def test_unknown_language_falls_back_to_english_texts(hass, setup_patches):
    from homeassistant.exceptions import ConfigEntryNotReady
    hass.config.language = "xx"
    entry = make_entry(hass, password="secret")
    setup_patches.ws_start.side_effect = RuntimeError("connection broke")
    with pytest.raises(ConfigEntryNotReady, match="The Websocket could not be started"):
        await _setup(hass, entry)


async def test_missing_device_data_is_reported_with_its_own_message(hass, setup_patches):
    from homeassistant.exceptions import ConfigEntryNotReady
    entry = make_entry(hass, password="secret")
    setup_patches.ws_start.return_value = False
    with pytest.raises(ConfigEntryNotReady, match="could not fetch essential"):
        await _setup(hass, entry)


# ----------------------------------------------------------------------------- end of an entry

async def test_unloading_the_last_charger_removes_the_services(hass, setup_patches):
    entry = make_entry(hass)
    await _setup(hass, entry)
    with patch.object(hass.config_entries, "async_unload_platforms", AsyncMock(return_value=True)):
        assert await async_unload_entry(hass, entry) is True
    assert entry.entry_id not in hass.data[DOMAIN]
    assert not hass.services.has_service(DOMAIN, SERVICE_SET_PV_DATA)
    assert entry.entry_id not in service_module._COORDINATOR_PER_CONFIG_ENTRY_ID_MAP


async def test_unloading_one_of_two_chargers_keeps_the_services(hass, setup_patches):
    first, second = make_entry(hass, serial="111111"), make_entry(hass, serial="222222")
    await _setup(hass, first)
    await _setup(hass, second)
    with patch.object(hass.config_entries, "async_unload_platforms", AsyncMock(return_value=True)):
        await async_unload_entry(hass, first)
    assert hass.services.has_service(DOMAIN, SERVICE_SET_PV_DATA)
    assert hass.data[DOMAIN][ACTIVE_CHARGER_COUNTER] == 1


async def test_failed_platform_unload_keeps_everything(hass, setup_patches):
    entry = make_entry(hass)
    await _setup(hass, entry)
    with patch.object(hass.config_entries, "async_unload_platforms", AsyncMock(return_value=False)):
        assert await async_unload_entry(hass, entry) is False
    assert entry.entry_id in hass.data[DOMAIN] and hass.services.has_service(DOMAIN, SERVICE_SET_PV_DATA)


async def test_changed_entry_is_reloaded(hass):
    entry = make_entry(hass)
    with patch.object(hass.config_entries, "async_reload", AsyncMock()) as reload:
        await entry_update_listener(hass, entry)
    reload.assert_awaited_once_with(entry.entry_id)


async def test_yaml_setup_is_accepted_and_ignored(hass):
    assert await async_setup(hass, {}) is True
