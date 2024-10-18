import logging

from custom_components.goecharger_api2.pygoecharger_ha import INTG_TYPE
from custom_components.goecharger_api2.pygoecharger_ha.keys import Tag
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_OFF
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from . import GoeChargerDataUpdateCoordinator, GoeChargerBaseEntity
from .const import DOMAIN, CONF_INTEGRATION_TYPE, BINARY_SENSORS, CONTROLLER_BINARY_SENSORS, \
    ExtBinarySensorEntityDescription

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, add_entity_cb: AddEntitiesCallback):
    _LOGGER.debug("BINARY_SENSOR async_setup_entry")
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    entities = []

    if CONF_INTEGRATION_TYPE in config_entry.data and config_entry.data.get(CONF_INTEGRATION_TYPE) == INTG_TYPE.CONTROLLER.value:
        for description in BINARY_SENSORS:
            entity = GoeChargerApiV2BinarySensor(coordinator, description)
            entities.append(entity)
    else:
        for description in CONTROLLER_BINARY_SENSORS:
            entity = GoeChargerApiV2BinarySensor(coordinator, description)
            entities.append(entity)

    add_entity_cb(entities)


class GoeChargerApiV2BinarySensor(GoeChargerBaseEntity, BinarySensorEntity):
    def __init__(self, coordinator: GoeChargerDataUpdateCoordinator, description: ExtBinarySensorEntityDescription):
        super().__init__(coordinator=coordinator, description=description)
        self._attr_icon_off = self.entity_description.icon_off

    @property
    def is_on(self) -> bool | None:
        try:
            value = None
            if self.coordinator.data is not None:
                if self.data_key in self.coordinator.data:
                    if self.entity_description.idx is not None:
                        # hacking the CAR_CONNECT state... -> "car" > 1
                        if self.data_key == Tag.CAR_CONNECTED.key:
                            value = int(self.coordinator.data[self.data_key]) > 1
                        else:
                            value = self.coordinator.data[self.data_key][self.entity_description.idx]
                    else:
                        value = self.coordinator.data[self.data_key]

                else:
                    if len(self.coordinator.data) > 0:
                        _LOGGER.info(f"is_on: for {self.data_key} not found in data: {len(self.coordinator.data)}")
                if value is None or value == "":
                    value = None

        except IndexError:
            if self.entity_description.idx is not None:
                _LOGGER.debug(f"lc-key: {self.data_key.lower()} value: {value} idx: {self.entity_description.idx} -> {self.coordinator.data[self.data_key]}")
            else:
                _LOGGER.debug(f"lc-key: {self.data_key.lower()} caused IndexError")
            value = None
        except KeyError:
            _LOGGER.warning(f"is_on caused KeyError for: {self.data_key}")
            value = None
        except TypeError:
            return None

        if not isinstance(value, bool):
            if isinstance(value, str):
                # parse anything else then 'on' to False!
                if value.lower() == 'on':
                    value = True
                else:
                    value = False
            else:
                value = False

        return value

    @property
    def icon(self):
        """Return the icon of the sensor."""
        if self._attr_icon_off is not None and self.state == STATE_OFF:
            return self._attr_icon_off
        else:
            return super().icon
