import asyncio
import logging
from asyncio import sleep
from typing import Final, Any

import voluptuous as vol
from aiohttp import ClientConnectionError
from homeassistant import config_entries, data_entry_flow
from homeassistant.config_entries import ConfigFlowResult, SOURCE_RECONFIGURE
from homeassistant.const import (
    CONF_ID,
    CONF_HOST,
    CONF_PASSWORD,
    CONF_MODEL,
    CONF_TYPE,
    CONF_SCAN_INTERVAL,
    CONF_DELAY,
    CONF_TOKEN,
    CONF_MODE
)
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .const import (
    DOMAIN,
    CONF_11KWLIMIT,
    CONF_INTEGRATION_TYPE,
    LAN,
    WAN,
    CONFIG_VERSION,
    CONFIG_MINOR_VERSION
)
from custom_components.goecharger_api2.pygoecharger_ha import GoeChargerApiV2Bridge, INTG_TYPE, TargetedEvent
from custom_components.goecharger_api2.pygoecharger_ha.keys import Tag
from custom_components.goecharger_api2.pygoecharger_ha.const import (
    FILTER_SYSTEMS,
    FILTER_VERSIONS,
    FILTER_ALL_CONFIG,
    FILTER_CONTROLER_SYSTEMS,
    FILTER_CONTROLER_SYSTEMS,
    FILTER_CONTROLER_VERSIONS,
    FILTER_CONTROLER_ALL_CONFIG
)

_LOGGER: logging.Logger = logging.getLogger(__package__)

SETUP_SYS_TYPE: Final = "stype"
SYSTEM_TYPES: Final = [LAN, WAN]


class GoeChargerApiV2FlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for goecharger_api2."""

    VERSION = CONFIG_VERSION
    MINOR_VERSION = CONFIG_MINOR_VERSION
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        """Initialize."""
        self._errors = {}

        self._selected_system = LAN
        self._default_scan_interval = 30 # Default scan interval for LAN - for WAN it will be set to 120 seconds
        self._default_delay = False

        self._default_host = "YOUR-IP-OR-HOSTNAME-HERE"
        self._default_integration_type = INTG_TYPE.CHARGER.value
        self._default_11kWLimit = False

        self._default_id = "YOUR-SERIAL-HERE"
        self._default_password = ""
        self._default_token = "YOUR-API-KEY-HERE"

        self._type = ""
        self._model = ""
        self._serial = ""

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        entry_data = self._get_reconfigure_entry().data
        self._selected_system = entry_data.get(CONF_MODE)

        if self._selected_system == WAN:
            self._default_scan_interval = entry_data.get(CONF_SCAN_INTERVAL, 120)
            self._default_delay = entry_data.get(CONF_DELAY, False)
            self._default_id = entry_data.get(CONF_ID, "YOUR-SERIAL-HERE")
            self._default_password = entry_data.get(CONF_PASSWORD, "")
            self._default_integration_type = entry_data.get(CONF_INTEGRATION_TYPE, INTG_TYPE.CHARGER.value)
            self._default_token = entry_data.get(CONF_TOKEN, "YOUR-API-KEY-HERE")
            return await self.async_step_user_wan()
        else:
            self._selected_system = LAN
            self._default_scan_interval = entry_data.get(CONF_SCAN_INTERVAL, 30)
            self._default_delay = entry_data.get(CONF_DELAY, False)
            self._default_host = entry_data.get(CONF_HOST, "YOUR-IP-OR-HOSTNAME-HERE")
            self._default_password = entry_data.get(CONF_PASSWORD, "")
            self._default_integration_type = entry_data.get(CONF_INTEGRATION_TYPE, INTG_TYPE.CHARGER.value)
            self._default_11kWLimit = entry_data.get(CONF_11KWLIMIT, False)
            return await self.async_step_user_lan()

    async def async_step_user(self, user_input=None):
        self._errors = {}
        if user_input is not None:
            self._selected_system = user_input[SETUP_SYS_TYPE]

            if self._selected_system == WAN:
                return await self.async_step_user_wan()
            else:
                # return await self.async_step_mode()
                return await self.async_step_user_lan()
        else:
            user_input = {
                SETUP_SYS_TYPE: LAN  # Default to LAN if no input is provided
            }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(SETUP_SYS_TYPE, default=user_input.get(SETUP_SYS_TYPE, LAN)):
                        selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=SYSTEM_TYPES,
                                mode=selector.SelectSelectorMode.DROPDOWN,
                                translation_key=SETUP_SYS_TYPE,
                            )
                        )
                }
            ),
            last_step=False,
            errors=self._errors,
        )

    async def async_step_user_lan(self, user_input=None):
        """Handle a flow initialized by the user."""
        self._errors = {}

        # Uncomment the next 2 lines if only a single instance of the integration is allowed:
        # if self._async_current_entries():
        #     return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            a_user_pwd = user_input.get(CONF_PASSWORD, "").strip()
            valid = await self._test_host(intg_type=user_input[CONF_INTEGRATION_TYPE], host=user_input[CONF_HOST], pwd=a_user_pwd, serial=None, token=None)
            if valid:
                if len(a_user_pwd) == 0 and CONF_PASSWORD in user_input:
                    user_input.pop(CONF_PASSWORD)
                user_input[CONF_MODE] = LAN
                user_input[CONF_SCAN_INTERVAL] = max(5, user_input[CONF_SCAN_INTERVAL])
                user_input[CONF_ID] = self._serial
                user_input[CONF_MODEL] = self._model.split(' ')[0]
                if user_input[CONF_INTEGRATION_TYPE] == INTG_TYPE.CHARGER.value:
                    user_input[CONF_TYPE] = f"{self._type} [{self._model}] Local"
                    title = f"go-eCharger API v2 [{self._serial}] Local"
                else:
                    user_input[CONF_TYPE] = f"{self._type} Local"
                    title = f"go-eController API v2 [{self._serial}] Local"

                self._abort_if_unique_id_configured()
                if self.source == SOURCE_RECONFIGURE:
                    return self.async_update_reload_and_abort(entry=self._get_reconfigure_entry(), data=user_input)
                else:
                    return self.async_create_entry(title=title, data=user_input)
            else:
                self._errors["base"] = "auth_lan"
                raise data_entry_flow.AbortFlow("auth_lan")
        else:
            user_input = {
                CONF_INTEGRATION_TYPE:  self._default_integration_type,
                CONF_HOST:              self._default_host,
                CONF_PASSWORD:          self._default_password,
                CONF_SCAN_INTERVAL:     self._default_scan_interval,
                CONF_DELAY:             self._default_delay,
                CONF_11KWLIMIT:         self._default_11kWLimit
            }

        return self.async_show_form(
            step_id="user_lan",
            data_schema=vol.Schema({
                vol.Required(CONF_INTEGRATION_TYPE, default=user_input[CONF_INTEGRATION_TYPE]):
                    selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[INTG_TYPE.CHARGER.value, INTG_TYPE.CONTROLLER.value],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                            translation_key=CONF_INTEGRATION_TYPE,
                        )
                    ),
                vol.Required(CONF_HOST, default=user_input[CONF_HOST]): str,
                vol.Optional(CONF_PASSWORD, description={"suggested_value": user_input[CONF_PASSWORD]}): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                ),
                vol.Required(CONF_SCAN_INTERVAL, default=user_input[CONF_SCAN_INTERVAL]): int,
                vol.Optional(CONF_DELAY, default=user_input[CONF_DELAY]): bool,
                vol.Required(CONF_11KWLIMIT, default=user_input[CONF_11KWLIMIT]): bool,
            }),
            description_placeholders={"repo": "https://github.com/marq24/ha-goecharger-api2"},
            last_step=True,
            errors=self._errors
        )

    async def async_step_user_wan(self, user_input=None):
        """Handle a flow initialized by the user."""
        self._errors = {}

        # Uncomment the next 2 lines if only a single instance of the integration is allowed:
        # if self._async_current_entries():
        #     return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            a_user_pwd = user_input.get(CONF_PASSWORD, "").strip()
            #valid = await self._test_host(intg_type=user_input[CONF_INTEGRATION_TYPE], host=None, serial=user_input[CONF_ID], token=user_input[CONF_TOKEN])
            valid = await self._test_host(intg_type=user_input[CONF_INTEGRATION_TYPE], host=None, pwd=a_user_pwd, serial=user_input[CONF_ID], token=user_input[CONF_TOKEN])
            if valid:
                if len(a_user_pwd) == 0 and CONF_PASSWORD in user_input:
                    user_input.pop(CONF_PASSWORD)
                user_input[CONF_MODE] = WAN
                user_input[CONF_SCAN_INTERVAL] = max(30, user_input[CONF_SCAN_INTERVAL])
                user_input[CONF_ID] = self._serial
                user_input[CONF_MODEL] = self._model.split(' ')[0]
                if user_input[CONF_INTEGRATION_TYPE] == INTG_TYPE.CHARGER.value:
                    user_input[CONF_TYPE] = f"{self._type} [{self._model}] Cloud"
                    title = f"go-eCharger API v2 [{self._serial}] Cloud"
                else:
                    user_input[CONF_TYPE] = f"{self._type} Cloud"
                    title = f"go-eController API v2 [{self._serial}] Cloud"
                #else:
                #    user_input[CONF_TYPE] = f"{self._type} Cloud"
                #    title = f"go-eController API v2 [{self._serial}] Cloud"
                self._abort_if_unique_id_configured()
                if self.source == SOURCE_RECONFIGURE:
                    return self.async_update_reload_and_abort(entry=self._get_reconfigure_entry(), data=user_input)
                else:
                    return self.async_create_entry(title=title, data=user_input)
            else:
                self._errors["base"] = "auth_wan"
                raise data_entry_flow.AbortFlow("auth_wan")
        else:
            user_input = {
                CONF_INTEGRATION_TYPE:  self._default_integration_type,
                CONF_ID:                self._default_id,
                CONF_PASSWORD:          self._default_password,
                CONF_TOKEN:             self._default_token,
                CONF_SCAN_INTERVAL:     self._default_scan_interval if self.source == SOURCE_RECONFIGURE else 120,
                CONF_DELAY:             self._default_delay
            }

        return self.async_show_form(
            step_id="user_wan",
            data_schema=vol.Schema({
                vol.Required(CONF_INTEGRATION_TYPE, default=user_input[CONF_INTEGRATION_TYPE]):
                    selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[INTG_TYPE.CHARGER.value, INTG_TYPE.CONTROLLER.value],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                            translation_key=CONF_INTEGRATION_TYPE,
                        )
                    ),
                vol.Required(CONF_ID, default=user_input[CONF_ID]): str,
                vol.Required(CONF_TOKEN, description={"suggested_value": user_input[CONF_TOKEN]}): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                ),
                vol.Optional(CONF_PASSWORD, description={"suggested_value": user_input[CONF_PASSWORD]}): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                ),
                vol.Required(CONF_SCAN_INTERVAL, default=user_input[CONF_SCAN_INTERVAL]): int,
                vol.Optional(CONF_DELAY, default=user_input[CONF_DELAY]): bool,
            }),
            description_placeholders={"repo": "https://github.com/marq24/ha-goecharger-api2"},
            last_step=True,
            errors=self._errors
        )

    async def _check_ws_connection_and_flags(self, client:GoeChargerApiV2Bridge):
        # the HAI flag, is the flag that indicates if the HTTPv2 LOCAL API is enabled
        # the CAE flag, is the flag that indicates if the HTTPv2 CLOUD API is enabled
        ret_val = False

        # the TargetedEvent has internally a list of API keys that are required/checked before the event will
        # notify to be set...
        ready_event = TargetedEvent(is_charger=client.isCharger)
        _ws_start_task = self.hass.async_create_background_task(client.ws_connect(a_event=ready_event, keep_ws_states_after_close=True), "ws_connection_check")
        try:
            _LOGGER.debug("_check_ws_connection_and_flags(): Waiting for the ws connection to be established (max 30 seconds)")
            await asyncio.wait_for(ready_event.wait(), timeout=30.0)
            if ready_event.has_errors():
                _LOGGER.debug(f"_check_ws_connection_and_flags(): ws connection failed! errors: {ready_event.errors}")
                return False

            if ready_event.is_set():
                ret_val = True

                # for now, we skip the HAI auto-enable... since in the case of the websocket implementation,
                # there is no need to enable it...
                val = client._ws_states.get(Tag.HAI.key, None)
                _LOGGER.debug(f"_check_ws_connection_and_flags(): ws connection established! and current value of HAI flag: {val}")
                # if val is not None:
                #     if not bool(val):
                #         _LOGGER.info(f"_check_ws_connection_and_flags(): setting HAI flag to TRUE -> enable the HTTP v2 API at the charger device")
                #         await client.write_value_to_key(Tag.HAI.key, True)
                #         await sleep(2)
                #         ret_val = True
                #     else:
                #         # HAI is enabled - nothing to do...
                #         ret_val = True
                # else:
                #     # There is NO 'hai' flag at all - this means that this device is not supporting a LOCAL http v2 API
                #     # so we must run/check how we can communicate with it at all?
                #     # OK fair enough, we have already communicated with the device via the websocket ;-)
                #     pass

        except asyncio.CancelledError as canceled:
            _LOGGER.debug(f"_check_ws_connection_and_flags(): ws connection check cancelled - no HAI flag found after 30 seconds")
            ret_val = False

        except asyncio.TimeoutError as timeout:
            _LOGGER.debug(f"_check_ws_connection_and_flags(): ws connection check Timeout - no HAI flag found after 30 seconds")
            ret_val = False

        finally:
            # Ensure background task is cleaned up
            _ws_start_task.cancel()

        try:
            await asyncio.wait_for(_ws_start_task, timeout=5.0)
        except asyncio.TimeoutError:
            _LOGGER.debug(f"_check_ws_connection_and_flags(): ws connection check Timeout - background task did not finish after 5 seconds")

        # we need some rest befor the code will fire another ws connection...
        try:
            await asyncio.sleep(2.5)
        except BaseException:
            pass

        return ret_val

    async def _test_host(self, intg_type:str, host:str, pwd:str, serial:str, token:str):
        try:
            session = async_create_clientsession(self.hass)
            client = GoeChargerApiV2Bridge(intg_type=intg_type, host=host, access_password=pwd, serial=serial, token=token, web_session=session,
                                           lang=self.hass.config.language.lower())

            # when the user has specified a password, then we will first try to establish a local WEBSOCKET connection
            # and try to read the 'hai' flag... if 'hai' is false, then we enable it...
            ws_test_ok = False
            if pwd is not None and len(str(pwd)) > 0:
                await self._check_ws_connection_and_flags(client)
                if client._ws_states is not None and len(client._ws_states) > 0:
                    _LOGGER.debug(f"_test_host(): ws check for '{host}' was successful")
                    ws_test_ok = True
                else:
                    _LOGGER.warning(f"_test_host(): Failed to establish ws connection and could not check flags for '{host}' - so we must fallback to the HTTP v2 API, and HAI or CAE must be enabled!")

            if ws_test_ok:
                # local v2 API
                has_hai = Tag.HAI.key in client._ws_states
                enabled_hai = False
                if has_hai:
                    enabled_hai = bool(client._ws_states[Tag.HAI.key])

                # cloud v2 API
                has_cae = Tag.CAE.key in client._ws_states
                enabled_cae = False
                if has_cae:
                    enabled_cae = bool(client._ws_states[Tag.CAE.key])

                # but at the end of the day, if the ws connection has returned any data,
                # we do not care about HAI or CAE flag - since we will just use
                # data received via ws..

            ret = await client.read_system()
            if ret is not None and len(ret) > 0:
                await client.read_versions()
                # self._oem = ret[Tag.OEM.key]
                self._type = str(ret[Tag.TYP.key]).replace('_', ' ')
                if intg_type == INTG_TYPE.CHARGER.value:
                    self._model = f"{ret[Tag.VAR.key]} kW"
                else:
                    # there is no model info for a controller... so we hardcode it,
                    # since it will be used anyhow only for 11/22kW Version detection...
                    self._model = "eControl" #f"{ret[Tag.FNA.key]}"

                self._serial = ret[Tag.SSE.key]
                _LOGGER.info(f"successfully validated host for '{intg_type}' -> result: {ret}")
                return True
        except ClientConnectionError as exc:
            _LOGGER.warning(f"Error while test credentials: {type(exc).__name__} {exc}")
        except Exception as exc:
            _LOGGER.error(f"Other Exception while test credentials: {type(exc).__name__} {exc}")
        return False

#     @staticmethod
#     @callback
#     def async_get_options_flow(config_entry):
#         return GoeChargerApiV2OptionsFlowHandler(config_entry)
#
#
# class GoeChargerApiV2OptionsFlowHandler(config_entries.OptionsFlow):
#     def __init__(self, config_entry):
#         """Initialize HACS options flow."""
#         if len(dict(config_entry.options)) == 0:
#             self.options = dict(config_entry.data)
#         else:
#             self.options = dict(config_entry.options)
#
#     async def async_step_init(self, user_input=None):  # pylint: disable=unused-argument
#         """Manage the options."""
#         if self.options.get(CONF_MODE, None) == WAN:
#             return await self.async_step_user_wan()
#         else:
#             return await self.async_step_user_lan()
#
#     async def async_step_user_lan(self, user_input=None):
#         """Handle a flow initialized by the user."""
#         interval = 5
#         step_type = "user_lan"
#         if user_input is not None:
#             user_input[CONF_SCAN_INTERVAL] = max(interval, user_input[CONF_SCAN_INTERVAL])
#             self.options.update(user_input)
#             return await self._update_options()
#
#         # is this the 11kW or the 22kW Version?
#         if self.options.get(CONF_INTEGRATION_TYPE, INTG_TYPE.CHARGER.value) == INTG_TYPE.CONTROLLER.value or int(self.options.get(CONF_MODEL)) == 11:
#             return self.async_show_form(
#                 step_id=step_type,
#                 data_schema=vol.Schema({
#                     vol.Required(CONF_SCAN_INTERVAL, default=self.options.get(CONF_SCAN_INTERVAL, interval)): int
#                 })
#             )
#         else:
#             return self.async_show_form(
#                 step_id=step_type,
#                 data_schema=vol.Schema({
#                     vol.Required(CONF_11KWLIMIT, default=self.options.get(CONF_11KWLIMIT, False)): bool,
#                     vol.Required(CONF_SCAN_INTERVAL, default=self.options.get(CONF_SCAN_INTERVAL, interval)): int
#                 })
#             )
#
#     async def async_step_user_wan(self, user_input=None):
#         """Handle a flow initialized by the user."""
#         interval = 30
#         step_type = "user_wan"
#         if user_input is not None:
#             user_input[CONF_SCAN_INTERVAL] = max(interval, user_input[CONF_SCAN_INTERVAL])
#             self.options.update(user_input)
#             return await self._update_options()
#
#         # is this the 11kW or the 22kW Version?
#         if self.options.get(CONF_INTEGRATION_TYPE, INTG_TYPE.CHARGER.value) == INTG_TYPE.CONTROLLER.value or int(self.options.get(CONF_MODEL)) == 11:
#             return self.async_show_form(
#                 step_id=step_type,
#                 data_schema=vol.Schema({
#                     vol.Required(CONF_SCAN_INTERVAL, default=self.options.get(CONF_SCAN_INTERVAL, interval)): int
#                 })
#             )
#         else:
#             return self.async_show_form(
#                 step_id=step_type,
#                 data_schema=vol.Schema({
#                     vol.Required(CONF_11KWLIMIT, default=self.options.get(CONF_11KWLIMIT, False)): bool,
#                     vol.Required(CONF_SCAN_INTERVAL, default=self.options.get(CONF_SCAN_INTERVAL, interval)): int
#                 })
#             )
#
#     async def _update_options(self):
#         return self.async_create_entry(title=self.config_entry.title, data=self.options)
