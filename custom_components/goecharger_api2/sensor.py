import logging
import re
from datetime import datetime, time
from typing import Final

from custom_components.goecharger_api2.pygoecharger_ha import INTG_TYPE
from custom_components.goecharger_api2.pygoecharger_ha.keys import Tag
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from . import GoeChargerDataUpdateCoordinator, GoeChargerBaseEntity
from .const import DOMAIN, CONF_INTEGRATION_TYPE, SENSOR_SENSORS, CONTROLLER_SENSOR_SENSORS, ExtSensorEntityDescription

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, add_entity_cb: AddEntitiesCallback):
    _LOGGER.debug("SENSOR async_setup_entry")
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    entities = []

    if CONF_INTEGRATION_TYPE in config_entry.data and config_entry.data.get(CONF_INTEGRATION_TYPE) == INTG_TYPE.CONTROLLER.value:
        for description in SENSOR_SENSORS:
            entity = GoeChargerSensor(coordinator, description)
            entities.append(entity)
    else:
        for description in CONTROLLER_SENSOR_SENSORS:
            entity = GoeChargerSensor(coordinator, description)
            entities.append(entity)

    add_entity_cb(entities)

CC_P1: Final = re.compile(r"(.)([A-Z][a-z]+)")
CC_P2: Final = re.compile(r"([a-z0-9])([A-Z])")

class GoeChargerSensor(GoeChargerBaseEntity, SensorEntity, RestoreEntity):

    def __init__(self, coordinator: GoeChargerDataUpdateCoordinator, description: ExtSensorEntityDescription):
        super().__init__(coordinator=coordinator, description=description)

    @staticmethod
    def _camel_to_snake(a_key: str):
        a_key = re.sub(CC_P1, r'\1 \2', a_key)
        return re.sub(CC_P2, r'\1 \2', a_key).lower()

    @property
    def state(self):
        # for SensorDeviceClass.DATE we will use out OWN 'state' render impl
        if self.entity_description.device_class == SensorDeviceClass.DATE:
            value = self.native_value
            if value is None:
                value = "unknown"
            return  value
        else:
            return SensorEntity.state.fget(self)

    @property
    def native_value(self):
        try:
            if self.entity_description.idx is not None:
                value = self.coordinator.data[self.data_key][self.entity_description.idx]
            elif self.data_key == Tag.CLL.key:
                # very special handling for the cll attribute - which is actually a json object that might should
                # be parsed to separate sensors - but for now we just create a string list
                value = ""
                for a_key in self.coordinator.data[self.data_key]:
                    a_map_key = f"{self.data_key.lower()}_{a_key.lower()}"
                    if  a_map_key in self.coordinator.lang_map:
                        value = f"{value}, {self.coordinator.lang_map[a_map_key]}: {self.coordinator.data[self.data_key][a_key]}"
                    else:
                        value = f"{value}, {self._camel_to_snake(a_key)}: {self.coordinator.data[self.data_key][a_key]}"

                value = value[2:]
            else:
                value = self.coordinator.data[self.data_key]

                if value is None or len(str(value)) == 0:
                    value = None
                else:
                    if self.entity_description.lookup is not None:
                        if self.data_key.lower() in self.coordinator.lang_map:
                            value = self.coordinator.lang_map[self.data_key.lower()][value]
                        else:
                            _LOGGER.warning(f"{self.data_key} not found in translations")
                    else:
                        # self.entity_description.lookup values are always 'strings' - so there we should not
                        # have an additional features like 'factor' or  'differential_base_key'
                        is_int_value = isinstance(value, int)

                        # the timestamp values of the go-eCharger are based on the reboot time stamp...
                        # so we have to subtract these values!
                        if is_int_value:
                            if self.entity_description.differential_base_key is not None:
                                differential_base = self.coordinator.data[self.entity_description.differential_base_key]
                                if differential_base is not None and int(differential_base) > 0:
                                    value = differential_base - int(value)

                            if self.entity_description.factor is not None and self.entity_description.factor > 0:
                                value = int(int(value) / self.entity_description.factor)

                        if isinstance(value, datetime):
                            return value.isoformat(sep=' ', timespec="minutes")
                        elif isinstance(value, time):
                            return value.isoformat(timespec="minutes")
                        elif isinstance(value, bool):
                            if value is True:
                                value = "on"
                            elif value is False:
                                value = "off"

        except IndexError:
            if self.entity_description.lookup is not None:
                _LOGGER.debug(f"lc-key: {self.data_key.lower()} value: {value} -> {self.coordinator.lang_map[self.data_key.lower()]}")
            else:
                _LOGGER.debug(f"lc-key: {self.data_key.lower()} caused IndexError")
            value = None
        except (KeyError, TypeError):
            value = None

        # final return statement...
        return value
