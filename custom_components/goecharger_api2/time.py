import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .schedule import add_schedule_rule_entities, create_schedule_rule_times, supports_schedule_rules

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, add_entity_cb: AddEntitiesCallback):
    _LOGGER.debug("TIME async_setup_entry")
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    if supports_schedule_rules(coordinator):
        add_schedule_rule_entities(coordinator, config_entry, add_entity_cb, create_schedule_rule_times)
