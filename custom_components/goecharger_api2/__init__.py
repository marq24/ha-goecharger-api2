import asyncio
import logging
from datetime import timedelta
from typing import Any, Final

from homeassistant.components.number import NumberDeviceClass
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_TYPE, CONF_ID, CONF_SCAN_INTERVAL, CONF_MODE, CONF_TOKEN
from homeassistant.core import Config, Event, SupportsResponse
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as config_val, entity_registry as entity_reg
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import Entity, EntityDescription
from homeassistant.helpers.typing import UNDEFINED, UndefinedType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.goecharger_api2.pygoecharger_ha import GoeChargerApiV2Bridge, TRANSLATIONS
from custom_components.goecharger_api2.pygoecharger_ha.keys import Tag
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
    CONF_11KWLIMIT
)
from .service import GoeChargerApiV2Service

_LOGGER: logging.Logger = logging.getLogger(__package__)

SCAN_INTERVAL = timedelta(seconds=10)
CONFIG_SCHEMA = config_val.removed(DOMAIN, raise_if_present=False)


async def async_setup(hass: HomeAssistant, config: Config):  # pylint: disable=unused-argument
    """Set up this integration using YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    if DOMAIN not in hass.data:
        value = "UNKOWN"
        _LOGGER.info(STARTUP_MESSAGE)
        hass.data.setdefault(DOMAIN, {"manifest_version": value})

    coordinator = GoeChargerDataUpdateCoordinator(hass, config_entry)
    await coordinator.async_refresh()
    if not coordinator.last_update_success:
        raise ConfigEntryNotReady
    else:
        await coordinator.read_versions()

    hass.data[DOMAIN][config_entry.entry_id] = coordinator

    for platform in PLATFORMS:
        hass.async_create_task(hass.config_entries.async_forward_entry_setup(config_entry, platform))

    if config_entry.state != ConfigEntryState.LOADED:
        config_entry.add_update_listener(async_reload_entry)

    # initialize our service...
    service = GoeChargerApiV2Service(hass, config_entry, coordinator)
    hass.services.async_register(DOMAIN, SERVICE_SET_PV_DATA, service.set_pv_data,
                                 supports_response=SupportsResponse.OPTIONAL)
    hass.services.async_register(DOMAIN, SERVICE_STOP_CHARGING, service.stop_charging,
                                 supports_response=SupportsResponse.OPTIONAL)

    if coordinator.check_for_max_of_16a:
        asyncio.create_task(coordinator.check_for_16a_limit(hass, config_entry.entry_id))

    # ok we are done...
    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    unload_ok = all(await asyncio.gather(*[
        hass.config_entries.async_forward_entry_unload(config_entry, platform)
        for platform in PLATFORMS
    ]))

    if unload_ok:
        if DOMAIN in hass.data and config_entry.entry_id in hass.data[DOMAIN]:
            coordinator = hass.data[DOMAIN][config_entry.entry_id]
            coordinator.clear_data()
            hass.data[DOMAIN].pop(config_entry.entry_id)

        hass.services.async_remove(DOMAIN, SERVICE_SET_PV_DATA)
        hass.services.async_remove(DOMAIN, SERVICE_STOP_CHARGING)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Reload config entry."""
    if await async_unload_entry(hass, config_entry):
        await asyncio.sleep(2)
        await async_setup_entry(hass, config_entry)


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
                                keys_to_patch.append(a_res_key)
                                res[a_res_key] = MAX_A
                        elif isinstance(res_obj, dict):
                            vals_to_check = final_dics.get(a_res_key)
                            for val in vals_to_check:
                                if res_obj[val] > MAX_A:
                                    res[a_res_key][val] = MAX_A
                                    if a_res_key not in keys_to_patch:
                                        keys_to_patch.append(a_res_key)

                    for a_key in keys_to_patch:
                        _LOGGER.info(f"reduce {a_res_key} to 16A -> writing {res[a_key]}")
                        await bridge.write_value_to_key(a_res_key, res[a_key])
                except Exception as e:
                    _LOGGER.error(f"Error while forcing 16A settings:", e)


class GoeChargerDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, config_entry):
        lang = hass.config.language.lower()
        self.name = config_entry.title
        if CONF_MODE in config_entry.data and config_entry.data.get(CONF_MODE) == WAN:
            self.mode = WAN
            self.bridge = GoeChargerApiV2Bridge(host=None,
                                                serial=config_entry.options.get(CONF_ID, config_entry.data.get(CONF_ID)),
                                                token=config_entry.options.get(CONF_TOKEN, config_entry.data.get(CONF_TOKEN)),
                                                web_session=async_get_clientsession(hass),
                                                lang=lang)
        else:
            self.mode = LAN
            self.bridge = GoeChargerApiV2Bridge(host=config_entry.options.get(CONF_HOST, config_entry.data.get(CONF_HOST)),
                                                serial=None,
                                                token=None,
                                                web_session=async_get_clientsession(hass),
                                                lang=lang)

        global SCAN_INTERVAL
        SCAN_INTERVAL = timedelta(seconds=config_entry.options.get(CONF_SCAN_INTERVAL,
                                                                   config_entry.data.get(CONF_SCAN_INTERVAL, 5)))
        self._serial = config_entry.data.get(CONF_ID)

        self.lang_map = None
        if lang in TRANSLATIONS:
            self.lang_map = TRANSLATIONS[lang]
        else:
            self.lang_map = TRANSLATIONS["en"]

        # config_entry only need for providing the '_device_info_dict'...
        self._config_entry = config_entry

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)

    # Callable[[Event], Any]
    def __call__(self, evt: Event) -> bool:
        _LOGGER.debug(f"Event arrived: {evt}")
        return True

    def clear_data(self):
        self.bridge.clear_data()
        self.data.clear()

    async def _async_update_data(self) -> dict:
        """Update data via library."""
        try:
            # if self.data is not None:
            #    _LOGGER.debug(f"number of fields before query: {len(self.data)} ")
            # result = await self.bridge.read_all()
            # _LOGGER.debug(f"number of fields after query: {len(result)}")
            # return result

            return await self.bridge.read_all()

        except UpdateFailed as exception:
            raise UpdateFailed() from exception
        except Exception as other:
            _LOGGER.error(f"unexpected: {other}")
            raise UpdateFailed() from other

    # async def async_write_tags(self, kv_pairs: Collection[Tuple[WKHPTag, Any]]) -> dict:
    #    """Get data from the API."""
    #    ret = await self.bridge.async_write_values(kv_pairs)
    #    return ret

    async def async_write_key(self, key: str, value, entity: Entity = None) -> dict:
        """Update single data"""
        result = await self.bridge.write_value_to_key(key, value)
        _LOGGER.debug(f"write result: {result}")

        if key in result:
            self.data[key] = result[key]
        else:
            _LOGGER.error(f"could not write value: '{value}' to: {key} result was: {result}")

        if entity is not None:
            entity.async_schedule_update_ha_state(force_refresh=True)

        # since we do not force an update when setting PV surplus data, we 'patch' internally our values
        if key == Tag.IDS.key:
            self.data = self.bridge._versions | self.bridge._states | self.bridge._config
            self.async_update_listeners()

        return result

    async def read_versions(self):
        await self.bridge.read_versions()
        if self.mode == LAN:
            self._device_info_dict = {
                "identifiers": {(
                    DOMAIN,
                    self._config_entry.data.get(CONF_HOST),
                    self._config_entry.title)},
                "manufacturer": MANUFACTURER,
                "suggested_area": "Garage",
                "name": self._config_entry.title,
                "model": self._config_entry.data.get(CONF_TYPE),
                "sw_version": self.bridge._versions[Tag.FWV.key]
                # hw_version
            }
        else:
            self._device_info_dict = {
                "identifiers": {(
                    DOMAIN,
                    self._config_entry.data.get(CONF_TOKEN),
                    self._config_entry.title)},
                "manufacturer": MANUFACTURER,
                "suggested_area": "Garage",
                "name": self._config_entry.title,
                "model": self._config_entry.data.get(CONF_TYPE),
                "sw_version": self.bridge._versions[Tag.FWV.key]
                # hw_version
            }

        # fetching the available cards that are enabled
        self.available_cards_idx = []
        idx = 1
        for a_card in self.bridge._versions[Tag.CARDS.key]:
            if a_card["cardId"]:
                self.available_cards_idx.append(str(idx))
            idx = idx + 1

        _LOGGER.info(f"active cards {self.available_cards_idx}")

        # check for the 16A limiter...
        self.check_for_max_of_16a = self._config_entry.options.get(CONF_11KWLIMIT, False)

        self.limit_to16a = (self.check_for_max_of_16a
                            or self.bridge._versions[Tag.VAR.key] == 11
                            or self.data[Tag.ADI.key])

        if (self.limit_to16a):
            _LOGGER.info(f"LIMIT to 16A is active")

    async def check_for_16a_limit(self, hass, entry_id):
        _LOGGER.debug(f"check relevant entities for 16A limit... in 15sec")
        await asyncio.sleep(15)

        _LOGGER.debug(f"check relevant entities for 16A limit NOW!")
        await check_and_write_to_16a(hass=hass, config_entry_id=entry_id, bridge=self.bridge)


class GoeChargerBaseEntity(Entity):
    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, coordinator: GoeChargerDataUpdateCoordinator, description: EntityDescription) -> None:
        # make sure that we keep the CASE of the key!
        self.data_key = description.key

        if hasattr(description, "idx") and description.idx is not None:
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
            self.entity_id = f"{DOMAIN}.goe_wan_{self.coordinator._serial}_{self._attr_translation_key}"
        else:
            self.entity_id = f"{DOMAIN}.goe_{self.coordinator._serial}_{self._attr_translation_key}"

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
        return self.entity_id

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
