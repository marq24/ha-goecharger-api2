"""Criticality of functions (and with them of their paths) of the integration.

Rubric: criticality = impact of a wrong path on the user. Probability is not rated separately; it is
covered by looking at which functions run often (the report shows call counts).

K1 critical  : changes the charger, its limits or the HA configuration; a wrong path can lock the charger,
               send wrong values, delete devices/entities or switch off the services.
K2 high      : connection, login, recovery and start of the integration; a wrong path makes the integration
               unavailable or shows stale data.
K3 medium    : correctness of what is shown or detected (values, units, device type), without writing.
K4 low       : helpers, naming, icons, logging, constructors of small helper classes.
"""
import re

K1, K2, K3, K4 = "K1 critical", "K2 high", "K3 medium", "K4 low"

# exact assignments: (file, qualified name without class prefix handling) -> (class, reason)
EXACT = {
    # bridge: writing
    ("pygoecharger_ha/__init__.py", "GoeChargerApiV2Bridge.write_value_to_key"): (K1, "writes a value to the charger (HTTP or WebSocket)"),
    ("pygoecharger_ha/__init__.py", "GoeChargerApiV2Bridge.write_multiple_values_to_keys"): (K1, "writes several values (vehicle selection)"),
    ("pygoecharger_ha/__init__.py", "GoeChargerApiV2Bridge._write_values_int"): (K1, "evaluates the answer of the charger to write commands"),
    ("pygoecharger_ha/__init__.py", "GoeChargerApiV2Bridge._ws_send_command"): (K1, "sends and signs commands over WebSocket"),
    # coordinator: writing and limits
    ("__init__.py", "GoeChargerDataUpdateCoordinator.async_write_key"): (K1, "central write path with error pause"),
    ("__init__.py", "GoeChargerDataUpdateCoordinator.async_write_multiple_keys"): (K1, "multiple write path with error pause"),
    ("__init__.py", "GoeChargerDataUpdateCoordinator.handle_write_result"): (K1, "takes the write result into the data"),
    ("__init__.py", "check_and_write_to_16a"): (K1, "writes current limits to the charger at start"),
    ("__init__.py", "GoeChargerDataUpdateCoordinator.check_for_16a_limit"): (K1, "starts writing the 16 A limit back"),
    ("__init__.py", "async_migrate_entry"): (K1, "deletes devices and with them entities"),
    ("__init__.py", "async_unload_entry"): (K1, "removes the services set_pv_data and stop_charging"),
    # services
    ("service.py", "GoeChargerApiV2Service.set_pv_data"): (K1, "sends PV data; controls PV charging"),
    ("service.py", "GoeChargerApiV2Service.stop_charging"): (K1, "locks and unlocks the charger"),
    ("service.py", "GoeChargerApiV2Service.get_coordinator"): (K1, "chooses the charger for services"),
    ("service.py", "_is_finite_number"): (K1, "prevents invalid values going to the charger"),
    ("service.py", "add_config_entry_to_service"): (K1, "registry of the chargers for the services"),
    ("service.py", "remove_config_entry_from_service"): (K1, "registry of the chargers for the services"),
    ("service.py", "GoeChargerApiV2Service.__init__"): (K1, "registry of the chargers for the services"),
    # entities that write
    ("number.py", "GoeChargerNumber.async_set_native_value"): (K1, "writes number values (currents, limits)"),
    ("number.py", "GoeChargerNumber.check_amp_min_max"): (K1, "automatically triggers setting amp"),
    ("select.py", "GoeChargerSelect.async_select_option"): (K1, "writes a selection, including the vehicle profile with several values"),
    ("switch.py", "GoeChargerSwitch.async_turn_on"): (K1, "switches settings on the charger"),
    ("switch.py", "GoeChargerSwitch.async_turn_off"): (K1, "switches settings on the charger"),
    ("button.py", "GoeChargerApiV2Button.async_press"): (K1, "triggers actions on the charger"),
    # connection, login, recovery, start
    ("pygoecharger_ha/__init__.py", "GoeChargerApiV2Bridge.ws_connect"): (K2, "login and message loop of the WebSocket connection"),
    ("pygoecharger_ha/__init__.py", "GoeChargerApiV2Bridge.extract_ws_message_data"): (K2, "processes all data and answers from the WebSocket"),
    ("pygoecharger_ha/__init__.py", "GoeChargerApiV2Bridge._read_filtered_data"): (K2, "central read path in polling"),
    ("pygoecharger_ha/__init__.py", "GoeChargerApiV2Bridge._read_all_data"): (K2, "reading all data over HTTP"),
    ("pygoecharger_ha/__init__.py", "GoeChargerApiV2Bridge.read_all_states"): (K2, "reading the status with hibernation"),
    ("pygoecharger_ha/__init__.py", "GoeChargerApiV2Bridge.read_all_config"): (K2, "reading the configuration with a retry pause"),
    ("pygoecharger_ha/__init__.py", "GoeChargerApiV2Bridge.read_all"): (K2, "read cycle"),
    ("pygoecharger_ha/__init__.py", "GoeChargerApiV2Bridge.read_versions"): (K2, "reads device and version data at start"),
    ("pygoecharger_ha/__init__.py", "GoeChargerApiV2Bridge.read_system"): (K2, "reads system data"),
    ("pygoecharger_ha/__init__.py", "GoeChargerApiV2Bridge.__init__"): (K2, "builds addresses for LAN, cloud and WebSocket"),
    ("pygoecharger_ha/__init__.py", "GoeChargerApiV2Bridge._ws_compute_hashed_password"): (K2, "password hash of the login"),
    ("pygoecharger_ha/__init__.py", "GoeChargerApiV2Bridge._ws_compute_auth_hash"): (K2, "answer to the login challenge"),
    ("pygoecharger_ha/__init__.py", "bcryptjs_base64_encode_serial"): (K2, "salt for the bcrypt login"),
    ("pygoecharger_ha/__init__.py", "GoeChargerApiV2Bridge._ws_decode_message"): (K2, "reads WebSocket messages"),
    ("pygoecharger_ha/__init__.py", "GoeChargerApiV2Bridge.ws_close"): (K2, "closes the connection cleanly"),
    ("pygoecharger_ha/__init__.py", "GoeChargerApiV2Bridge.ws_check_last_update"): (K2, "detects a dead connection"),
    ("pygoecharger_ha/__init__.py", "GoeChargerApiV2Bridge._ws_notify_for_new_data"): (K2, "passes new data on to HA"),
    ("pygoecharger_ha/__init__.py", "TargetedEvent.check_and_set"): (K2, "reports that the start data is complete"),
    ("pygoecharger_ha/__init__.py", "TargetedEvent.__init__"): (K2, "defines the required keys for the start"),
    ("__init__.py", "async_setup_entry"): (K2, "start of the integration"),
    ("__init__.py", "GoeChargerDataUpdateCoordinator._async_update_data"): (K2, "read cycle with error pause"),
    ("__init__.py", "GoeChargerDataUpdateCoordinator._handle_client_connection_error"): (K2, "error counter and restart"),
    ("__init__.py", "GoeChargerDataUpdateCoordinator.start_websocket_and_wait_for_first_data"): (K2, "start of the WebSocket connection"),
    ("__init__.py", "GoeChargerDataUpdateCoordinator.force_async_update_now"): (K2, "forces a new WebSocket connection"),
    ("__init__.py", "GoeChargerDataUpdateCoordinator._async_watchdog_check"): (K2, "reconnect"),
    ("__init__.py", "GoeChargerDataUpdateCoordinator._check_for_ws_task_and_cancel_if_running"): (K2, "reconnect"),
    ("__init__.py", "GoeChargerDataUpdateCoordinator.start_watchdog"): (K2, "reconnect"),
    ("__init__.py", "GoeChargerDataUpdateCoordinator.stop_watchdog"): (K2, "reconnect"),
    ("__init__.py", "GoeChargerDataUpdateCoordinator.trigger_restart_delayed"): (K2, "restart after persistent errors"),
    ("__init__.py", "GoeChargerDataUpdateCoordinator.clear_data"): (K2, "clean-up on unload"),
    ("__init__.py", "GoeChargerDataUpdateCoordinator.read_versions"): (K2, "detects device type, 16 A limit and cards"),
    ("__init__.py", "entry_update_listener"): (K2, "reloads the entry on changes"),
    ("config_flow.py", "GoeChargerApiV2FlowHandler._test_host"): (K2, "checks access during setup"),
    ("config_flow.py", "GoeChargerApiV2FlowHandler._check_ws_connection_and_flags"): (K2, "checks the WebSocket during setup"),
    ("config_flow.py", "GoeChargerApiV2FlowHandler.async_step_user_lan"): (K2, "local setup"),
    ("config_flow.py", "GoeChargerApiV2FlowHandler.async_step_user_wan"): (K2, "cloud setup"),
    ("config_flow.py", "GoeChargerApiV2FlowHandler.async_step_reconfigure"): (K2, "reconfiguration"),
    ("config_flow.py", "GoeChargerApiV2FlowHandler.async_step_user"): (K2, "setup, choice of LAN or cloud"),
}

# defaults by file for everything not listed
FILE_DEFAULT = {
    "sensor.py": (K3, "value display"),
    "binary_sensor.py": (K3, "value display"),
    "number.py": (K3, "value display"),
    "select.py": (K3, "value display"),
    "switch.py": (K3, "value display"),
    "button.py": (K4, "helper function"),
    "entity.py": (K4, "display name"),
    "pygoecharger_ha/keys.py": (K4, "helper function"),
}
NAME_DEFAULT = [
    (re.compile(r"is_valid_charger_entity|cards_as_object_present"), (K3, "determines which entities exist")),
    (re.compile(r"_read_filtered_data_from_ws_source|none_null_get|available_fields"), (K3, "reads from the data store")),
    (re.compile(r"clear_data|reset_stored_update_ts|force_config_update|ws_set_coordinator|cancel_existing_debouncer|request_update_in_sec|_debounce"), (K3, "data store and update")),
    (re.compile(r"_ws_normalize|ExpiringStore|\.get$|\.set$|_cleanup|__len__|__call__|device_info|unique_id|available$|_name_internal|_friendly_name|call_later_update_device_registry|async_setup$|has_errors|set_error|__hash__|__str__"), (K4, "helper function or display name")),
]


def classify(file: str, qual: str):
    if (file, qual) in EXACT:
        return EXACT[(file, qual)]
    if file in FILE_DEFAULT:
        return FILE_DEFAULT[file]
    for pattern, value in NAME_DEFAULT:
        if pattern.search(qual):
            return value
    return (K4, "helper function")
