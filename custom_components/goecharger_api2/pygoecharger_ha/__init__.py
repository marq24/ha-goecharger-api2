import asyncio
import json
import logging
import random
from json import JSONDecodeError
from time import time

from aiohttp import ClientResponseError
from packaging.version import Version

from custom_components.goecharger_api2.pygoecharger_ha.const import (
    TRANSLATIONS,
    INTG_TYPE,
    CAR_VALUES,
    FILTER_SYSTEMS,
    FILTER_VERSIONS,
    FILTER_MIN_STATES,
    FILTER_IDS_ADDON,
    FILTER_TIMES_ADDON,
    FILTER_ALL_STATES,
    FILTER_ALL_CONFIG,

    FILTER_CONTROLER_SYSTEMS,
    FILTER_CONTROLER_VERSIONS,
    FILTER_CONTROLER_MIN_STATES,
    FILTER_CONTROLER_TIMES_ADDON,
    FILTER_CONTROLER_ALL_STATES,
    FILTER_CONTROLER_ALL_CONFIG,
    FILTER_CARDS_ID_CLASSIC,
    FILTER_CARDS_ID_FWV60,
    FILTER_CARDS_ENGY_CLASSIC,
    FILTER_CARDS_ENGY_FWV60,
)
from custom_components.goecharger_api2.pygoecharger_ha.keys import Tag, IS_TRIGGER

_LOGGER: logging.Logger = logging.getLogger(__package__)


class GoeChargerApiV2Bridge:

    def __init__(self, intg_type:str, host: str, serial:str, token:str, web_session, lang: str = "en") -> None:
        if host is not None:
            self.host_url = f"http://{host}"
            self.token = None
        elif serial is not None and token is not None:
            # the Cloud-API endpoint!
            # looks like that CONTROLLER and CHARGER use the SAME API-Endpoint?!
            # in contrast to the documentation :-/
            self.host_url = f"https://{serial.zfill(6)}.api.v3.go-e.io"
            self.token = f"Bearer {token}"

        if intg_type is not None and intg_type == INTG_TYPE.CONTROLLER.value:
            self.isController = True
            self.isCharger = False
            self._logkey = "go-eController"
            self._FILTER_SYSTEMS = FILTER_CONTROLER_SYSTEMS
            self._FILTER_VERSIONS = FILTER_CONTROLER_VERSIONS
            self._FILTER_MIN_STATES = FILTER_CONTROLER_MIN_STATES
            self._FILTER_IDS_ADDON = ""
            self._FILTER_TIMES_ADDON = FILTER_CONTROLER_TIMES_ADDON
            self._FILTER_ALL_STATES = FILTER_CONTROLER_ALL_STATES
            self._FILTER_ALL_CONFIG = FILTER_CONTROLER_ALL_CONFIG
        else:
            self.isCharger = True
            self.isController = False
            self._logkey = "go-eCharger"
            self._FILTER_SYSTEMS = FILTER_SYSTEMS
            self._FILTER_VERSIONS = FILTER_VERSIONS

            self._FILTER_MIN_STATES = FILTER_MIN_STATES
            self._FILTER_IDS_ADDON = FILTER_IDS_ADDON
            self._FILTER_TIMES_ADDON = FILTER_TIMES_ADDON

            self._FILTER_ALL_STATES = FILTER_ALL_STATES.format(CARDS_ENERGY_FILTER=FILTER_CARDS_ENGY_CLASSIC)
            self._FILTER_ALL_CONFIG = FILTER_ALL_CONFIG.format(CARDS_ID_FILTER=FILTER_CARDS_ID_CLASSIC)

        self.web_session = web_session
        self.lang_map = None
        if lang in TRANSLATIONS:
            self.lang_map = TRANSLATIONS[lang]
        else:
            self.lang_map = TRANSLATIONS["en"]

        self._LAST_CONFIG_UPDATE_TS = 0
        self._LAST_FULL_STATE_UPDATE_TS = 0
        self._REQUEST_IDS_DATA = False
        self._versions = {}
        self._states = {}
        self._config = {}

    def available_fields(self) -> int:
        return len(self._versions) + len(self._states) + len(self._config)

    def clear_data(self):
        self._LAST_CONFIG_UPDATE_TS = 0
        self._LAST_FULL_STATE_UPDATE_TS = 0
        self._REQUEST_IDS_DATA = False
        self._versions = {}
        self._states = {}
        self._config = {}

    def reset_stored_update_ts(self):
        self._LAST_CONFIG_UPDATE_TS = 0
        self._LAST_FULL_STATE_UPDATE_TS = 0

    async def read_system(self) -> dict:
        return await self._read_filtered_data(filters=self._FILTER_SYSTEMS, log_info="read_system")

    async def read_versions(self):
        for attempt in range(5):
            self._versions = await self._read_filtered_data(filters=self._FILTER_VERSIONS, log_info=f"read_versions (attempt {attempt+1})")
            if self._versions is not None and len(self._versions) > 0:
                break
            if attempt < 4:
                # sleep random between 2 and 10 seconds...
                await asyncio.sleep(random.uniform(2, 10))

        if self._versions is None or len(self._versions) == 0:
            _LOGGER.warning(f"read_versions(): no versions data available - enable debug log for details!")
            return False

        if self.isCharger:
            # we must check if this is firmware 60.0 or higher - since if this
            # is the case, we must use a different filter for the cards-data
            # Since in the 60.0 firmware the key 'cards' has been removed and
            # has been replaced by 30 single keys (instead of using a json object)
            # This must be special Austrian logic - but what do I know!
            # 2026 Update:
            # It looks like, that the cards[] have returned - at least in 60.3 the
            # cards object has returned, so we include this in our check...
            fwv = self._versions.get(Tag.FWV.key, "0.0")
            if '-' in fwv:
                _LOGGER.debug(f"read_versions(): firmware version must be patched! {fwv}")
                fwv = fwv[:fwv.index('-')]

            if Version(fwv) >= Version("60.0") and len(self._versions.get(FILTER_CARDS_ID_CLASSIC, [])) == 0:
                _LOGGER.info(f"read_versions(): '{fwv}' FirmwareVersion detected -> using 'card' keys: {FILTER_CARDS_ID_FWV60}")
                self._FILTER_ALL_STATES = FILTER_ALL_STATES.format(CARDS_ENERGY_FILTER=FILTER_CARDS_ENGY_FWV60)
                self._FILTER_ALL_CONFIG = FILTER_ALL_CONFIG.format(CARDS_ID_FILTER=FILTER_CARDS_ID_FWV60)
            else:
                _LOGGER.info(f"read_versions(): '{fwv}' FirmwareVersion detected -> 'cards' list is present")
                self._FILTER_ALL_STATES = FILTER_ALL_STATES.format(CARDS_ENERGY_FILTER=FILTER_CARDS_ENGY_CLASSIC)
                self._FILTER_ALL_CONFIG = FILTER_ALL_CONFIG.format(CARDS_ID_FILTER=FILTER_CARDS_ID_CLASSIC)
        return True

    async def read_all(self) -> dict:
        await self.read_all_states();
        # 1 day = 24h * 60min * 60sec = 86400 sec
        # 1 hour = 60min * 60sec = 3600 sec
        if self._LAST_CONFIG_UPDATE_TS + 3600 < time():
            await self.read_all_config();

        return self._versions | self._states | self._config

    async def read_all_states(self):
        do_minimal_status_update: bool = False
        if self.isCharger:
            # ok we are in idle state - so we do not need all states... [but 5 minutes (=300sec) do a full update]
            if Tag.CAR.key in self._states and self._states[Tag.CAR.key] == CAR_VALUES.IDLE.value:
                if self._LAST_FULL_STATE_UPDATE_TS + 300 > time():
                    do_minimal_status_update = True
        elif self.isController:
            if self._LAST_FULL_STATE_UPDATE_TS + 300 > time():
                do_minimal_status_update = True

        if do_minimal_status_update:
            filter = self._FILTER_MIN_STATES
            if self.isCharger and self._REQUEST_IDS_DATA:
                filter = filter + self._FILTER_IDS_ADDON

            # check what additional times do frequent update?!
            filter = filter+self._FILTER_TIMES_ADDON

            idle_states = await self._read_filtered_data(filters=filter, log_info="read_idle_states")
            if len(idle_states) > 0:
                # copy all fields from 'idle_states' to self._states
                self._states.update(idle_states)

                # reset the '_REQUEST_IDS_DATA' flag (will be enabled again, if we post new PV data to the
                # wallbox)
                if self.isCharger and self._REQUEST_IDS_DATA:
                    self._REQUEST_IDS_DATA = False

                # check, if the car idle state have changed to something else
                if self.isCharger and Tag.CAR.key in self._states and self._states[Tag.CAR.key] != CAR_VALUES.IDLE.value:
                    # the car state is not 'idle' - so we should fetch all states...
                    self._LAST_FULL_STATE_UPDATE_TS = 0
                    await self.read_all_states()

        else:
            self._states = await self._read_filtered_data(filters=self._FILTER_ALL_STATES, log_info="read_all_states")
            if len(self._states) > 0:
                self._LAST_FULL_STATE_UPDATE_TS = time()

    async def force_config_update(self):
        self._LAST_CONFIG_UPDATE_TS = 0
        self._LAST_FULL_STATE_UPDATE_TS = 0
        await self.read_all_config()

    async def read_all_config(self):
        if len(self._FILTER_ALL_CONFIG) > 0:
            self._config = await self._read_filtered_data(filters=self._FILTER_ALL_CONFIG, log_info="read_all_config")
            if len(self._config) > 0:
                self._LAST_CONFIG_UPDATE_TS = time()
            else:
                # If config read fails, wait 5 minutes before retrying to prevent hammering
                _LOGGER.info(f"read_all_config(): failed - backing off for 5 minutes")
                self._LAST_CONFIG_UPDATE_TS = time() - 3600 + 300 # Reset timer to 5 mins from now (300s left to 3600)
        else:
            # no configuration filter yet...
            pass

    async def _read_filtered_data(self, filters: str, log_info: str) -> dict:
        args = {"filter": filters}
        req_field_count = len(args['filter'].split(','))
        _LOGGER.debug(f"_read_filtered_data(): {log_info} going to request {req_field_count} keys from {self._logkey}@{self.host_url}")
        if self.token:
            headers = {"Authorization": self.token}
        else:
            headers = None
        async with (self.web_session.get(f"{self.host_url}/api/status", headers=headers, params=args) as res):
            try:
                if res.status in [200, 400]:
                    try:
                        r_json = await res.json()
                        if r_json is not None and len(r_json) > 0:
                            resp_field_count = len(r_json)
                            if resp_field_count >= req_field_count:
                                _LOGGER.debug(f"_read_filtered_data(): read {resp_field_count} values from {self._logkey}@{self.host_url}")
                            else:
                                missing_fields_in_reponse = []
                                requested_fields = args['filter'].split(',')
                                for a_req_key in requested_fields:
                                    if a_req_key not in r_json:
                                        missing_fields_in_reponse.append(a_req_key)

                                _LOGGER.debug(f"_read_filtered_data(): [missing fields: {len(missing_fields_in_reponse)} -> {missing_fields_in_reponse}] - not all requested fields where present in the response from from {self._logkey}@{self.host_url}")
                            return r_json

                    except JSONDecodeError as json_exc:
                        _LOGGER.warning(f"_read_filtered_data(): {log_info} JSONDecodeError while 'await res.json(): {json_exc}")

                    except ClientResponseError as io_exc:
                        _LOGGER.warning(f"_read_filtered_data(): {log_info} ClientResponseError while 'await res.json(): {io_exc}")

                else:
                    _LOGGER.warning(f"{log_info} failed with http-status {res.status}")
            except ClientResponseError as io_exc:
                _LOGGER.warning(f"{log_info} failed cause: {io_exc}")
            except BaseException as err:
                _LOGGER.warning(f"_read_filtered_data(): {log_info} BaseException: {type(err).__name__}: {err}")

        return {}

    async def _read_all_data(self) -> dict:
        _LOGGER.info(f"_read_all_data(): going to request ALL keys from {self._logkey}@{self.host_url}")
        if self.token:
            headers = {"Authorization": self.token}
        else:
            headers = None
        async with self.web_session.get(f"{self.host_url}/api/status", headers=headers) as res:
            try:
                if res.status in [200, 400]:
                    try:
                        r_json = await res.json()
                        if r_json is not None and len(r_json) > 0:
                            return r_json

                    except JSONDecodeError as json_exc:
                        _LOGGER.warning(f"_read_all_data(): JSONDecodeError while 'await res.json(): {json_exc}")

                    except ClientResponseError as io_exc:
                        _LOGGER.warning(f"_read_all_data(): ClientResponseError while 'await res.json(): {io_exc}")

                else:
                    _LOGGER.warning(f"_read_all_data(): REQ_ALL failed with http-status {res.status}")

            except ClientResponseError as io_exc:
                _LOGGER.warning(f"_read_all_data(): REQ_ALL failed cause: {io_exc}")
            except BaseException as err:
                _LOGGER.warning(f"_read_all_data(): BaseException: {type(err).__name__}: {err}")
        return {}

    async def write_value_to_key(self, key, value) -> dict:
        if value is None:
            args = f"{key}=null"
        elif isinstance(value, (bool, int, float)):
            args = {key: str(value).lower()}
        elif isinstance(value, dict):
            args = {key: json.dumps(value).replace(' ','')}
        elif isinstance(value, str) and value == IS_TRIGGER:
            # ok, these are special trigger actions that we want to call from the FE...
            match key:
                case Tag.INTERNAL_FORCE_CONFIG_READ.key:
                    await self.force_config_update()

            return {key: value}
        else:
            args = {key: '"'+str(value)+'"'}

        return await self._write_values_int(args, key, value)

    async def _write_values_int(self, args, key, value) -> dict:
        _LOGGER.info(f"_write_values_int(): going to write {args} to {self._logkey}@{self.host_url}")
        if self.token:
            headers = {"Authorization": self.token}
        else:
            headers = None

        async with self.web_session.get(f"{self.host_url}/api/set", headers=headers, params=args) as res:
            try:
                if res.status == 200:
                    try:
                        r_json = await res.json()
                        if r_json is not None and len(r_json) > 0:
                            if key in r_json and r_json[key]:
                                # ignore 'force-update' for 'ids' (PV surplus charging)
                                if key != Tag.IDS.key:
                                    self._LAST_CONFIG_UPDATE_TS = 0
                                    self._LAST_FULL_STATE_UPDATE_TS = 0
                                else:
                                    if self.isCharger:
                                        self._REQUEST_IDS_DATA = True
                                return {key: value}
                            else:
                                return {"err": r_json}

                    except JSONDecodeError as json_exc:
                        _LOGGER.warning(f"_write_values_int(): JSONDecodeError while 'await res.json(): {json_exc}")

                    except ClientResponseError as io_exc:
                        _LOGGER.warning(f"_write_values_int(): ClientResponseError while 'await res.json(): {io_exc}")

                elif res.status == 500 and int(res.headers['Content-Length']) > 0:
                    try:
                        r_json = await res.json()
                        return {"err": r_json}
                    except JSONDecodeError as json_exc:
                        _LOGGER.warning(f"_write_values_int(): JSONDecodeError while 'res.status == 500 res.json(): {json_exc}")
                    except ClientResponseError as io_exc:
                        _LOGGER.warning(f"_write_values_int(): ClientResponseError while 'res.status == 500 res.json(): {io_exc}")
                else:
                    _LOGGER.warning(f"_write_values_int(): failed with http-status {res.status}")

            except ClientResponseError as io_exc:
                _LOGGER.warning(f"_write_values_int(): failed cause: {io_exc}")
            except BaseException as err:
                _LOGGER.warning(f"_write_values_int(): BaseException: {type(err).__name__}: {err}")

        return {}
