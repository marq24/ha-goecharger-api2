import logging
from typing import Final, Any

import voluptuous as vol
from aiohttp import ClientConnectionError

from custom_components.goecharger_api2.pygoecharger_ha import GoeChargerApiV2Bridge, INTG_TYPE
from custom_components.goecharger_api2.pygoecharger_ha.keys import Tag
from homeassistant import config_entries, data_entry_flow
from homeassistant.config_entries import ConfigFlowResult, SOURCE_RECONFIGURE
from homeassistant.const import CONF_ID, CONF_HOST, CONF_PASSWORD, CONF_MODEL, CONF_TYPE, CONF_SCAN_INTERVAL, \
    CONF_TOKEN, CONF_MODE
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from .const import DOMAIN, CONF_11KWLIMIT, CONF_INTEGRATION_TYPE, LAN, WAN, CONFIG_VERSION, CONFIG_MINOR_VERSION

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
            self._default_id = entry_data.get(CONF_ID, "YOUR-SERIAL-HERE")
            self._default_password = entry_data.get(CONF_PASSWORD, "")
            self._default_integration_type = entry_data.get(CONF_INTEGRATION_TYPE, INTG_TYPE.CHARGER.value)
            self._default_token = entry_data.get(CONF_TOKEN, "YOUR-API-KEY-HERE")
            return await self.async_step_user_wan()
        else:
            self._selected_system = LAN
            self._default_scan_interval = entry_data.get(CONF_SCAN_INTERVAL, 30)
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
            valid = await self._test_host(intg_type=user_input[CONF_INTEGRATION_TYPE], host=user_input[CONF_HOST], pwd=user_input[CONF_PASSWORD], serial=None, token=None)
            if valid:
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
                vol.Optional(CONF_PASSWORD, default=user_input[CONF_PASSWORD]): str,
                vol.Required(CONF_SCAN_INTERVAL, default=user_input[CONF_SCAN_INTERVAL]): int,
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
            #valid = await self._test_host(intg_type=user_input[CONF_INTEGRATION_TYPE], host=None, serial=user_input[CONF_ID], token=user_input[CONF_TOKEN])
            valid = await self._test_host(intg_type=user_input[CONF_INTEGRATION_TYPE], host=None, pwd=user_input[CONF_PASSWORD], serial=user_input[CONF_ID], token=user_input[CONF_TOKEN])
            if valid:
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
                CONF_SCAN_INTERVAL:     self._default_scan_interval if self.source == SOURCE_RECONFIGURE else 120
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
                vol.Optional(CONF_PASSWORD, default=user_input[CONF_PASSWORD]): str,
                vol.Required(CONF_TOKEN, default=user_input[CONF_TOKEN]): str,
                vol.Required(CONF_SCAN_INTERVAL, default=user_input[CONF_SCAN_INTERVAL]): int,
            }),
            description_placeholders={"repo": "https://github.com/marq24/ha-goecharger-api2"},
            last_step=True,
            errors=self._errors
        )

    async def _test_host(self, intg_type:str, host:str, pwd:str, serial:str, token:str):
        try:
            session = async_create_clientsession(self.hass)
            client = GoeChargerApiV2Bridge(intg_type=intg_type, host=host, access_password=pwd, serial=serial, token=token, web_session=session,
                                           lang=self.hass.config.language.lower())

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
