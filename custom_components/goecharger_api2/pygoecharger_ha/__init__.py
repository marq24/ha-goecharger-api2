import asyncio
import base64
import hashlib
import hmac
import json
import logging
import random
import secrets
from collections import ChainMap
from time import time

import aiohttp
import bcrypt
import msgpack
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
    API_KEYS_TO_IGNORE_FROM_WS,
)
from custom_components.goecharger_api2.pygoecharger_ha.keys import Tag, IS_TRIGGER

_LOGGER: logging.Logger = logging.getLogger(__package__)


class GoeChargerApiV2Bridge:

    def __init__(self, intg_type:str, host: str, access_password:str, serial:str, token:str, web_session, lang: str = "en") -> None:
        self.ws_url = None
        if host is not None:
            self.host_url = f"http://{host}"
            self.token = None

            # could we use the local websocket...?
            if access_password is not None and len(access_password.strip()) > 0:
                self.access_password = access_password.strip()
                self.ws_url = f"ws://{host}/ws"

        elif serial is not None and token is not None:
            # the Cloud-API endpoint!
            # looks like that CONTROLLER and CHARGER use the SAME API-Endpoint?!
            # in contrast to the documentation :-/
            self.host_url = f"https://{serial.zfill(6)}.api.v3.go-e.io"
            self.token = f"Bearer {token}"

            # could we use the wan websocket...?
            if access_password is not None and len(access_password.strip()) > 0:
                self.access_password = access_password.strip()
                self.ws_url = f"wss://app.v3.go-e.io/{serial}"

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

        # the new ws stuff...
        self.ws_connected = False
        self.coordinator = None
        self._ws_connection = None
        self._ws_hashed_password = None
        self._ws_request_id_counter = 0
        self._ws_debounced_update_task = None
        self._ws_LAST_UPDATE = 0
        self._ws_device_info = {}
        self._ws_states = {}
        self._ws_serial = None
        self._ws_secured = False
        self._ws_proto = -1
        self._ws_protocol = -1

    def available_fields(self) -> int:
        return len(self._versions) + len(self._states) + len(self._config) + len(self._ws_states)

    def clear_data(self):
        self._LAST_CONFIG_UPDATE_TS = 0
        self._LAST_FULL_STATE_UPDATE_TS = 0
        self._REQUEST_IDS_DATA = False
        self._versions = {}
        self._states = {}
        self._config = {}
        self._ws_LAST_UPDATE = 0
        self._ws_device_info = {}
        self._ws_states = {}
        self._ws_serial = None
        self._ws_secured = False
        self._ws_proto = -1
        self._ws_protocol = -1

    def reset_stored_update_ts(self):
        self._LAST_CONFIG_UPDATE_TS = 0
        self._LAST_FULL_STATE_UPDATE_TS = 0
        self._ws_LAST_UPDATE = 0

    async def read_system(self) -> dict:
        # TODO: WEBSOCKET
        return await self._read_filtered_data(filters=self._FILTER_SYSTEMS, log_info="read_system")

    async def read_versions(self):
        # TODO: WEBSOCKET
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
                _LOGGER.info(f"read_versions(): HTTP-API '{fwv}' FirmwareVersion detected -> using 'card' keys: {FILTER_CARDS_ID_FWV60}")
                self._FILTER_ALL_STATES = FILTER_ALL_STATES.format(CARDS_ENERGY_FILTER=FILTER_CARDS_ENGY_FWV60)
                self._FILTER_ALL_CONFIG = FILTER_ALL_CONFIG.format(CARDS_ID_FILTER=FILTER_CARDS_ID_FWV60)
            else:
                _LOGGER.info(f"read_versions(): HTTP-API '{fwv}' FirmwareVersion detected -> 'cards' list is present")
                self._FILTER_ALL_STATES = FILTER_ALL_STATES.format(CARDS_ENERGY_FILTER=FILTER_CARDS_ENGY_CLASSIC)
                self._FILTER_ALL_CONFIG = FILTER_ALL_CONFIG.format(CARDS_ID_FILTER=FILTER_CARDS_ID_CLASSIC)
        return True

    async def read_all(self) -> dict:
        await self.read_all_states()
        # 1 day = 24h * 60min * 60sec = 86400 sec
        # 1 hour = 60min * 60sec = 3600 sec
        if self._LAST_CONFIG_UPDATE_TS + 3600 < time():
            await self.read_all_config()

        return ChainMap(self._ws_states, self._config, self._states, self._versions)

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

                    except json.JSONDecodeError as json_exc:
                        _LOGGER.warning(f"_read_filtered_data(): {log_info} JSONDecodeError while 'await res.json(): {json_exc}")

                    except aiohttp.ClientResponseError as io_exc:
                        _LOGGER.warning(f"_read_filtered_data(): {log_info} ClientResponseError while 'await res.json(): {io_exc}")

                else:
                    _LOGGER.warning(f"{log_info} failed with http-status {res.status}")
            except aiohttp.ClientResponseError as io_exc:
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

                    except json.JSONDecodeError as json_exc:
                        _LOGGER.warning(f"_read_all_data(): JSONDecodeError while 'await res.json(): {json_exc}")

                    except aiohttp.ClientResponseError as io_exc:
                        _LOGGER.warning(f"_read_all_data(): ClientResponseError while 'await res.json(): {io_exc}")

                else:
                    _LOGGER.warning(f"_read_all_data(): REQ_ALL failed with http-status {res.status}")

            except aiohttp.ClientResponseError as io_exc:
                _LOGGER.warning(f"_read_all_data(): REQ_ALL failed cause: {io_exc}")
            except BaseException as err:
                _LOGGER.warning(f"_read_all_data(): BaseException: {type(err).__name__}: {err}")
        return {}

    async def write_value_to_key(self, key, value) -> dict:
        is_button_press = value is not None and str(value) == IS_TRIGGER

        if not is_button_press and self.ws_connected and self._ws_connection is not None:
            await self._ws_send_command(key, value)
            return None
        else:
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
                    case Tag.INTERNAL_FORCE_REFRESH_ALL.key:
                        self.reset_stored_update_ts()
                        # we do the actual request for the new data in the
                        # DataUpdateCoordinator... (with a short delwy of some
                        # seconds...)
                        # await self.read_all()

                return {key: value}
            else:
                args = {key: '"'+str(value)+'"'}

            return await self._write_values_int(args, a_result_key = key, a_result_value = value)

    async def write_multiple_values_to_keys(self, args, key, value) -> dict:
        if self.ws_connected and self._ws_connection is not None:
            for a_key, a_value in args.items():
                await self._ws_send_command(a_key, a_value)
                await asyncio.sleep(0.75)
            return None
        else:

            return await self._write_values_int(args, a_result_key = key, a_result_value = value)

    async def _write_values_int(self, args, a_result_key, a_result_value) -> dict:
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
                            if a_result_key in r_json and r_json[a_result_key]:
                                # ignore 'force-update' for 'ids' (PV surplus charging)
                                if a_result_key != Tag.IDS.key:
                                    self._LAST_CONFIG_UPDATE_TS = 0
                                    self._LAST_FULL_STATE_UPDATE_TS = 0
                                else:
                                    if self.isCharger:
                                        self._REQUEST_IDS_DATA = True
                                return {a_result_key: a_result_value}
                            else:
                                return {"err": r_json}

                    except json.JSONDecodeError as json_exc:
                        _LOGGER.warning(f"_write_values_int(): JSONDecodeError while 'await res.json(): {json_exc}")

                    except aiohttp.ClientResponseError as io_exc:
                        _LOGGER.warning(f"_write_values_int(): ClientResponseError while 'await res.json(): {io_exc}")

                elif res.status == 500 and int(res.headers['Content-Length']) > 0:
                    try:
                        r_json = await res.json()
                        return {"err": r_json}
                    except json.JSONDecodeError as json_exc:
                        _LOGGER.warning(f"_write_values_int(): JSONDecodeError while 'res.status == 500 res.json(): {json_exc}")
                    except aiohttp.ClientResponseError as io_exc:
                        _LOGGER.warning(f"_write_values_int(): ClientResponseError while 'res.status == 500 res.json(): {io_exc}")
                else:
                    _LOGGER.warning(f"_write_values_int(): failed with http-status {res.status}")

            except aiohttp.ClientResponseError as io_exc:
                _LOGGER.warning(f"_write_values_int(): failed cause: {io_exc}")
            except BaseException as err:
                _LOGGER.warning(f"_write_values_int(): BaseException: {type(err).__name__}: {err}")

        return {}



    #######################
    ###### WEBSOCKET ######
    #######################
    def ws_set_coordinator(self, coordinator):
        self.coordinator = coordinator
        self._ws_debounced_update_task = None

    def ws_check_last_update(self) -> bool:
        if self._ws_LAST_UPDATE + 50 > time():
            _LOGGER.debug(f"ws_check_last_update(): all good! [last update: {int(time()-self._ws_LAST_UPDATE)} sec ago]")
            return True
        else:
            _LOGGER.info(f"ws_check_last_update(): force reconnect...")
            return False

    async def ws_close(self, ws):
        """Close the WebSocket connection cleanly."""
        if self._ws_serial is not None:
            _LOGGER.debug(f"ws_close(): for '{self._ws_serial}' called")
        else:
            _LOGGER.debug(f"ws_close(): for '{self.ws_url}' called")

        self.ws_connected = False
        if ws is not None:
            try:
                await ws.close()
                _LOGGER.debug(f"ws_close(): connection closed successfully")
            except BaseException as e:
                _LOGGER.info(f"ws_close(): Error closing WebSocket connection: {type(e).__name__} - {e}")
            finally:
                ws = None
        else:
            _LOGGER.debug(f"ws_close(): No active WebSocket connection to close (ws is None)")

    def _ws_notify_for_new_data(self):
        if self._ws_debounced_update_task is not None and not self._ws_debounced_update_task.done():
            self._ws_debounced_update_task.cancel()
        self._ws_debounced_update_task = asyncio.create_task(self._ws_debounce_coordinator_update())

    async def _ws_debounce_coordinator_update(self):
        await asyncio.sleep(0.3)
        if hasattr(self, "coordinator") and self.coordinator is not None:
            self.coordinator.async_set_updated_data(ChainMap(self._ws_states, self._config, self._states, self._versions))

    def _ws_compute_hashed_password(self, hash_type: str, password: str, serial: str) -> bytes:
        if hash_type == "pbkdf2":
            """Compute PBKDF2-SHA512 hashed password for WebSocket authentication"""
            hashed = hashlib.pbkdf2_hmac(
                'sha512',
                password.encode('utf-8'),
                serial.encode('utf-8'),
                100000,
                256
            )
            return base64.b64encode(hashed)[:32]
        elif hash_type == "bcrypt":
            # initially found @ https://github.com/joscha82/wattpilot/issues/46#issuecomment-3289810024
            # and then took it from wattpilot!
            # https://github.com/mk-maddin/wattpilot-HA/blob/master/custom_components/wattpilot/wattpilot/src/wattpilot/__init__.py#L498
            iterations = 8
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            salt = f"$2a${iterations:02d}${bcryptjs_encode_base64(serial, 16)}"
            return bcrypt.hashpw(password_hash.encode(), salt.encode())[len(salt):]

        return None

    def _ws_compute_auth_hash(self, token1: str, token2: str, token3: str, hashed_password: bytes) -> str:
        """Compute authentication hash for WebSocket"""
        hash1 = hashlib.sha256(token1.encode() + hashed_password).hexdigest()
        final_hash = hashlib.sha256((token3 + token2 + hash1).encode()).hexdigest()
        return final_hash

    def _ws_decode_message(self, msg):
        """Decode incoming WebSocket message (MessagePack or JSON)"""
        if isinstance(msg, bytes):
            if msg[0:1] == b'\x00':
                return msgpack.unpackb(msg[1:])
            else:
                return msgpack.unpackb(msg)
        elif isinstance(msg, str):
            return json.loads(msg)
        return msg

    def _ws_normalize_value(self, value):
        """Recursively normalize values (convert bytes to strings)"""
        if isinstance(value, bytes):
            try:
                return value.decode('utf-8')
            except:
                return value.hex()
        elif isinstance(value, dict):
            return {self._ws_normalize_value(k): self._ws_normalize_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._ws_normalize_value(item) for item in value]
        elif isinstance(value, tuple):
            return tuple(self._ws_normalize_value(item) for item in value)
        else:
            return value

    def _ws_normalize_dict(self, data: dict) -> dict:
        """Convert dict with bytes keys/values to string keys/values recursively"""
        result = {}
        for key, value in data.items():
            key_str = key.decode('utf-8') if isinstance(key, bytes) else str(key)
            result[key_str] = self._ws_normalize_value(value)
        return result

    async def _ws_send_command(self, key: str, value):
        """Send a setValue command via WebSocket"""
        _LOGGER.debug(f"_ws_send_command(): Sending {key}:{value} via WebSocket...")
        self._ws_request_id_counter += 1

        if value is None:
            value = "null"

        original_message = {
            "type": "setValue",
            "requestId": self._ws_request_id_counter,
            "key": key,
            "value": value
        }

        if self._ws_secured:
            # the local websocket needs special handling...
            payload = json.dumps(original_message)
            h = hmac.new(bytearray(self._ws_hashed_password), bytearray(payload.encode()), hashlib.sha256)
            secure_message = {
                "type": "securedMsg",
                "data": payload,
                "requestId": f"{original_message['requestId']}sm",
                "hmac": h.hexdigest()
            }

            # Pack as msgpack with 0x00 prefix
            msg_packed = b'\x00' + msgpack.packb(secure_message)

            _LOGGER.debug(f"_ws_send_command(): Sending {key}={value} as BYTES")
            await self._ws_connection.send_bytes(msg_packed)
        else:
            # the cloud API can receive real JSON data...
            _LOGGER.debug(f"_ws_send_command(): Sending {key}={value} as JSON")
            await self._ws_connection.send_json(original_message)

        return True


    async def ws_connect(self):
        """Connect to WebSocket with full authentication and message handling"""
        _LOGGER.debug(f"ws_connect() STARTED...")
        self.ws_connected = False

        if self.ws_url is None:
            _LOGGER.warning("ws_connect(): WebSocket URL not configured")
            return None

        if self.token:
            headers = {"Authorization": self.token}
        else:
            headers = None

        try:
            async with self.web_session.ws_connect(url=self.ws_url, headers=headers) as ws:
                self._ws_connection = ws
                _LOGGER.info(f"ws_connect(): Connected to WebSocket: {self.ws_url}")

                # Step 1: Receive HELLO message
                hello_msg = await ws.receive()
                hello_data = self._ws_decode_message(hello_msg.data)
                normalized_hello = self._ws_normalize_dict(hello_data)

                serial = normalized_hello.get('serial')
                if not serial:
                    _LOGGER.warning("ws_connect(): No serial in hello message")
                    return None

                self._ws_serial = serial
                self._ws_secured = normalized_hello.get('secured', False)
                self._ws_proto = normalized_hello.get('proto', -1)
                self._ws_protocol = normalized_hello.get('protocol', -1)

                # 'devicetype': 'go-eCharger_V4'
                # 'devicetype': 'go-eCharger_Phoenix', 'devicesubtype': 'core_cable',

                _LOGGER.debug(f"ws_connect(): Extracted the device serial: {self._ws_serial} [secured: {self._ws_secured}, proto: {self._ws_proto}, protocol: {self._ws_protocol}]")
                self._ws_device_info = {k: v for k, v in normalized_hello.items()}
                if 'type' in self._ws_device_info:
                    self._ws_device_info.pop('type', None)
                _LOGGER.debug(f"ws_connect(): ws_device_info: {self._ws_device_info}")


                # Step 2: Receive AUTH REQUIRED message
                auth_req_msg = await ws.receive()
                auth_data = self._ws_decode_message(auth_req_msg.data)
                normalized_auth = self._ws_normalize_dict(auth_data)

                hash_type = normalized_auth.get('hash', 'pbkdf2').lower()
                if hash_type not in ['pbkdf2', 'bcrypt']:
                    _LOGGER.info(f"ws_connect(): Unsupported authentication hash type: {hash_type}")
                    return None

                # Step 3: Compute hashed password
                if not hasattr(self, 'access_password') or not self.access_password:
                    _LOGGER.warning("ws_connect(): No access_password configured")
                    return None

                self._ws_hashed_password = self._ws_compute_hashed_password(hash_type, self.access_password, serial)
                _logging_pwd = self._ws_hashed_password.decode('utf-8')
                _LOGGER.debug(f"ws_connect(): Computed hashed password {_logging_pwd[:6]}...{_logging_pwd[-6:]}")

                token1 = normalized_auth.get('token1')
                token2 = normalized_auth.get('token2')
                if not token1 or not token2:
                    _LOGGER.warning("ws_connect(): Missing authentication tokens")
                    return None

                # Step 4: Generate token3 and compute auth hash
                token3 = secrets.token_hex(16)
                auth_hash = self._ws_compute_auth_hash(token1, token2, token3, self._ws_hashed_password)

                # Step 5: Send AUTH response
                auth_response = {
                    "type": "auth",
                    "token3": token3,
                    "hash": auth_hash
                }
                if self.token is not None:
                    # the cloud API can receive real JSON data...
                    await ws.send_json(auth_response)
                else:
                    auth_packed = b'\x00' + msgpack.packb(auth_response)
                    await ws.send_bytes(auth_packed)

                _LOGGER.debug("ws_connect(): Sent authentication response")

                # Step 6: Receive AUTH result
                auth_result = await ws.receive()
                result_data = self._ws_decode_message(auth_result.data)
                normalized_result = self._ws_normalize_dict(result_data)

                msg_type = normalized_result.get('type', '')
                if msg_type != 'authSuccess' and not normalized_result.get('success'):
                    _LOGGER.warning(f"ws_connect(): Authentication failed: {normalized_result}")
                    return None

                _LOGGER.info("ws_connect(): Authentication successful!")
                self.ws_connected = True

                # Step 7: Handle incoming messages
                async for msg in ws:
                    new_data_arrived = False

                    if msg.type == aiohttp.WSMsgType.BINARY:
                        try:
                            data = self._ws_decode_message(msg.data)
                            normalized = self._ws_normalize_dict(data)
                            new_data_arrived = self.extract_ws_message_data(normalized)

                        except Exception as e:
                            _LOGGER.warning(f"ws_connect(): Error processing BINARY message: {type(e).__name__} - {e}")

                    elif msg.type == aiohttp.WSMsgType.TEXT:
                        try:
                            data = json.loads(msg.data)
                            new_data_arrived = self.extract_ws_message_data(data)

                        except Exception as e:
                            _LOGGER.warning(f"ws_connect(): Error processing TEXT message: {type(e).__name__} - {e}")

                    elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                        _LOGGER.info(f"ws_connect(): WebSocket closed or error: {msg}")
                        break

                    else:
                        _LOGGER.warning(f"ws_connect(): Unknown message type: {msg.type}")

                    # Notify coordinator if new data arrived
                    if new_data_arrived:
                        # Store the last time we heard from the websocket
                        self._ws_LAST_UPDATE = time()
                        self._ws_notify_for_new_data()

        except aiohttp.ClientConnectionError as err:
            _LOGGER.error(f"ws_connect(): Could not connect to websocket: {type(err).__name__} - {err}")
        except asyncio.TimeoutError as time_exc:
            _LOGGER.debug(f"ws_connect(): TimeoutError: No WebSocket message received within timeout period")
        except asyncio.CancelledError as canceled:
            _LOGGER.info(f"ws_connect(): Terminated - {type(canceled).__name__}")
        except BaseException as x:
            _LOGGER.error(f"ws_connect(): Error: {type(x).__name__} - {x}")

        _LOGGER.debug(f"ws_connect() ENDED")

        try:
            await self.ws_close(ws)
        except UnboundLocalError:
            _LOGGER.debug(f"ws_connect(): Skipping ws_close() (ws_connection is unbound)")
        except BaseException as e:
            _LOGGER.error(f"ws_connect(): Error in ws_close(): {type(e).__name__} - {e}")

        self.ws_connected = False
        self._ws_connection = None
        self._ws_states = {}
        self._ws_LAST_UPDATE = 0
        return None

    def extract_ws_message_data(self, data:dict):
        new_data_arrived = False
        msg_type = data.get('type', 'unknown').lower()

        if msg_type == 'fullstatus':
            status_data = data.get('status', {})
            if status_data and len(status_data) > 0:
                if data.get('partial', False):
                    self._ws_states.update(status_data)
                else:
                    # Full update - but verify all existing keys are present
                    missing_keys = set(self._ws_states.keys()) - set(status_data.keys())
                    if missing_keys:
                        _LOGGER.info(f"extract_ws_message_data(): Full update missing {len(missing_keys)} - so we will preserve them!")
                        self._ws_states.update(status_data)
                    else:
                        self._ws_states = {k: v for k, v in status_data.items()}

                new_data_arrived = True
                _LOGGER.debug(f"extract_ws_message_data(): Received 'fullStatus' with {len(status_data)} keys")

        elif msg_type == 'deltastatus':
            status_data = data.get('status', {})
            if status_data and len(status_data) > 0:
                # Filter out keys we want to ignore
                filtered_data = {k: v for k, v in status_data.items() if
                                 k not in API_KEYS_TO_IGNORE_FROM_WS}
                if filtered_data:
                    self._ws_states.update(filtered_data)
                    new_data_arrived = True
                    _LOGGER.debug(f"extract_ws_message_data(): Received 'deltaStatus' with {len(filtered_data)} keys")

        elif msg_type == 'response':
            if data.get('success'):
                status_data = data.get('status', {})
                if status_data and len(status_data) > 0:
                    self._ws_states.update(status_data)
                    new_data_arrived = True
                    _LOGGER.debug(f"extract_ws_message_data(): Received 'response' with {len(status_data)} keys")
            else:
                _LOGGER.warning(f"extract_ws_message_data(): Command failed: {data}")

        else:
            _LOGGER.debug(f"extract_ws_message_data(): Received {msg_type} message")

        return new_data_arrived

@staticmethod
def bcryptjs_base64_encode(b: bytes, length: int) -> str:
    BASE64_CODE = "./ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"

    if not 0 < length <= len(b):
        raise ValueError(f"Illegal len: {length}")

    rs = []
    i = 0

    while i < length:
        c1 = (b[i] & 0x03) << 4
        rs.append(BASE64_CODE[b[i] >> 2])
        i += 1

        if i >= length:
            rs.append(BASE64_CODE[c1])
            break

        rs.append(BASE64_CODE[c1 | (b[i] >> 4)])
        c1 = (b[i] & 0x0f) << 2
        i += 1

        if i >= length:
            rs.append(BASE64_CODE[c1])
            break

        rs.append(BASE64_CODE[c1 | (b[i] >> 6)])
        rs.append(BASE64_CODE[b[i] & 0x3f])
        i += 1

    return "".join(rs)

@staticmethod
def bcryptjs_encode_base64(s: str, length: int) -> str:
    if not s.isdigit():
        _LOGGER.warning(f"bcryptjs_encode_base64(): check serial string - should be digits only: {s}")
        raise ValueError(f"Check serial string - should be digits only: {s}")

    b = bytes([0] * (length - len(s)) + [int(ch) for ch in s])
    return bcryptjs_base64_encode(b, length)
