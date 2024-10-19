import logging

from custom_components.goecharger_api2.pygoecharger_ha import INTG_TYPE
from custom_components.goecharger_api2.pygoecharger_ha.keys import Tag
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from . import GoeChargerDataUpdateCoordinator, GoeChargerBaseEntity
from .const import DOMAIN, SELECT_SENSORS, CONTROLLER_SELECT_SENSORS, ExtSelectEntityDescription

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, add_entity_cb: AddEntitiesCallback):
    _LOGGER.debug("SELECT async_setup_entry")
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    entities = []

    if coordinator.intg_type == INTG_TYPE.CHARGER.value:
        for description in SELECT_SENSORS:
            entity = GoeChargerSelect(coordinator, description)
            entities.append(entity)
    else:
        for description in CONTROLLER_SELECT_SENSORS:
            entity = GoeChargerSelect(coordinator, description)
            entities.append(entity)

    add_entity_cb(entities)


class GoeChargerSelect(GoeChargerBaseEntity, SelectEntity):
    def __init__(self, coordinator: GoeChargerDataUpdateCoordinator, description: ExtSelectEntityDescription):
        if description.key == Tag.TRX.key:
            options = ["null", "0"]
            description.options = options + coordinator.available_cards_idx
        super().__init__(coordinator=coordinator, description=description)

    @property
    def current_option(self) -> str | None:
        try:
            value = self.coordinator.data[self.data_key]
            if value is None or value == "":
                # special handling for tra 'transaction' API key...
                # where None means, that Auth is required
                if self.data_key == Tag.TRX.key:
                    value = "null"
                else:
                    value = 'unknown'
            if isinstance(value, int):
                value = str(value)
        except KeyError:
            value = "unknown"
        except TypeError:
            return None
        return value

    async def async_select_option(self, option: str) -> None:
        try:
            if str(option) == "null":
                await self.coordinator.async_write_key(self.data_key, None, self)
            else:
                await self.coordinator.async_write_key(self.data_key, int(option), self)
        except ValueError:
            return "unavailable"
