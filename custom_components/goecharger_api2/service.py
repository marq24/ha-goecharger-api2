import datetime
import logging

from homeassistant.core import ServiceCall

from custom_components.goecharger_api2.pygoecharger_ha.keys import Tag

_LOGGER: logging.Logger = logging.getLogger(__package__)


class GoeChargerApiV2Service():
    def __init__(self, hass, config, coordinator):  # pylint: disable=unused-argument
        """Initialize the sensor."""
        self._hass = hass
        self._config = config
        self._coordinator = coordinator

    async def set_pv_data(self, call: ServiceCall):
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
                resp = await self._coordinator.async_write_key(Tag.IDS.key, payload)
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