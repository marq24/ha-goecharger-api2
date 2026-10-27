import asyncio
import datetime
import logging
import math

from numbers import Number

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import ServiceCall, HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.goecharger_api2.const import WAN
from custom_components.goecharger_api2.pygoecharger_ha.const import INTG_TYPE
from custom_components.goecharger_api2.pygoecharger_ha.keys import Tag

_LOGGER: logging.Logger = logging.getLogger(__package__)

_COORDINATOR_PER_CONFIG_ENTRY_ID_MAP: dict[str, DataUpdateCoordinator] = {}

def _is_finite_number(value) -> bool:
    """NaN and infinity are Numbers, but would be sent to the charger as invalid JSON."""
    if not isinstance(value, Number):
        return False
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError, OverflowError):
        return False

def add_config_entry_to_service(config: ConfigEntry, coordinator: DataUpdateCoordinator):
    global _COORDINATOR_PER_CONFIG_ENTRY_ID_MAP
    _COORDINATOR_PER_CONFIG_ENTRY_ID_MAP[config.entry_id] = coordinator
    _LOGGER.debug(f"add_config_entry_to_service(): Added config entry {config.entry_id} to _COORDINATOR_PER_CONFIG_ENTRY_ID_MAP now: {len(_COORDINATOR_PER_CONFIG_ENTRY_ID_MAP)} entries")

def remove_config_entry_from_service(config: ConfigEntry):
    global _COORDINATOR_PER_CONFIG_ENTRY_ID_MAP
    if config.entry_id in _COORDINATOR_PER_CONFIG_ENTRY_ID_MAP:
        _COORDINATOR_PER_CONFIG_ENTRY_ID_MAP.pop(config.entry_id)
        _LOGGER.debug(f"remove_config_entry_from_service(): Removed config entry {config.entry_id} from _COORDINATOR_PER_CONFIG_ENTRY_ID_MAP now: {len(_COORDINATOR_PER_CONFIG_ENTRY_ID_MAP)} entries")

class GoeChargerApiV2Service():
    def __init__(self, hass: HomeAssistant, config: ConfigEntry, coordinator: DataUpdateCoordinator):  # pylint: disable=unused-argument
        """Initialize the sensor."""
        self._hass = hass
        self._config = config
        # when we create a new instance of the service, we will reset the map, so that only
        # the last config entry is used for the service calls
        global _COORDINATOR_PER_CONFIG_ENTRY_ID_MAP
        _COORDINATOR_PER_CONFIG_ENTRY_ID_MAP = {}
        _COORDINATOR_PER_CONFIG_ENTRY_ID_MAP[config.entry_id] = coordinator
        _LOGGER.debug(f"__init__(): Added config entry {config.entry_id} to _COORDINATOR_PER_CONFIG_ENTRY_ID_MAP now: {len(_COORDINATOR_PER_CONFIG_ENTRY_ID_MAP)} entries")

        self._stop_in_progress = False

    async def set_pv_data(self, call: ServiceCall):
        config_id, coordinator = self.get_coordinator(call)
        _LOGGER.debug(f"Service-set_pv_data(): Provided config_id: {config_id} -> using {coordinator.name} serial: {coordinator._serial}")

        # before we're going to 'post' any data to the cloud, we will check if there is ANY vehicle connected
        if coordinator.intg_type == INTG_TYPE.CHARGER.value and coordinator.mode == WAN:
            # see also binary_sensor.py.is_on()
            a_car_state = coordinator.data.get(Tag.CAR_CONNECTED.key, -1)
            if isinstance(a_car_state, Number):
                if int(a_car_state) < 2:
                    _LOGGER.debug(f"Service-set_pv_data(): No CAR CONNECTED to the Wallbox: API returned 'car' value '{a_car_state}'")
                    if call.return_response:
                        return {"error": f"No CAR CONNECTED to the Wallbox: API returned 'car' value '{a_car_state}'"}
                    else:
                        return None

        pgrid = call.data.get('pgrid', None)
        ppv = call.data.get('ppv', 0)
        pakku = call.data.get('pakku', 0)
        if pgrid is not None and isinstance(pgrid, Number):
            if not _is_finite_number(ppv):
                ppv = 0
            if not _is_finite_number(pakku):
                pakku = 0

            payload = {
                "pGrid": float(pgrid),
                "pPv": float(ppv),
                "pAkku": float(pakku)
            }
            _LOGGER.debug(f"Service-set_pv_data(): set PV data: {payload}")
            try:
                resp = await coordinator.async_write_key(Tag.IDS.key, payload)
                if call.return_response:
                    return {
                        "success": "true",
                        "date": str(datetime.datetime.now().time()),
                        "response": resp
                    }

            except (ValueError, TypeError) as exc:
                if call.return_response:
                    return {"error": str(exc), "date": str(datetime.datetime.now().time())}

        if call.return_response:
            return {"error": "No Grid Power provided (or false data)", "date": str(datetime.datetime.now().time())}

    async def stop_charging(self, call: ServiceCall):
        if not self._stop_in_progress:
            config_id, coordinator = self.get_coordinator(call)
            self._stop_in_progress = True
            _LOGGER.debug(f"Force STOP_CHARGING")
            _LOGGER.debug(f"Provided config_id: {config_id} -> using {coordinator.name} serial: {coordinator._serial}")
            try:
                resp = await coordinator.async_write_key(Tag.FRC.key, 1)
                if Tag.FRC.key in resp:
                    _LOGGER.debug(f"STOP_CHARGING: waiting for 5 minutes...")
                    await asyncio.sleep(300)
                    _LOGGER.debug(f"STOP_CHARGING: 5 minutes are over... disable charging LOCK again")

                    resp = await coordinator.async_write_key(Tag.FRC.key, 0)

                    self._stop_in_progress = False
                    if call.return_response:
                        return {
                            "success": "true",
                            "date": str(datetime.datetime.now().time()),
                            "response": resp
                        }

                else:
                    _LOGGER.debug(f"response does not contain {Tag.FRC.key}: {resp}")

                    self._stop_in_progress = False
                    if call.return_response:
                        return {"error": "A STOP_CHARGING request could not be send", "date": str(datetime.datetime.now().time())}

            except (ValueError, TypeError) as exc:
                if call.return_response:
                    return {"error": str(exc), "date": str(datetime.datetime.now().time())}

        else:
            if call.return_response:
                return {"error": "A STOP_CHARGING request is already in progress", "date": str(datetime.datetime.now().time())}

    def get_coordinator(self, call):
        global _COORDINATOR_PER_CONFIG_ENTRY_ID_MAP
        config_id = call.data.get('configid', None)
        if config_id is None:
            coordinator = next(iter(_COORDINATOR_PER_CONFIG_ENTRY_ID_MAP.values()))
        else:
            # Fetch the config entry
            entry = self._hass.config_entries.async_get_entry(config_id)
            # Check if it exists and is not disabled
            if entry is not None and not entry.disabled_by:
                if config_id in _COORDINATOR_PER_CONFIG_ENTRY_ID_MAP:
                    coordinator = _COORDINATOR_PER_CONFIG_ENTRY_ID_MAP[config_id]
                else:
                    _LOGGER.warning(f"get_coordinator(): Provided config_id: {config_id} does not exist in _COORDINATOR_PER_CONFIG_ENTRY_ID_MAP")
                    raise ServiceValidationError(f"The selected goecharger_api2 config entry ({config_id}) is not in the internal _COORDINATOR_PER_CONFIG_ENTRY_ID_MAP dictionary.")
            else:
                _LOGGER.warning(f"get_coordinator(): Provided config_id: {config_id} does not exist or is disabled in config entries")
                raise ServiceValidationError(f"The selected goecharger_api2 config entry ({config_id}) is disabled or invalid.")

        return config_id, coordinator