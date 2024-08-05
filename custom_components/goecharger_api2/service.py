import asyncio
import datetime
import logging

from homeassistant.core import ServiceCall, HomeAssistant
from homeassistant.config_entries import ConfigEntry

from custom_components.goecharger_api2.pygoecharger_ha.keys import Tag

_LOGGER: logging.Logger = logging.getLogger(__package__)

_COORDINATOR_PER_CONFIGENTRYID_MAP = {}

class GoeChargerApiV2Service():
    def __init__(self, hass: HomeAssistant, config: ConfigEntry, coordinator):  # pylint: disable=unused-argument
        """Initialize the sensor."""
        self._hass = hass
        self._config = config
        _COORDINATOR_PER_CONFIGENTRYID_MAP[config.entry_id] = coordinator
        self._stop_in_progress = False

    async def set_pv_data(self, call: ServiceCall):
        config_id = call.data.get('configid', None)
        if config_id is None:
            coordinator = next(iter(_COORDINATOR_PER_CONFIGENTRYID_MAP.values()))
        else:
            coordinator = _COORDINATOR_PER_CONFIGENTRYID_MAP[config_id]
        _LOGGER.debug(f"Provided config_id: {config_id} -> using {coordinator.name} serial: {coordinator._serial}")

        pgrid = call.data.get('pgrid', None)
        ppv = call.data.get('ppv', 0)
        pakku = call.data.get('pakku', 0)
        if pgrid is not None and isinstance(pgrid, (int, float)):
            if not isinstance(ppv, (int, float)):
                ppv = 0
            if not isinstance(pakku, (int, float)):
                pakku = 0

            payload = {
                "pGrid": float(pgrid),
                "pPv": float(ppv),
                "pAkku": float(pakku)
            }
            _LOGGER.debug(f"Service set PV data: {payload}")
            try:
                resp = await coordinator.async_write_key(Tag.IDS.key, payload)
                if call.return_response:
                    return {
                        "success": "true",
                        "date": str(datetime.datetime.now().time()),
                        "response": resp
                    }

            except ValueError as exc:
                if call.return_response:
                    return {"error": str(exc), "date": str(datetime.datetime.now().time())}

        if call.return_response:
            return {"error": "No Grid Power provided (or false data)", "date": str(datetime.datetime.now().time())}

    async def stop_charging(self, call: ServiceCall):
        if not self._stop_in_progress:
            self._stop_in_progress = True
            _LOGGER.debug(f"Force STOP_CHARGING")

            config_id = call.data.get('configid', None)
            if config_id is None:
                coordinator = next(iter(_COORDINATOR_PER_CONFIGENTRYID_MAP.values()))
            else:
                coordinator = _COORDINATOR_PER_CONFIGENTRYID_MAP[config_id]
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

            except ValueError as exc:
                if call.return_response:
                    return {"error": str(exc), "date": str(datetime.datetime.now().time())}

        else:
            if call.return_response:
                return {"error": "A STOP_CHARGING request is already in progress", "date": str(datetime.datetime.now().time())}
