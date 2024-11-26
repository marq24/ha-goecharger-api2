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
            new_options = ["null", "0"] + coordinator.available_cards_idx
            # ok we need to create a new entity description with the new options...
            # [since ExtSelectEntityDescription is frozen]
            description = ExtSelectEntityDescription (
                key = description.key,
                device_class = description.device_class,
                entity_category = description.entity_category,
                entity_registry_enabled_default = description.entity_registry_enabled_default,
                entity_registry_visible_default = description.entity_registry_visible_default,
                force_update = description.force_update,
                icon = description.icon,
                has_entity_name = description.has_entity_name,
                name = description.name,
                translation_key = description.translation_key,
                translation_placeholders = description.translation_placeholders,
                unit_of_measurement = description.unit_of_measurement,
                options = new_options,
                idx = description.idx,
            )
        super().__init__(coordinator=coordinator, description=description)

    @property
    def current_option(self) -> str | None:
        try:
            if self.entity_description.idx is not None:
                if self.data_key in self.coordinator.data:
                    value = self.coordinator.data[self.data_key][self.entity_description.idx]
                else:
                    _LOGGER.warning(f"current_option: for {self.data_key} with index not found in data: {len(self.coordinator.data)}")
                    return "unavailable"
            else:
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

            if self.entity_description.idx is not None:
                if self.data_key in self.coordinator.data:
                    # we have to write all values of the object... [not only the set one]
                    obj = self.coordinator.data[self.data_key]
                    if str(option) == "null":
                        obj[self.entity_description.idx] = None
                    else:
                        obj[self.entity_description.idx] = option

                    await self.coordinator.async_write_key(self.data_key, obj, self)
                else:
                    _LOGGER.warning(f"async_select_option: for {self.data_key} with index not found in data: {len(self.coordinator.data)}")
                    return "unavailable"
            else:
                if str(option) == "null":
                    await self.coordinator.async_write_key(self.data_key, None, self)
                else:
                    await self.coordinator.async_write_key(self.data_key, int(option), self)
        except ValueError:
            return "unavailable"
