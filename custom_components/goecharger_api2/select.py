import logging

from custom_components.goecharger_api2 import GoeChargerDataUpdateCoordinator, GoeChargerBaseEntity
from custom_components.goecharger_api2.const import DOMAIN, SELECT_SENSORS, CONTROLLER_SELECT_SENSORS, \
    ExtSelectEntityDescription
from custom_components.goecharger_api2.pygoecharger_ha import INTG_TYPE
from custom_components.goecharger_api2.pygoecharger_ha.const import CT_VALUES, CT_VALUES_MAP
from custom_components.goecharger_api2.pygoecharger_ha.keys import Tag
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

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
        super().__init__(entity_type=Platform.SELECT, coordinator=coordinator, description=description)

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

            if self.data_key == Tag.CT.key:
                value = value.lower()

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
                        if self.entity_description.key in [Tag.SCH_WEEK.key, Tag.SCH_SATUR.key, Tag.SCH_SUND.key]:
                            # 1. we must post the new value as integer
                            option = int(option)
                            # 2. we must remove the 'second' object from the 'begin' & 'end' time information
                            # this is quite ridiculous!
                            for interval in obj["ranges"]:
                                if "second" in interval["begin"]:
                                    del interval["begin"]["second"]
                                if "second" in interval["end"]:
                                    del interval["end"]["second"]

                        obj[self.entity_description.idx] = option

                    await self.coordinator.async_write_key(self.data_key, obj, self)
                else:
                    _LOGGER.warning(f"async_select_option: for {self.data_key} with index not found in data: {len(self.coordinator.data)}")
                    return "unavailable"
            else:
                if str(option) == "null":
                    await self.coordinator.async_write_key(self.data_key, None, self)

                else:
                    if self.data_key == Tag.CT.key:
                        # quite a quick hack - since normally we write multiple values via a service...
                        args = {Tag.CT.key: '"'+str(CT_VALUES_MAP[option])+'"'}

                        # simulateUnpluggingShort (su) false, when Default, true otherwise
                        if option == CT_VALUES.DEFAULT.value:
                            args[Tag.SU.key] = str(False).lower()
                        else:
                            args[Tag.SU.key] = str(True).lower()

                        # setting the Minimum charging current (mca)
                        if option == CT_VALUES.RENAULTZOE.value:
                            # Zoe need's 10 as value
                            args[Tag.MCA.key] = str(10).lower()
                        else:
                            args[Tag.MCA.key] = str(6).lower()

                        # finally wringing the key...
                        await self.coordinator.async_write_multiple_keys(args, self.data_key, option, self)

                    else:
                        await self.coordinator.async_write_key(self.data_key, int(option), self)
        except ValueError:
            return "unavailable"
