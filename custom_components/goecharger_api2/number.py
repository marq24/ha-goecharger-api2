import logging

from custom_components.goecharger_api2.pygoecharger_ha import INTG_TYPE
from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from . import GoeChargerDataUpdateCoordinator, GoeChargerBaseEntity
from .const import DOMAIN, NUMBER_SENSORS, CONTROLLER_NUMBER_SENSORS, ExtNumberEntityDescription

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, add_entity_cb: AddEntitiesCallback):
    _LOGGER.debug("NUMBER async_setup_entry")
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    entities = []

    if coordinator.intg_type == INTG_TYPE.CHARGER.value:
        for description in NUMBER_SENSORS:
            entity = GoeChargerNumber(coordinator, description)
            entities.append(entity)
    else:
        for description in CONTROLLER_NUMBER_SENSORS:
            entity = GoeChargerNumber(coordinator, description)
            entities.append(entity)

    add_entity_cb(entities)


class GoeChargerNumber(GoeChargerBaseEntity, NumberEntity):
    def __init__(self, coordinator: GoeChargerDataUpdateCoordinator, description: ExtNumberEntityDescription):
        if description.check_16a_limit and coordinator.limit_to16a:
            # ok we need to create a new entity description with the new options...
            # [since ExtNumberEntityDescription is frozen]
            description = ExtNumberEntityDescription (
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

                max_value = description.max_value,
                min_value = description.min_value,
                mode = description.mode,
                # here is the value, that we overwrite...
                native_max_value = 16,
                native_min_value = description.native_min_value,
                native_step = description.native_step,
                native_unit_of_measurement = description.native_unit_of_measurement,
                step = description.step,

                write_zero_as_null = description.write_zero_as_null,
                handle_as_float = description.handle_as_float,
                factor = description.factor,
                idx = description.idx,
                check_16a_limit = description.check_16a_limit
            )
        super().__init__(coordinator=coordinator, description=description)

    @property
    def native_value(self):
        try:
            if self.entity_description.idx is not None:
                value = self.coordinator.data[self.data_key][self.entity_description.idx]
            else:
                value = self.coordinator.data[self.data_key]

            if value is None or value == "":
                return "unknown"
            elif self.entity_description.handle_as_float is not None and self.entity_description.handle_as_float:
                if self.entity_description.factor is not None and self.entity_description.factor > 0:
                    value = float(int(value) / self.entity_description.factor)
                else:
                    value = float(value)
            elif self.entity_description.factor is not None and self.entity_description.factor > 0:
                value = int(int(value) / self.entity_description.factor)

        except KeyError:
            return "unknown"

        except TypeError:
            return None

        return value

    async def async_set_native_value(self, value) -> None:
        # _LOGGER.info(f"set_native {self.data_key} {value} idx? {self.entity_description.idx}) factor: {self.entity_description.factor} float? {self.entity_description.handle_as_float}")
        try:
            if self.entity_description.idx is not None:
                # we have to write all values of the object... [not only the set one]
                obj = self.coordinator.data[self.data_key]

                if int(value) == 0 and self.entity_description.write_zero_as_null is not None and self.entity_description.write_zero_as_null:
                    obj[self.entity_description.idx] = None
                elif self.entity_description.factor is not None and self.entity_description.factor > 0:
                    # no special handling for 'handle_as_float' here - since the float's just exist in the GUI... if the
                    # backend these values are (keep my fingers crossed) always int's
                    obj[self.entity_description.idx] = int(value * self.entity_description.factor)
                elif self.entity_description.handle_as_float is not None and self.entity_description.handle_as_float:
                    obj[self.entity_description.idx] = float(value)
                else:
                    # we will write all numbers as integer's [no decimal's/fractions!!!]
                    obj[self.entity_description.idx] = int(value)

                await self.coordinator.async_write_key(self.data_key, obj, self)

            else:
                if int(value) == 0 and self.entity_description.write_zero_as_null is not None and self.entity_description.write_zero_as_null:
                    await self.coordinator.async_write_key(self.data_key, None, self)
                elif self.entity_description.factor is not None and self.entity_description.factor > 0:
                    # no special handling for 'handle_as_float' here - since the float's just exist in the GUI... if the
                    # backend these values are (keep my fingers crossed) always int's
                    await self.coordinator.async_write_key(self.data_key, int(value * self.entity_description.factor), self)
                elif self.entity_description.handle_as_float is not None and self.entity_description.handle_as_float:
                    await self.coordinator.async_write_key(self.data_key, float(value), self)
                else:
                    # we will write all numbers as integer's [no decimal's/fractions!!!]
                    await self.coordinator.async_write_key(self.data_key, int(value), self)

        except ValueError:
            return "unavailable"
