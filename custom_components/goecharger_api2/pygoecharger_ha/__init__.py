import json
import logging
from json import JSONDecodeError
from time import time

from aiohttp import ClientResponseError

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
)
from custom_components.goecharger_api2.pygoecharger_ha.keys import Tag, IS_TRIGGER

_LOGGER: logging.Logger = logging.getLogger(__package__)


class GoeChargerApiV2Bridge:

    def __init__(self, intg_type:str, host: str, serial:str, token:str, web_session, lang: str = "en") -> None:
        if host is not None:
            self.host_url = f"http://{host}"
            self.token = None
        elif serial is not None and token is not None:
            # the Cloud-API 2 endpoint!
            if intg_type is not None and intg_type == INTG_TYPE.CONTROLLER.value:
                # CONTROLLER:
                # see: https://github.com/goecharger/go-eController-API/blob/main/cloudapi-en.md
                # https://serial_number.api.controller.go-e.io/api/set
                self.host_url = f"https://{serial}.api.controller.go-e.io"
            else:
                # CHARGER
                # see: https://github.com/goecharger/go-eCharger-API-v2/blob/main/cloudapi-en.md
                # https://serial_number.api.v3.go-e.io/api/set
                self.host_url = f"https://{serial}.api.v3.go-e.io"
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
            self._FILTER_ALL_STATES = FILTER_ALL_STATES
            self._FILTER_ALL_CONFIG = FILTER_ALL_CONFIG

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

    async def read_system(self) -> dict:
        return await self._read_filtered_data(filters=self._FILTER_SYSTEMS, log_info="read_system")

    async def read_versions(self):
        self._versions = await self._read_filtered_data(filters=self._FILTER_VERSIONS, log_info="read_versions")

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
                    _LAST_FULL_STATE_UPDATE_TS = 0
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
            # no configuration filter yet...
            pass

    async def _read_filtered_data(self, filters: str, log_info: str) -> dict:
        args = {"filter": filters}
        req_field_count = len(args['filter'].split(','))
        _LOGGER.debug(f"going to request {req_field_count} keys from {self._logkey}@{self.host_url}")
        if self.token:
            headers = {"Authorization": self.token}
        else:
            headers = None
        async with self.web_session.get(f"{self.host_url}/api/status", headers=headers, params=args) as res:
            try:
                if res.status in [200, 400]:
                    try:
                        r_json = await res.json()
                        if r_json is not None and len(r_json) > 0:
                            resp_field_count = len(r_json)
                            if resp_field_count >= req_field_count:
                                _LOGGER.debug(f"read {resp_field_count} values from {self._logkey}@{self.host_url}")
                            else:
                                missing_fields_in_reponse = []
                                requested_fields = args['filter'].split(',')
                                for a_req_key in requested_fields:
                                    if a_req_key not in r_json:
                                        missing_fields_in_reponse.append(a_req_key)

                                _LOGGER.info(
                                    f"[missing fields: {len(missing_fields_in_reponse)} -> {missing_fields_in_reponse}] - not all requested fields where present in the response from from {self._logkey}@{self.host_url}")
                            return r_json

                    except JSONDecodeError as json_exc:
                        _LOGGER.warning(f"APP-API: JSONDecodeError while 'await res.json(): {json_exc}")

                    except ClientResponseError as io_exc:
                        _LOGGER.warning(f"APP-API: ClientResponseError while 'await res.json(): {io_exc}")

                else:
                    _LOGGER.warning(f"APP-API: {log_info} failed with http-status {res.status}")

            except ClientResponseError as io_exc:
                _LOGGER.warning(f"APP-API: {log_info} failed cause: {io_exc}")

        return {}

    async def _read_all_data(self) -> dict:
        _LOGGER.info(f"going to request ALL keys from {self._logkey}@{self.host_url}")
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
                        _LOGGER.warning(f"APP-API: JSONDecodeError while 'await res.json(): {json_exc}")

                    except ClientResponseError as io_exc:
                        _LOGGER.warning(f"APP-API: ClientResponseError while 'await res.json(): {io_exc}")

                else:
                    _LOGGER.warning(f"APP-API: REQ_ALL failed with http-status {res.status}")

            except ClientResponseError as io_exc:
                _LOGGER.warning(f"APP-API: REQ_ALL failed cause: {io_exc}")

        return {}

    async def write_value_to_key(self, key, value) -> dict:
        if value is None:
            args = f"{key}=null"
        elif isinstance(value, (bool, int, float)):
            args = {key: str(value).lower()}
        elif isinstance(value, dict):
            args = {key: json.dumps(value)}
        elif isinstance(value, str) and value == IS_TRIGGER:
            # ok this are special trigger actions, that we want to call from the FE...
            match key:
                case Tag.INTERNAL_FORCE_CONFIG_READ.key:
                    await self.force_config_update()

            return {key: value}
        else:
            args = {key: '"'+str(value)+'"'}

        _LOGGER.info(f"going to write {args} to {self._logkey}@{self.host_url}")
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
                        _LOGGER.warning(f"APP-API: JSONDecodeError while 'await res.json(): {json_exc}")

                    except ClientResponseError as io_exc:
                        _LOGGER.warning(f"APP-API: ClientResponseError while 'await res.json(): {io_exc}")

                elif res.status == 500 and int(res.headers['Content-Length']) > 0:
                    try:
                        r_json = await res.json()
                        return {"err": r_json}
                    except JSONDecodeError as json_exc:
                        _LOGGER.warning(f"APP-API: JSONDecodeError while 'res.status == 500 res.json(): {json_exc}")

                    except ClientResponseError as io_exc:
                        _LOGGER.warning(f"APP-API: ClientResponseError while 'res.status == 500 res.json(): {io_exc}")

                else:
                    _LOGGER.warning(f"APP-API: write_value failed with http-status {res.status}")

            except ClientResponseError as io_exc:
                _LOGGER.warning(f"APP-API: write_value failed cause: {io_exc}")

        return {}
