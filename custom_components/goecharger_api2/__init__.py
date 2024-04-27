import asyncio
import json
import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_TYPE, CONF_ID, CONF_SCAN_INTERVAL
from homeassistant.core import Config, Event
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as config_val
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import Entity, EntityDescription
from homeassistant.helpers.typing import UNDEFINED, UndefinedType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.goecharger_api2.pygoecharger_ha import GoeChargerApiV2Bridge, TRANSLATIONS
from custom_components.goecharger_api2.pygoecharger_ha.keys import Tag
from .const import (
    NAME,
    DOMAIN,
    MANUFACTURER,
    PLATFORMS,
    STARTUP_MESSAGE,
    SERVICE_SET_HOLIDAY,
    SERVICE_SET_SCHEDULE_DATA,
    SERVICE_SET_DISINFECTION_START_TIME,
    SERVICE_GET_ENERGY_BALANCE,
    SERVICE_GET_ENERGY_BALANCE_MONTHLY

)

_LOGGER: logging.Logger = logging.getLogger(__package__)

SCAN_INTERVAL = timedelta(seconds=10)
CONFIG_SCHEMA = config_val.removed(DOMAIN, raise_if_present=False)


async def async_setup(hass: HomeAssistant, config: Config):  # pylint: disable=unused-argument
    """Set up this integration using YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    if DOMAIN not in hass.data:
        value = "UNKOWN"
        try:
            basepath = __file__[:-11]
            with open(f"{basepath}manifest.json") as f:
                manifest = json.load(f)
                value = manifest["version"]
        except:
            pass
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

    # ok we are done...
    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    unload_ok = all(await asyncio.gather(*[
        hass.config_entries.async_forward_entry_unload(config_entry, platform)
        for platform in PLATFORMS
    ]))

    if unload_ok:
        if DOMAIN in hass.data and config_entry.entry_id in hass.data[DOMAIN]:
            # even if waterkotte does not support logout... I code it here...
            coordinator = hass.data[DOMAIN][config_entry.entry_id]
            coordinator.clear_data()
            hass.data[DOMAIN].pop(config_entry.entry_id)

        # hass.services.async_remove(DOMAIN, SERVICE_SET_HOLIDAY)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Reload config entry."""
    if await async_unload_entry(hass, config_entry):
        await asyncio.sleep(2)
        await async_setup_entry(hass, config_entry)


class GoeChargerDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, config_entry):
        lang = hass.config.language.lower()
        self.name = config_entry.title
        self.bridge = GoeChargerApiV2Bridge(host=config_entry.options.get(CONF_HOST, config_entry.data.get(CONF_HOST)),
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
            #if self.data is not None:
            #    _LOGGER.debug(f"number of fields before query: {len(self.data)} ")
            # result = await self.bridge.read_all()
            #_LOGGER.debug(f"number of fields after query: {len(result)}")
            #return result

            return await self.bridge.read_all()

        except UpdateFailed as exception:
            raise UpdateFailed() from exception
        except Exception as other:
            _LOGGER.error(f"unexpected: {other}")
            raise UpdateFailed() from other

    #async def async_write_tags(self, kv_pairs: Collection[Tuple[WKHPTag, Any]]) -> dict:
    #    """Get data from the API."""
    #    ret = await self.bridge.async_write_values(kv_pairs)
    #    return ret

    async def async_write_key(self, key: str, value, entity: Entity = None):
        """Update single data"""
        result = await self.bridge.write_value_to_key(key, value)
        _LOGGER.debug(f"write result: {result}")

        if key in result:
            self.data[key] = result[key]
        else:
            _LOGGER.error(f"could not write value: '{value}' to: {key} result was: {result}")

        if entity is not None:
            entity.async_schedule_update_ha_state(force_refresh=True)

    async def read_versions(self):
        await self.bridge.read_versions()
        self._device_info_dict = {
            "identifiers": {
                ("DOMAIN", DOMAIN),
                ("SERIAL", self._serial),
                ("IP", self._config_entry.options.get(CONF_HOST, self._config_entry.data.get(CONF_HOST))),
            },
            "manufacturer": MANUFACTURER,
            "suggested_area": "Garage",
            "name": NAME,
            "model": self._config_entry.data.get(CONF_TYPE),
            "sw_version": self.bridge._versions[Tag.FWV.key]
        }
        # hw_version


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
        else:
            self._attr_translation_key = self.data_key.lower()

        self.entity_description = description
        self.coordinator = coordinator
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
