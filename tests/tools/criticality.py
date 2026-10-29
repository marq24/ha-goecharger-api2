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

K1, K2, K3, K4 = "K1 kritisch", "K2 hoch", "K3 mittel", "K4 niedrig"

# exact assignments: (file, qualified name without class prefix handling) -> (class, reason)
EXACT = {
    # bridge: writing
    ("pygoecharger_ha/__init__.py", "GoeChargerApiV2Bridge.write_value_to_key"): (K1, "schreibt einen Wert an den Charger (HTTP oder WebSocket)"),
    ("pygoecharger_ha/__init__.py", "GoeChargerApiV2Bridge.write_multiple_values_to_keys"): (K1, "schreibt mehrere Werte (Fahrzeugauswahl)"),
    ("pygoecharger_ha/__init__.py", "GoeChargerApiV2Bridge._write_values_int"): (K1, "wertet die Antwort des Chargers auf Schreibbefehle aus"),
    ("pygoecharger_ha/__init__.py", "GoeChargerApiV2Bridge._ws_send_command"): (K1, "sendet und signiert Befehle per WebSocket"),
    # coordinator: writing and limits
    ("__init__.py", "GoeChargerDataUpdateCoordinator.async_write_key"): (K1, "zentraler Schreibpfad mit Fehlerpause"),
    ("__init__.py", "GoeChargerDataUpdateCoordinator.async_write_multiple_keys"): (K1, "Mehrfach-Schreibpfad mit Fehlerpause"),
    ("__init__.py", "GoeChargerDataUpdateCoordinator.handle_write_result"): (K1, "übernimmt das Schreibergebnis in die Daten"),
    ("__init__.py", "check_and_write_to_16a"): (K1, "schreibt beim Start Stromgrenzen an den Charger"),
    ("__init__.py", "GoeChargerDataUpdateCoordinator.check_for_16a_limit"): (K1, "startet das Zurückschreiben der 16-A-Grenze"),
    ("__init__.py", "async_migrate_entry"): (K1, "löscht Geräte und damit Entitäten"),
    ("__init__.py", "async_unload_entry"): (K1, "entfernt die Dienste set_pv_data und stop_charging"),
    # services
    ("service.py", "GoeChargerApiV2Service.set_pv_data"): (K1, "sendet PV-Daten; steuert das PV-Laden"),
    ("service.py", "GoeChargerApiV2Service.stop_charging"): (K1, "sperrt und entsperrt den Charger"),
    ("service.py", "GoeChargerApiV2Service.get_coordinator"): (K1, "wählt den Charger für Dienste"),
    ("service.py", "_is_finite_number"): (K1, "verhindert ungültige Werte an den Charger"),
    ("service.py", "add_config_entry_to_service"): (K1, "Register der Charger für die Dienste"),
    ("service.py", "remove_config_entry_from_service"): (K1, "Register der Charger für die Dienste"),
    ("service.py", "GoeChargerApiV2Service.__init__"): (K1, "Register der Charger für die Dienste"),
    # entities that write
    ("number.py", "GoeChargerNumber.async_set_native_value"): (K1, "schreibt Zahlenwerte (Ströme, Grenzen)"),
    ("number.py", "GoeChargerNumber.check_amp_min_max"): (K1, "löst automatisch das Setzen von amp aus"),
    ("select.py", "GoeChargerSelect.async_select_option"): (K1, "schreibt Auswahl, inklusive Fahrzeugprofil mit mehreren Werten"),
    ("switch.py", "GoeChargerSwitch.async_turn_on"): (K1, "schaltet Einstellungen am Charger"),
    ("switch.py", "GoeChargerSwitch.async_turn_off"): (K1, "schaltet Einstellungen am Charger"),
    ("button.py", "GoeChargerApiV2Button.async_press"): (K1, "löst Aktionen am Charger aus"),
    # connection, login, recovery, start
    ("pygoecharger_ha/__init__.py", "GoeChargerApiV2Bridge.ws_connect"): (K2, "Anmeldung und Nachrichtenschleife der WebSocket-Verbindung"),
    ("pygoecharger_ha/__init__.py", "GoeChargerApiV2Bridge.extract_ws_message_data"): (K2, "verarbeitet alle Daten und Antworten vom WebSocket"),
    ("pygoecharger_ha/__init__.py", "GoeChargerApiV2Bridge._read_filtered_data"): (K2, "zentraler Lesepfad im Polling"),
    ("pygoecharger_ha/__init__.py", "GoeChargerApiV2Bridge._read_all_data"): (K2, "Lesen aller Daten per HTTP"),
    ("pygoecharger_ha/__init__.py", "GoeChargerApiV2Bridge.read_all_states"): (K2, "Statuslesen mit Hibernation"),
    ("pygoecharger_ha/__init__.py", "GoeChargerApiV2Bridge.read_all_config"): (K2, "Konfigurationslesen mit Wiederholungs-Pause"),
    ("pygoecharger_ha/__init__.py", "GoeChargerApiV2Bridge.read_all"): (K2, "Lesezyklus"),
    ("pygoecharger_ha/__init__.py", "GoeChargerApiV2Bridge.read_versions"): (K2, "liest Geräte- und Versionsdaten beim Start"),
    ("pygoecharger_ha/__init__.py", "GoeChargerApiV2Bridge.read_system"): (K2, "liest Systemdaten"),
    ("pygoecharger_ha/__init__.py", "GoeChargerApiV2Bridge.__init__"): (K2, "bildet Adressen für LAN, Cloud und WebSocket"),
    ("pygoecharger_ha/__init__.py", "GoeChargerApiV2Bridge._ws_compute_hashed_password"): (K2, "Passwort-Hash der Anmeldung"),
    ("pygoecharger_ha/__init__.py", "GoeChargerApiV2Bridge._ws_compute_auth_hash"): (K2, "Antwort auf die Anmelde-Aufforderung"),
    ("pygoecharger_ha/__init__.py", "bcryptjs_base64_encode_serial"): (K2, "Salz für die bcrypt-Anmeldung"),
    ("pygoecharger_ha/__init__.py", "GoeChargerApiV2Bridge._ws_decode_message"): (K2, "liest WebSocket-Nachrichten"),
    ("pygoecharger_ha/__init__.py", "GoeChargerApiV2Bridge.ws_close"): (K2, "schließt die Verbindung sauber"),
    ("pygoecharger_ha/__init__.py", "GoeChargerApiV2Bridge.ws_check_last_update"): (K2, "erkennt eine tote Verbindung"),
    ("pygoecharger_ha/__init__.py", "GoeChargerApiV2Bridge._ws_notify_for_new_data"): (K2, "gibt neue Daten an HA weiter"),
    ("pygoecharger_ha/__init__.py", "TargetedEvent.check_and_set"): (K2, "meldet, dass die Startdaten vollständig sind"),
    ("pygoecharger_ha/__init__.py", "TargetedEvent.__init__"): (K2, "legt die Pflichtschlüssel für den Start fest"),
    ("__init__.py", "async_setup_entry"): (K2, "Start der Integration"),
    ("__init__.py", "GoeChargerDataUpdateCoordinator._async_update_data"): (K2, "Lesezyklus mit Fehlerpause"),
    ("__init__.py", "GoeChargerDataUpdateCoordinator._handle_client_connection_error"): (K2, "Fehlerzähler und Neustart"),
    ("__init__.py", "GoeChargerDataUpdateCoordinator.start_websocket_and_wait_for_first_data"): (K2, "Start der WebSocket-Verbindung"),
    ("__init__.py", "GoeChargerDataUpdateCoordinator.force_async_update_now"): (K2, "erzwingt neue WebSocket-Verbindung"),
    ("__init__.py", "GoeChargerDataUpdateCoordinator._async_watchdog_check"): (K2, "Wiederverbindung"),
    ("__init__.py", "GoeChargerDataUpdateCoordinator._check_for_ws_task_and_cancel_if_running"): (K2, "Wiederverbindung"),
    ("__init__.py", "GoeChargerDataUpdateCoordinator.start_watchdog"): (K2, "Wiederverbindung"),
    ("__init__.py", "GoeChargerDataUpdateCoordinator.stop_watchdog"): (K2, "Wiederverbindung"),
    ("__init__.py", "GoeChargerDataUpdateCoordinator.trigger_restart_delayed"): (K2, "Neustart nach Dauerfehlern"),
    ("__init__.py", "GoeChargerDataUpdateCoordinator.clear_data"): (K2, "Aufräumen beim Entladen"),
    ("__init__.py", "GoeChargerDataUpdateCoordinator.read_versions"): (K2, "erkennt Gerätetyp, 16-A-Limit und Karten"),
    ("__init__.py", "entry_update_listener"): (K2, "lädt den Entry bei Änderungen neu"),
    ("config_flow.py", "GoeChargerApiV2FlowHandler._test_host"): (K2, "prüft Zugang beim Einrichten"),
    ("config_flow.py", "GoeChargerApiV2FlowHandler._check_ws_connection_and_flags"): (K2, "prüft WebSocket beim Einrichten"),
    ("config_flow.py", "GoeChargerApiV2FlowHandler.async_step_user_lan"): (K2, "Einrichtung lokal"),
    ("config_flow.py", "GoeChargerApiV2FlowHandler.async_step_user_wan"): (K2, "Einrichtung Cloud"),
    ("config_flow.py", "GoeChargerApiV2FlowHandler.async_step_reconfigure"): (K2, "Umkonfigurieren"),
    ("config_flow.py", "GoeChargerApiV2FlowHandler.async_step_user"): (K2, "Einrichtung, Auswahl LAN oder Cloud"),
}

# defaults by file for everything not listed
FILE_DEFAULT = {
    "sensor.py": (K3, "Wertdarstellung"),
    "binary_sensor.py": (K3, "Wertdarstellung"),
    "number.py": (K3, "Wertdarstellung"),
    "select.py": (K3, "Wertdarstellung"),
    "switch.py": (K3, "Wertdarstellung"),
    "button.py": (K4, "Hilfsfunktion"),
    "entity.py": (K4, "Anzeigename"),
    "pygoecharger_ha/keys.py": (K4, "Hilfsfunktion"),
}
NAME_DEFAULT = [
    (re.compile(r"is_valid_charger_entity|cards_as_object_present"), (K3, "bestimmt, welche Entitäten es gibt")),
    (re.compile(r"_read_filtered_data_from_ws_source|none_null_get|available_fields"), (K3, "liest aus dem Datenspeicher")),
    (re.compile(r"clear_data|reset_stored_update_ts|force_config_update|ws_set_coordinator|cancel_existing_debouncer|request_update_in_sec|_debounce"), (K3, "Datenspeicher und Aktualisierung")),
    (re.compile(r"_ws_normalize|ExpiringStore|\.get$|\.set$|_cleanup|__len__|__call__|device_info|unique_id|available$|_name_internal|_friendly_name|call_later_update_device_registry|async_setup$|has_errors|set_error|__hash__|__str__"), (K4, "Hilfsfunktion oder Anzeigename")),
]


def classify(file: str, qual: str):
    if (file, qual) in EXACT:
        return EXACT[(file, qual)]
    if file in FILE_DEFAULT:
        return FILE_DEFAULT[file]
    for pattern, value in NAME_DEFAULT:
        if pattern.search(qual):
            return value
    return (K4, "Hilfsfunktion")
