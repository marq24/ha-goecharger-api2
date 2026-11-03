import logging
from dataclasses import replace
from typing import Final

from homeassistant.components.number import (
    DOMAIN as NUMBER_DOMAIN,
    SERVICE_SET_VALUE,
    ATTR_VALUE,
   NumberEntity
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.goecharger_api2.pygoecharger_ha import INTG_TYPE
from . import GoeChargerDataUpdateCoordinator, GoeChargerBaseEntity, Tag, WAN, LAN
from .const import DOMAIN, NUMBER_SENSORS, CONTROLLER_NUMBER_SENSORS, ExtNumberEntityDescription
from .pygoecharger_ha.keys import is_finite_number

_LOGGER = logging.getLogger(__name__)

KEYS_THAT_NEED_TO_BE_CHECKED_FOR_MIN_MAX: Final = [Tag.AMP.key, Tag.TCL.key]

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, add_entity_cb: AddEntitiesCallback):
    _LOGGER.debug("NUMBER async_setup_entry")
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    entities = []

    if coordinator.intg_type == INTG_TYPE.CHARGER.value:
        for description in NUMBER_SENSORS:
            if description.check_16a_limit and coordinator.limit_to16a:
                # when there is a loadbalancer group id set and the key is LOT, we do not overwrite the
                # native_max_value... [since the overall max value in the group can be larger than 16A!]
                if not (coordinator.is_loadbalancer_group_id_set and description.key in [Tag.LOT.key]):
                    description = replace(description, native_max_value = 16)
                else:
                    _LOGGER.debug(f"NUMBER async_setup_entry: not overwriting native_max_value for key {description.key} - {description.idx}")

            entity = GoeChargerNumber(coordinator, description)
            entities.append(entity)
    else:
        for description in CONTROLLER_NUMBER_SENSORS:
            entity = GoeChargerNumber(coordinator, description)
            entities.append(entity)

    add_entity_cb(entities)


class GoeChargerNumber(GoeChargerBaseEntity, NumberEntity):
    def __init__(self, coordinator: GoeChargerDataUpdateCoordinator, description: ExtNumberEntityDescription):
        super().__init__(entity_type=Platform.NUMBER, coordinator=coordinator, description=description)

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()

        # currently only the 'Tag.AMP.key' and 'Tag.TCL.key' entities need to be modified
        # based on MIN and MAX AMP settings... [have in mind that 'data_key' is not unique !!!]
        if self.data_key in KEYS_THAT_NEED_TO_BE_CHECKED_FOR_MIN_MAX:
            self.coordinator.entities[self.data_key] = self


    @property
    def native_value(self):
        try:
            value = None
            if self.coordinator.data is not None:
                value = (self.coordinator.data or {}).get(self.data_key)
                if self.entity_description.idx is not None:
                    # this is still some sort of silly access...
                    value = value[self.entity_description.idx]

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

        # we must we check min/max of AMP (based on AMA and MCA)
        self.check_entity_min_max_bounds(value)
        return value


    async def async_set_native_value(self, value) -> None:
        validate_write_success = False
        if self.tag is not None:
            validate_write_success =  hasattr(self.tag, "tag_func_validate_output")

        # _LOGGER.info(f"set_native {self.data_key} {value} idx? {self.entity_description.idx}) factor: {self.entity_description.factor} float? {self.entity_description.handle_as_float}")
        try:
            desc = self.entity_description
            if int(value) == 0 and desc.write_zero_as_null:
                final_value_to_set = None
            elif desc.factor and desc.factor > 0:
                final_value_to_set = int(value * desc.factor)
            elif desc.handle_as_float:
                final_value_to_set = float(value)
            else:
                final_value_to_set = int(value)

            if desc.idx is None:
                final_object_to_write = final_value_to_set
            else:
                final_object_to_write = self.coordinator.data[self.data_key]
                final_object_to_write[desc.idx] = final_value_to_set

            result = await self.coordinator.async_write_key(self.data_key, final_object_to_write, self, require_ack=validate_write_success)

            # must we verify that the setting of the value was successful?
            if validate_write_success:
                if result:
                    self.tag.tag_func_validate_output(result, value)
                else:
                    raise ValueError(f"No 'result' returned from write operation for key {self.data_key} - cannot validate output value {value}")

        except ValueError as ve:
            raise HomeAssistantError(f"ValueError when set value {value}: for {self.data_key}") from ve

    def check_entity_min_max_bounds(self, value):
        # the bth entities that restrict the min/max bounds are AMA and MCA (max & min charging current)
        if self.data_key in [Tag.AMA.key, Tag.MCA.key]:
            if not is_finite_number(value):
                _LOGGER.debug(f"check_entity_min_max_bounds(): '{value}' is not a number")
                return

            filtered_entities = {k: self.coordinator.entities[k] for k in KEYS_THAT_NEED_TO_BE_CHECKED_FOR_MIN_MAX if k in self.coordinator.entities}
            for a_entity in filtered_entities.values():
                if a_entity:
                    set_new_value = None
                    is_max_mode = self.data_key == Tag.AMA.key
                    attr_name = "_attr_native_max_value" if is_max_mode else "_attr_native_min_value"

                    current_attr_val = getattr(a_entity, attr_name, None)
                    if current_attr_val != value:
                        _LOGGER.debug(f"native_value(): {a_entity} setting {("max" if is_max_mode else "min")} -> {value}")
                        setattr(a_entity, attr_name, value)

                        if is_finite_number(a_entity.native_value):
                            if (a_entity.native_value > value) if is_max_mode else (a_entity.native_value < value):
                                set_new_value = value

                    if set_new_value:
                        _LOGGER.debug(f"native_value(): {a_entity} setting value -> {set_new_value}")
                        self.hass.async_create_task(
                            self.hass.services.async_call(
                                domain=NUMBER_DOMAIN,
                                service=SERVICE_SET_VALUE,
                                service_data= {
                                    ATTR_ENTITY_ID: a_entity.entity_id,
                                    ATTR_VALUE: set_new_value,
                                },
                                blocking=False,
                            )
                        )