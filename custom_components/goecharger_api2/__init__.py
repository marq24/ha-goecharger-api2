import asyncio
import logging
import random
from collections import ChainMap
from datetime import timedelta
from time import time
from typing import Any, Final

from aiohttp import ClientConnectionError
from packaging.version import Version

from custom_components.goecharger_api2.pygoecharger_ha import GoeChargerApiV2Bridge, TRANSLATIONS, INTG_TYPE
from custom_components.goecharger_api2.pygoecharger_ha.keys import Tag
from homeassistant.components.number import NumberDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_TYPE,
    CONF_ID,
    CONF_SCAN_INTERVAL,
    CONF_MODE,
    CONF_TOKEN,
    CONF_PASSWORD,
    EVENT_HOMEASSISTANT_STARTED
)
from homeassistant.core import HomeAssistant, Event, SupportsResponse, CoreState
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import (
    config_validation as config_val,
    entity_registry as entity_reg,
    device_registry as device_reg
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import Entity, EntityDescription
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.typing import UNDEFINED, UndefinedType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.loader import async_get_integration
from .const import (
    LAN,
    WAN,
    NAME,
    DOMAIN,
    MANUFACTURER,
    PLATFORMS,
    STARTUP_MESSAGE,
    SERVICE_SET_PV_DATA,
    SERVICE_STOP_CHARGING,
    CONF_11KWLIMIT,
    CONF_INTEGRATION_TYPE,
    CONFIG_VERSION, CONFIG_MINOR_VERSION
)
from .service import GoeChargerApiV2Service

_LOGGER: logging.Logger = logging.getLogger(__package__)

SCAN_INTERVAL = timedelta(seconds=10)
CONFIG_SCHEMA = config_val.removed(DOMAIN, raise_if_present=False)
WEBSOCKET_WATCHDOG_INTERVAL: Final = timedelta(minutes=5, seconds=1)


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    if config_entry.version < CONFIG_VERSION:
        if config_entry.data is not None and len(config_entry.data) > 0:
            _LOGGER.debug(f"Migrating configuration from version {config_entry.version}.{config_entry.minor_version}")
            if config_entry.options is not None and len(config_entry.options):
                new_data = {**config_entry.data, **config_entry.options}
            else:
                new_data = config_entry.data
            hass.config_entries.async_update_entry(config_entry, data=new_data, options={}, version=CONFIG_VERSION, minor_version=CONFIG_MINOR_VERSION)
            _LOGGER.debug(f"Migration to configuration version {config_entry.version}.{config_entry.minor_version} successful")
    return True


async def async_setup(hass: HomeAssistant, config: dict):  # pylint: disable=unused-argument
    """Set up this integration using YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    if DOMAIN not in hass.data:
        the_integration = await async_get_integration(hass, DOMAIN)
        intg_version = the_integration.version if the_integration is not None else "UNKNOWN"
        _LOGGER.info(STARTUP_MESSAGE % intg_version)
        hass.data.setdefault(DOMAIN, {"manifest_version": intg_version})

    coordinator = GoeChargerDataUpdateCoordinator(hass, config_entry)
    await coordinator.async_refresh()
    if not coordinator.last_update_success:
        raise ConfigEntryNotReady
    else:
        if not await coordinator.read_versions():
            raise ConfigEntryNotReady("Could not read versions from charger/controller! - please enable debug logging to see more details!")

    start_ws_watch_dog = False
    if coordinator.intg_type == INTG_TYPE.CHARGER.value:
        a_pwd = config_entry.data.get(CONF_PASSWORD, None)
        if a_pwd is not None and len(a_pwd.strip()) > 0:
            start_ws_watch_dog = True

    if start_ws_watch_dog:
        # ws watchdog...
        if hass.state is CoreState.running:
            _LOGGER.debug(f"starting watchdog INSTANTLY")
            await coordinator.start_watchdog()
        else:
            _LOGGER.debug(f"starting watchdog delayed... (when EVENT_HOMEASSISTANT_STARTED is fired)")
            hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, coordinator.start_watchdog)

    hass.data[DOMAIN][config_entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    # initialize our service...
    if coordinator.intg_type == INTG_TYPE.CHARGER.value:
        service = GoeChargerApiV2Service(hass, config_entry, coordinator)
        hass.services.async_register(DOMAIN, SERVICE_SET_PV_DATA, service.set_pv_data,
                                     supports_response=SupportsResponse.OPTIONAL)
        hass.services.async_register(DOMAIN, SERVICE_STOP_CHARGING, service.stop_charging,
                                     supports_response=SupportsResponse.OPTIONAL)

    if coordinator.check_for_max_of_16a:
        asyncio.create_task(coordinator.check_for_16a_limit(hass, config_entry.entry_id))

    asyncio.create_task(coordinator.cleanup_device_registry(hass))

    # double check, if the ws_watchdog should be started...
    if start_ws_watch_dog and coordinator._ws_start_task is None:
        asyncio.create_task(coordinator._async_watchdog_check())

    config_entry.async_on_unload(config_entry.add_update_listener(entry_update_listener))
    # ok we are done...
    return True


def check_unload_services(hass: HomeAssistant):
    active_integration_configs = hass.config_entries.async_entries(domain=DOMAIN, include_disabled=False, include_ignore=False)
    if active_integration_configs is not None and len(active_integration_configs) > 0:
        return False
    else:
        return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)

    if unload_ok:
        if DOMAIN in hass.data and config_entry.entry_id in hass.data[DOMAIN]:
            coordinator = hass.data[DOMAIN][config_entry.entry_id]
            coordinator.stop_watchdog()
            coordinator.clear_data()
            hass.data[DOMAIN].pop(config_entry.entry_id)

        # ONLY remove the SERVICES if this is the LAST ACTIVE config_entry that will be unloaded!
        if check_unload_services(hass):
            hass.services.async_remove(DOMAIN, SERVICE_SET_PV_DATA)
            hass.services.async_remove(DOMAIN, SERVICE_STOP_CHARGING)

    return unload_ok


async def entry_update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    _LOGGER.debug(f"entry_update_listener() called for entry: {config_entry.entry_id}")
    await hass.config_entries.async_reload(config_entry.entry_id)


@staticmethod
async def check_and_write_to_16a(hass: HomeAssistant, config_entry_id: str, bridge: GoeChargerApiV2Bridge):
    _LOGGER.info(f"checking entities")
    tags = []
    if hass is not None:
        a_entity_reg = entity_reg.async_get(hass)
        if a_entity_reg is not None:
            MAX_A: Final = 16
            # we query from the HA entity registry all entities that are created by this
            # 'config_entry' -> we use here just default api calls [no more hacks!]
            key_list = []
            for entity in entity_reg.async_entries_for_config_entry(registry=a_entity_reg,
                                                                    config_entry_id=config_entry_id):
                if entity.original_device_class == NumberDeviceClass.CURRENT:
                    if "max" in entity.capabilities:
                        if entity.capabilities["max"] == MAX_A:
                            key_list.append(entity.translation_key)

            if len(key_list) > 0:
                _LOGGER.info(f"16A checker: found {len(key_list)} entities with max current of {MAX_A}A - {key_list}")
                final_key_list = []
                final_dics = {}
                for a_key in key_list:
                    if '_' in a_key:
                        res = a_key.split('_')
                        if res[0] not in final_dics:
                            final_dics[res[0]] = []
                        final_dics[res[0]].append(res[1])
                        a_key = res[0]

                    if a_key not in final_key_list:
                        final_key_list.append(a_key)

                try:
                    res = await bridge._read_filtered_data(filters=",".join(final_key_list), log_info="16A checker")
                    keys_to_patch = []
                    for a_res_key in res.keys():
                        res_obj = res[a_res_key]
                        if isinstance(res_obj, int):
                            if res_obj > MAX_A:
                                res[a_res_key] = MAX_A
                                if a_res_key not in keys_to_patch:
                                    keys_to_patch.append(a_res_key)
                        elif isinstance(res_obj, dict):
                            #_LOGGER.warning(f"found dict in 16A check: {res_obj}")
                            vals_to_check = final_dics.get(a_res_key)
                            for val in vals_to_check:
                                if res_obj[val] > MAX_A:
                                    res[a_res_key][val] = MAX_A
                                    if a_res_key not in keys_to_patch:
                                        keys_to_patch.append(a_res_key)

                    _LOGGER.info(f"reduce the following keys: {keys_to_patch}")
                    for a_key in keys_to_patch:
                        _LOGGER.info(f"reduce {a_key} to 16A -> writing {res[a_key]}")
                        await bridge.write_value_to_key(a_key, res[a_key])
                except Exception as e:
                    _LOGGER.error(f"Error while forcing 16A settings:", e)

@staticmethod
async def check_device_registry(hass: HomeAssistant):
    _LOGGER.info(f"check device registry...")
    if hass is not None:
        a_device_reg = device_reg.async_get(hass)
        if a_device_reg is not None:
            key_list = []
            for a_device_entry in list(a_device_reg.devices.values()):
                if hasattr(a_device_entry, "identifiers"):
                    ident_value = a_device_entry.identifiers
                    if f"{ident_value}".__contains__(DOMAIN) and len(next(iter(ident_value))) != 4:
                        _LOGGER.debug(f"found a OLD {DOMAIN} DeviceEntry: {a_device_entry}")
                        key_list.append(a_device_entry.id)

            if len(key_list) > 0:
                _LOGGER.info(f"NEED TO DELETE old {DOMAIN} DeviceEntries: {key_list}")
                for a_device_entry_id in key_list:
                    a_device_reg.async_remove_device(device_id=a_device_entry_id)


class GoeChargerDataUpdateCoordinator(DataUpdateCoordinator):

    _debounced_update_task: asyncio.Task | None = None
    _watchdog = None
    _ws_start_task: asyncio.Task | None = None

    def __init__(self, hass: HomeAssistant, config_entry):
        self._watchdog = None
        self._ws_start_task = None
        self._force_classic_requests = False

        lang = hass.config.language.lower()
        self._hass = hass
        self.name = config_entry.title

        # are we a charger or a controller ?! (by default we are obvious a go-eCharger)
        self.intg_type = INTG_TYPE.CHARGER.value
        if CONF_INTEGRATION_TYPE in config_entry.data and config_entry.data.get(CONF_INTEGRATION_TYPE) == INTG_TYPE.CONTROLLER.value:
            self.intg_type = INTG_TYPE.CONTROLLER.value

        if CONF_MODE in config_entry.data and config_entry.data.get(CONF_MODE) == WAN:
            self.mode = WAN
            self.bridge = GoeChargerApiV2Bridge(
                intg_type=self.intg_type,
                host=None,
                access_password=config_entry.data.get(CONF_PASSWORD, None),
                serial=config_entry.data.get(CONF_ID),
                token=config_entry.data.get(CONF_TOKEN),
                web_session=async_get_clientsession(hass),
                lang=lang)
        else:
            self.mode = LAN
            self.bridge = GoeChargerApiV2Bridge(
                intg_type=self.intg_type,
                host=config_entry.data.get(CONF_HOST),
                access_password=config_entry.data.get(CONF_PASSWORD, None),
                serial=None,
                token=None,
                web_session=async_get_clientsession(hass),
                lang=lang)

        global SCAN_INTERVAL
        SCAN_INTERVAL = timedelta(seconds=config_entry.data.get(CONF_SCAN_INTERVAL, 5))
        self._serial = config_entry.data.get(CONF_ID)

        self.lang_map = None
        if lang in TRANSLATIONS:
            self.lang_map = TRANSLATIONS[lang]
        else:
            self.lang_map = TRANSLATIONS["en"]

        # config_entry only need for providing the '_device_info_dict'...
        self._config_entry = config_entry
        self._is_charger_fw_version_60_0_or_higher = False
        self._no_cards_list_is_present = False
        self._CLIENT_COMMUNICATION_ERROR_TS = 0
        self._CLIENT_COMMUNICATION_ERROR_COUNT = 0
        self._RESTART_TRIGGERED = False
        self._debounced_update_task = None
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)

    def cards_as_single_entries(self):
        return self._is_charger_fw_version_60_0_or_higher and (self.bridge.ws_connected or self._no_cards_list_is_present)

    async def start_watchdog(self, event=None):
        """Start websocket watchdog."""
        await self._async_watchdog_check()
        self._watchdog = async_track_time_interval(
            self.hass,
            self._async_watchdog_check,
            WEBSOCKET_WATCHDOG_INTERVAL,
        )

    def stop_watchdog(self):
        if hasattr(self, "_watchdog") and self._watchdog is not None:
            self._watchdog()

    def _check_for_ws_task_and_cancel_if_running(self):
        if self._ws_start_task is not None and not self._ws_start_task.done():
            _LOGGER.debug(f"Watchdog: websocket connect task is still running - canceling it...")
            try:
                canceled = self._ws_start_task.cancel()
                _LOGGER.debug(f"Watchdog: websocket connect task was CANCELED? {canceled}")
            except BaseException as ex:
                _LOGGER.info(f"Watchdog: websocket connect task cancel failed: {type(ex).__name__} - {ex}")
            self._ws_start_task = None

    async def _async_watchdog_check(self, *_):
        if not self.bridge.ws_connected:
            self._check_for_ws_task_and_cancel_if_running()
            _LOGGER.info(f"Watchdog: websocket connect required")
            self.bridge.ws_set_coordinator(coordinator=self)
            self._ws_start_task = self._config_entry.async_create_background_task(self.hass, self.bridge.ws_connect(), "ws_connection")
            if self._ws_start_task is not None:
                _LOGGER.debug(f"Watchdog: task created {self._ws_start_task.get_coro()}")
        else:
            _LOGGER.debug(f"Watchdog: websocket is connected")
            if not self.bridge.ws_check_last_update():
                self._check_for_ws_task_and_cancel_if_running()

    # Callable[[Event], Any]
    def __call__(self, evt: Event) -> bool:
        _LOGGER.debug(f"Event arrived: {evt}")
        return True

    def clear_data(self):
        _LOGGER.debug(f"clear_data called...")
        self._check_for_ws_task_and_cancel_if_running()
        self.bridge.clear_data()
        if self.data is not None:
            self.data.clear()
        self._CLIENT_COMMUNICATION_ERROR_TS = 0
        self._CLIENT_COMMUNICATION_ERROR_COUNT = 0
        self._RESTART_TRIGGERED = False
        self._debounced_update_task = None

    async def trigger_restart_delayed(self) -> None:
        # Generate a random sleep time between 5 and 10 minutes (300 and 600 seconds)
        random_seconds = random.uniform(300, 600)
        # random_seconds = random.uniform(60, 120)
        _LOGGER.info(f"trigger_restart_delayed(): Sleeping for {random_seconds:.2f} seconds...")
        await asyncio.sleep(random_seconds)
        _LOGGER.info(f"trigger_restart_delayed(): --- RELOAD INTEGRATION NOW ---")
        await self.hass.config_entries.async_reload(self._config_entry.entry_id)

    def request_update_in_sec(self, seconds: float):
        if self._debounced_update_task is not None and not self._debounced_update_task.done():
            self._debounced_update_task.cancel()
        self._debounced_update_task = asyncio.create_task(self._debounce_coordinator_update(seconds))

    async def _debounce_coordinator_update(self, seconds: float):
        await asyncio.sleep(seconds)
        await self.async_refresh()

    def handle_write_result(self, a_type, value, key, result, entity):
        if result is None and self.bridge.ws_connected:
            # when using websocket - the writing result will be handled
            # already in the ws-response processor...
            return
        else:
            _LOGGER.debug(f"handle_write_result() {a_type} result: {result}")

        if key in result:
            self.data[key] = result[key]
        else:
            _LOGGER.error(f"handle_write_result() could not write {a_type} value: '{value}' to: {key} result was: {result}")

        do_refresh = True
        if self.intg_type == INTG_TYPE.CHARGER.value:
            # since we do not force an update when setting PV surplus data, we 'patch' internally our values
            if key == Tag.IDS.key:
                self.data = ChainMap(self.bridge._ws_states, self.bridge._config, self.bridge._states, self.bridge._versions)
                self.async_update_listeners()
                do_refresh = False

            elif key == Tag.INTERNAL_FORCE_REFRESH_ALL.key:
                self.request_update_in_sec(2.5)
                do_refresh = False

        if do_refresh:
            if entity is not None:
                entity.async_schedule_update_ha_state(force_refresh=True)
            #self.request_update_in_sec(10)

    def _handle_client_connection_error(self, msg: str, exception: Exception):
        # ok, we have issues communicating with the Wallbox...
        # let's delay the next request at least by 5 minutes
        #  to allow the wallbox to become alive again?!
        self._CLIENT_COMMUNICATION_ERROR_TS = time()
        self._CLIENT_COMMUNICATION_ERROR_COUNT += 1
        if self._CLIENT_COMMUNICATION_ERROR_COUNT > 8:
            _LOGGER.warning(f"{msg}: Too many ClientConnectionError #{self._CLIENT_COMMUNICATION_ERROR_COUNT} while fetching data: {exception} - will try to restart integration.")
            if not self._RESTART_TRIGGERED:
                _LOGGER.info(f"{msg}: TRIGGER RESTART...")
                self._RESTART_TRIGGERED = True
                self.hass.async_create_task(self.trigger_restart_delayed())
        else:
            _LOGGER.info(f"{msg}: ClientConnectionError #{self._CLIENT_COMMUNICATION_ERROR_COUNT} while fetching data: {exception}")

    async def _async_update_data(self) -> dict:
        """Update data via library."""
        _LOGGER.debug(f"_async_update_data(): CALLED")
        if self.bridge.ws_connected and self._force_classic_requests is False:
            _LOGGER.debug(f"_async_update_data called (but websocket is active - no data will be requested!)")
            return None
        else:
            if self._CLIENT_COMMUNICATION_ERROR_TS + 3600 > time():
                time_info = 3600 - (time() - self._CLIENT_COMMUNICATION_ERROR_TS)
                _LOGGER.info(f"_async_update_data(): skipping update due to client communication error for the next {time_info} seconds")
                return self.data
            if self._RESTART_TRIGGERED:
                _LOGGER.info(f"_async_update_data(): RESTART is TRIGGERED (waiting for random sleep delay) - skipping update")
                return self.data
    
            try:
                new_data = await self.bridge.read_all()
                if new_data is not None and len(new_data) > 0:
                    self._CLIENT_COMMUNICATION_ERROR_TS = 0
                    self._CLIENT_COMMUNICATION_ERROR_COUNT = 0
                # THIS is JUST FOR INTERNAL TESTING...
                # if not self._RESTART_TRIGGERED:
                #     _LOGGER.info(f"_async_update_data(): TRIGGER RESTART...")
                #     self._RESTART_TRIGGERED = True
                #     self.hass.async_create_task(self.trigger_restart_delayed())
                return new_data
    
            except ClientConnectionError as exception:
                self._handle_client_connection_error("_async_update_data()", exception)
                raise UpdateFailed(f"Error while fetching data: {exception}") from exception
            except UpdateFailed as exception:
                raise UpdateFailed() from exception
            except Exception as other:
                _LOGGER.error(f"_async_update_data(): unexpected: {other}")
                raise UpdateFailed() from other

    async def async_write_key(self, key: str, value, entity: Entity = None) -> dict:
        if self._CLIENT_COMMUNICATION_ERROR_TS + 3600 > time():
            time_info = 3600 - (time() - self._CLIENT_COMMUNICATION_ERROR_TS)
            _LOGGER.info(f"async_write_key(): skipping due to client communication error for the next {time_info} seconds")
            raise ValueError(f"async_write_key(): skipping due to client communication error for the next {time_info} seconds")
        if self._RESTART_TRIGGERED:
            _LOGGER.info(f"async_write_key(): RESTART is TRIGGERED (waiting for random sleep delay)")
            raise ValueError("async_write_key(): RESTART is TRIGGERED (waiting for random sleep delay)")

        try:
            result = await self.bridge.write_value_to_key(key, value)
            self.handle_write_result("single", value, key, result, entity)
            return result

        except ClientConnectionError as exception:
            self._handle_client_connection_error("async_write_key()", exception)
            raise ValueError(f"ClientConnectionError while writing {key} to wallbox: {exception}") from exception
        except Exception as e:
            _LOGGER.error(f"Error while writing single {key} to wallbox: {e}")
            raise ValueError(f"Exception while writing {key} to wallbox: {e}") from e

    async def async_write_multiple_keys(self, attr:dict, key: str, value, entity: Entity = None) -> dict:
        if self._CLIENT_COMMUNICATION_ERROR_TS + 3600 > time():
            time_info = 3600 - (time() - self._CLIENT_COMMUNICATION_ERROR_TS)
            _LOGGER.info(f"async_write_multiple_keys(): skipping due to client communication error for the next {time_info} seconds")
            raise ValueError(f"async_write_multiple_keys(): skipping due to client communication error for the next {time_info} seconds")
        if self._RESTART_TRIGGERED:
            _LOGGER.info(f"async_write_multiple_keys(): RESTART is TRIGGERED (waiting for random sleep delay)")
            raise ValueError("async_write_multiple_keys(): RESTART is TRIGGERED (waiting for random sleep delay)")

        try:
            result = await self.bridge.write_multiple_values_to_keys(attr, key, value)
            self.handle_write_result("multiple", value, key, result, entity)
            return result

        except ClientConnectionError as exception:
            self._handle_client_connection_error("async_write_multiple_keys()", exception)
            raise ValueError(f"ClientConnectionError while writing multiple {key} to wallbox: {exception}") from exception
        except Exception as e:
            _LOGGER.error(f"Error while writing multiple {key} to wallbox: {e}")
            raise ValueError(f"Exception while writing multiple {key} to wallbox: {e}") from e

    async def read_versions(self):
        if not await self.bridge.read_versions():
            return False

        # charger and controller have both FWV tag...
        if Tag.FWV.key in self.bridge._versions:
            sw_version = self.bridge._versions.get(Tag.FWV.key, "0.0")
            if '-' in sw_version:
                _LOGGER.debug(f"read_versions(): firmware version must be patched! {sw_version}")
                sw_version = sw_version[:sw_version.index('-')]

            if self.intg_type == INTG_TYPE.CHARGER.value:
                # when we request the version info for the charger, then this request will/should also contain the
                # key 'cards'. The cards array  has been removed in FW 60.0 - but currently in my 60.3 it's back
                # again - so as long as this array is available, we can/should/will use it?!
                self._is_charger_fw_version_60_0_or_higher = Version(sw_version) >= Version("60.0")
                if len(self.bridge._versions.get(Tag.CARDS.key, [])) == 0:
                    self._no_cards_list_is_present = True
        else:
            sw_version = "UNKNOWN"

        if self.mode == LAN:
            self._device_info_dict = {
                # be careful when adjusting the 'identifiers' -> since this will create probably new DeviceEntries
                # and there exists also code which CLEAN all Devices that does not have 4 (four) identifier values!!
                "identifiers": {(
                    DOMAIN,
                    self._serial,
                    self._config_entry.data.get(CONF_HOST),
                    self._config_entry.title)},
                "manufacturer": MANUFACTURER,
                "name": self._config_entry.title,
                "model": self._config_entry.data.get(CONF_TYPE),
                "sw_version": sw_version
                # hw_version
            }
        else:
            self._device_info_dict = {
                # be careful when adjusting the 'identifiers' -> since this will create probably new DeviceEntries
                # and there exists also code which CLEAN all Devices that does not have 4 (four) identifier values!!
                "identifiers": {(
                    DOMAIN,
                    self._serial,
                    self._config_entry.data.get(CONF_TOKEN),
                    self._config_entry.title)},
                "manufacturer": MANUFACTURER,
                "name": self._config_entry.title,
                "model": self._config_entry.data.get(CONF_TYPE),
                "sw_version": sw_version
                # hw_version
            }

        self.available_cards_idx = []
        # additional charger stuff...
        if self.intg_type == INTG_TYPE.CHARGER.value:
            # fetching the available cards that are enabled
            idx = 1
            if self._is_charger_fw_version_60_0_or_higher and self._no_cards_list_is_present:
                # since FWV 60.0 there is no cards object any longer...
                for a_card_number in range(0, 10):
                    a_key_id = f"c{a_card_number}i"
                    if self.bridge._versions.get(a_key_id, False):
                        self.available_cards_idx.append(str(idx))
                    idx = idx + 1

            elif Tag.CARDS.key in self.bridge._versions:
                for a_card in self.bridge._versions[Tag.CARDS.key]:
                    if a_card["cardId"]:
                        self.available_cards_idx.append(str(idx))
                    idx = idx + 1
            else:
                _LOGGER.info(f"NO CARDS Object found!")

            _LOGGER.info(f"active cards {self.available_cards_idx}")

            # check for the 16A limiter...
            self.check_for_max_of_16a = self._config_entry.data.get(CONF_11KWLIMIT, False)

            self.limit_to16a = (self.check_for_max_of_16a
                                or self.bridge._versions.get(Tag.VAR.key, -1) == 11
                                or self.data.get(Tag.ADI.key, False))

            if (self.limit_to16a):
                _LOGGER.info(f"LIMIT to 16A is active")
        else:
            # no additional controller stuff... but we need to init some variables
            self.check_for_max_of_16a = False
            self.limit_to16a = False

        return True

    async def check_for_16a_limit(self, hass, entry_id):
        _LOGGER.debug(f"check relevant entities for 16A limit... in 15sec")
        await asyncio.sleep(15)
        _LOGGER.debug(f"check relevant entities for 16A limit NOW!")
        await check_and_write_to_16a(hass=hass, config_entry_id=entry_id, bridge=self.bridge)

    async def cleanup_device_registry(self, hass: HomeAssistant):
        _LOGGER.debug(f"check device registry for orphan {DOMAIN} entries... in 20sec")
        await asyncio.sleep(20)
        _LOGGER.debug(f"check device registry for orphan {DOMAIN} entries NOW!")
        await check_device_registry(hass=hass)


class GoeChargerBaseEntity(Entity):
    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, entity_type:str, coordinator: GoeChargerDataUpdateCoordinator, description: EntityDescription) -> None:
        # make sure that we keep the CASE of the key!
        self.data_key = description.key

        # tuple_idx must have description.translation_key !
        if hasattr(description, "tuple_idx") and description.tuple_idx is not None:
            if description.translation_key is not None:
                self._attr_translation_key = description.translation_key.lower()
            else:
                if len(description.tuple_idx) > 1:
                    subKey1 = description.tuple_idx[0]
                    subKey2 = description.tuple_idx[1]
                    self._attr_translation_key = f"{self.data_key}_{subKey1}_{subKey2}".lower()
                elif len(description.tuple_idx) > 0:
                    subKey1 = description.tuple_idx[0]
                    self._attr_translation_key = f"{self.data_key}_{subKey1}".lower()

        elif hasattr(description, "idx") and description.idx is not None:
            self._attr_translation_key = f"{self.data_key.lower()}_{description.idx}"
        elif hasattr(description, "lookup") and description.lookup is not None:
            self._attr_translation_key = f"{self.data_key.lower()}_value"
        elif hasattr(description, "differential_base_key") and description.differential_base_key is not None:
            self._attr_translation_key = f"{self.data_key.lower()}_delta"
        else:
            self._attr_translation_key = self.data_key.lower()

        self.entity_description = description
        self.coordinator = coordinator

        if self.coordinator.mode == WAN:
            self.entity_id = f"{entity_type}.goe_wan_{self.coordinator._serial}_{self._attr_translation_key}".lower()
        else:
            self.entity_id = f"{entity_type}.goe_{self.coordinator._serial}_{self._attr_translation_key}".lower()

    def _name_internal(self, device_class_name: str | None,
                       platform_translations: dict[str, Any], ) -> str | UndefinedType | None:
        return super()._name_internal(device_class_name, platform_translations)

    @property
    def device_info(self) -> dict:
        return self.coordinator._device_info_dict

    @property
    def available(self):
        """Return True if entity is available."""
        return self.coordinator.last_update_success

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return f"{DOMAIN}.{self.entity_id.split('.')[1]}".lower()

    async def async_added_to_hass(self):
        """Connect to dispatcher listening for entity data notifications."""
        self.async_on_remove(self.coordinator.async_add_listener(self.async_write_ha_state))

    async def async_update(self):
        """Update entity."""
        await self.coordinator.async_request_refresh()

    @property
    def should_poll(self) -> bool:
        return False

    def _friendly_name_internal(self) -> str | None:
        """Return the friendly name.

        If has_entity_name is False, this returns self.name
        If has_entity_name is True, this returns device.name + self.name
        """
        name = self.name
        if name is UNDEFINED:
            name = None

        if not self.has_entity_name or not (device_entry := self.device_entry):
            return name

        device_name = device_entry.name_by_user or device_entry.name
        if name is None and self.use_device_name:
            return device_name

        # we overwrite the default impl here and just return our 'name'
        # return f"{device_name} {name}" if device_name else name
        if device_entry.name_by_user is not None:
            return f"{device_entry.name_by_user} {name}" if device_name else name
        else:
            return f"[go-e] {name}"
