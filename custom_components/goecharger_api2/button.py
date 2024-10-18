import logging

from custom_components.goecharger_api2.pygoecharger_ha import INTG_TYPE
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from . import GoeChargerDataUpdateCoordinator, GoeChargerBaseEntity
from .const import DOMAIN, BUTTONS, CONTROLLER_BUTTONS, ExtButtonEntityDescription

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, add_entity_cb: AddEntitiesCallback):
    _LOGGER.debug("BUTTON async_setup_entry")
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    entities = []

    if coordinator.intg_type == INTG_TYPE.CHARGER.value:
        for description in BUTTONS:
            entity = GoeChargerApiV2Button(coordinator, description)
            entities.append(entity)
    else:
        for description in CONTROLLER_BUTTONS:
            entity = GoeChargerApiV2Button(coordinator, description)
            entities.append(entity)

    add_entity_cb(entities)


class GoeChargerApiV2Button(GoeChargerBaseEntity, ButtonEntity):
    def __init__(self, coordinator: GoeChargerDataUpdateCoordinator, description: ExtButtonEntityDescription):
        super().__init__(coordinator=coordinator, description=description)

    async def async_press(self, **kwargs):
        try:
            await self.coordinator.async_write_key(self.data_key, self.entity_description.payload, self)
        except ValueError:
            return "unavailable"