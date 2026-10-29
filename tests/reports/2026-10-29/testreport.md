# Testreport und Testabdeckung: `ha-goecharger-api2`

| | |
|---|---|
| **Datum** | 2026-10-29 |
| **Geprüfter Code** | `marq24/ha-goecharger-api2` `main`, Commit `98af3e0` |
| **Tests** | Fork `OliEder/ha-goecharger-api2`, Branch `tests/regression-suite`, Commit `1d50118+local` |
| **Umgebung** | Python 3.14.3, Home Assistant 2026.10.4, coverage 7.16.2, radon 6.0.1 |
| **Rohdaten** | `coverage-all.json`, `coverage-blocking.json`, `coverage-baseline.json`, `junit-all.xml`, `pathtrace-all.json`, `pathtrace-baseline.json` in diesem Ordner (der HTML-Bericht ist nicht eingecheckt und lässt sich mit `tests/tools/measure.sh` neu erzeugen) |

## 1. Zusammenfassung

| Kennzahl | Wert |
|---|---|
| Tests gesammelt / bestanden / fehlgeschlagen | 911 / 885 / 26 (alle beabsichtigt: 12 `known_bug`, 14 `needs_decision`) |
| Blockierende Menge (ohne die beiden Marker) | 885 von 885 bestanden |
| **Zeilenabdeckung** (alle Tests) | **93.0 %** (2351 von 2529 Anweisungen) |
| **Zweigabdeckung** (alle Tests) | **85.0 %** (784 von 922 Zweigen) |
| **Pfadabdeckung** (obere Schranke der Basispfade, alle Funktionen) | **61 %** (484 von 794) |
| **Pfadabdeckung** (obere Schranke, nur die vier Kernmodule) | **62 %** (357 von 580) |
| Funktionen: nie ausgeführt / mit zu wenigen Pfaden / Pfadzahl nicht widerlegt | 14 / 58 / 48 (von 120) |

**Entwicklung gegenüber dem ersten Report (gleicher Tag, Stand vor dem Ausbau der Tests)**

| Kennzahl | Vorher | Jetzt |
|---|---|---|
| Verhaltens- und Fehlertests (ohne Vertragsprüfungen je Schlüssel) | 125 | 491 |
| Zeilenabdeckung | 55.2 % | 93.0 % |
| Zweigabdeckung | 31.8 % | 85.0 % |
| Pfadabdeckung (obere Schranke), alle Funktionen | 20 % | 61 % |
| Pfadabdeckung (obere Schranke), Kernmodule | 27 % | 62 % |

**Was das bedeutet:** Die Tests prüfen jetzt auch die Plattformen (Wertdarstellung, Schreiben) und die Laufzeitpfade des Koordinators. Zeilen- und Zweigabdeckung sind hoch, die Pfadabdeckung ist deutlich niedriger, weil sie verlangt, dass jede Funktion **viele verschiedene Kombinationen** von Entscheidungen durchläuft. Die Pfadzahl ist eine obere Schranke und kein Beleg für Vollständigkeit (Abschnitt 2).

## 2. Begriffe und Messverfahren (wichtig für die Einordnung)

| Kennzahl | Bedeutung | Gemessen mit |
|---|---|---|
| Zeilenabdeckung | Anteil der ausgeführten Anweisungen | `coverage.py` |
| Zweigabdeckung | Anteil der genommenen Verzweigungsausgänge (`if`/`else`, Schleife betreten/übersprungen, `try`/`except`). Entspricht der Entscheidungsabdeckung. | `coverage.py --cov-branch` |
| Pfadabdeckung | Anteil der möglichen Ausführungswege durch eine Funktion. **Wird von `coverage.py` nicht gemessen** und ist bei Schleifen und vielen Entscheidungen praktisch nicht vollständig erreichbar (Zahl der Pfade wächst exponentiell). | siehe unten |

**Wie die Pfadzahlen entstehen.** Ein eigenes Test-Plugin (`tests/tools/pathtracer.py`, nutzt `sys.monitoring`) zeichnet für **jeden Aufruf** einer Funktion die Folge der ausgeführten Zeilen auf. Schleifen werden verkürzt: eine Zeile zählt je Aufruf höchstens zweimal. Danach zählt es, wie viele **verschiedene** Pfade je Funktion im Testlauf vorkamen.

Diese Zahl wird mit der **zyklomatischen Komplexität** (CC, `radon`) verglichen. Die CC ist die Zahl der linear unabhängigen Basispfade einer Funktion. Daraus folgt eine **sichere Aussage in eine Richtung**:
- Wurden weniger verschiedene Pfade beobachtet als CC, sind **sicher nicht** alle Basispfade getestet.
- Wurden mindestens CC Pfade beobachtet, ist das **kein Beleg** für vollständige Abdeckung. Die Pfade können sich in denselben Entscheidungen ähneln.
- Die Kennzahl „Pfadabdeckung (obere Schranke)“ summiert je Funktion `min(beobachtete Pfade, CC)` und teilt durch die Summe der CC. Die tatsächliche Basispfadabdeckung ist **höchstens so hoch**.

Grenzen: Die Messung ist empirisch und heuristisch. Verschachtelte Funktionen werden der umgebenden Funktion zugerechnet oder nicht erfasst. Nur eine Tracing-Variante (Zeilenfolgen) wurde verwendet.

## 3. Testergebnisse

| Datei | Tests | fehlgeschlagen | Zeit |
|---|---|---|---|
| `test_api_contract.py` | 420 | 14 | 5.77 s |
| `test_bridge.py` | 3 | 0 | 0.06 s |
| `test_bridge_http.py` | 20 | 2 | 0.29 s |
| `test_bridge_polling.py` | 47 | 0 | 0.63 s |
| `test_bridge_write_paths.py` | 21 | 0 | 0.44 s |
| `test_config_flow_failures.py` | 8 | 0 | 0.17 s |
| `test_config_flow_paths.py` | 17 | 0 | 0.32 s |
| `test_coordinator_errors.py` | 2 | 0 | 0.03 s |
| `test_coordinator_failures.py` | 14 | 0 | 0.23 s |
| `test_coordinator_runtime.py` | 76 | 0 | 1.12 s |
| `test_entity_ids.py` | 10 | 0 | 0.16 s |
| `test_migration.py` | 3 | 0 | 0.04 s |
| `test_platform_actions.py` | 60 | 0 | 0.89 s |
| `test_platform_values.py` | 72 | 0 | 1.04 s |
| `test_service.py` | 7 | 3 | 0.10 s |
| `test_services_and_setup.py` | 39 | 1 | 0.68 s |
| `test_services_and_unload.py` | 10 | 6 | 0.22 s |
| `test_versions_16a.py` | 10 | 0 | 0.20 s |
| `test_ws_connect_paths.py` | 34 | 0 | 2.54 s |
| `test_ws_login_failures.py` | 13 | 0 | 0.96 s |
| `test_ws_protocol.py` | 25 | 0 | 0.58 s |

Hinweis: `test_api_contract.py` enthält 420 parametrisierte Vertragsprüfungen (je Schlüssel). Verhaltens- und Fehlerpfadtests insgesamt: 491.

**Gesamtdauer** 18.619 s.

## 4. Abdeckung je Datei

| Datei | Anweisungen | Zeilenabdeckung | Zweige | Zweigabdeckung | CC (Summe) | Pfade (obere Schranke) |
|---|---|---|---|---|---|---|
| `__init__.py` | 604 | 96 % | 266 | 89 % | 224 | 59 % |
| `binary_sensor.py` | 71 | 82 % | 34 | 68 % | 27 | 59 % |
| `button.py` | 31 | 61 % | 8 | 0 % | 8 | 38 % |
| `config_flow.py` | 178 | 96 % | 44 | 93 % | 42 | 64 % |
| `const.py` | 69 | 100 % | 0 | – | 0 | – |
| `entity.py` | 31 | 26 % | 14 | 0 % | 11 | 0 % |
| `number.py` | 94 | 81 % | 48 | 71 % | 50 | 44 % |
| `pygoecharger_ha/__init__.py` | 721 | 95 % | 302 | 91 % | 280 | 60 % |
| `pygoecharger_ha/const.py` | 61 | 100 % | 0 | – | 0 | – |
| `pygoecharger_ha/keys.py` | 255 | 99 % | 0 | – | 2 | 0 % |
| `select.py` | 100 | 88 % | 56 | 84 % | 36 | 72 % |
| `sensor.py` | 109 | 87 % | 60 | 82 % | 42 | 76 % |
| `service.py` | 104 | 97 % | 42 | 98 % | 34 | 85 % |
| `switch.py` | 101 | 88 % | 48 | 79 % | 38 | 74 % |

**Vergleich:** Nur die blockierenden Tests: Zeilen 92.9 %, Zweige 85.0 %. Die beabsichtigt roten Tests (bekannte Fehler und Abweichungen) verändern die Abdeckung kaum (0.1 Prozentpunkte bei den Zeilen).


## 5. Pfade nach Kritikalität

**Maßstab.** Kritikalität ist die Auswirkung eines falschen Pfades auf den Nutzer, nicht die Häufigkeit. Die Einstufung gilt für eine ganze Funktion und damit für alle ihre Pfade. Die Zuordnung steht in `tests/tools/criticality.py` (mit Begründung je Funktion) und ist eine Einschätzung, keine Messung.

| Klasse | Bedeutung | Beispiele |
|---|---|---|
| **K1 kritisch** | Ändert den Charger, seine Grenzen oder die HA-Konfiguration; ein falscher Pfad kann den Charger sperren, falsche Werte senden, Geräte löschen oder Dienste entfernen | `write_value_to_key`, `stop_charging`, `set_pv_data`, `check_and_write_to_16a`, `async_migrate_entry` |
| **K2 hoch** | Verbindung, Anmeldung, Erholung, Start; ein falscher Pfad macht die Integration unverfügbar oder zeigt alte Daten | `ws_connect`, `_async_update_data`, `async_setup_entry`, Config-Flow |
| **K3 mittel** | Korrektheit dessen, was angezeigt oder erkannt wird, ohne Schreiben | Wertdarstellung der Entitäten, `is_valid_charger_entity` |
| **K4 niedrig** | Hilfsfunktionen, Namen, Symbole, Logging | `_ws_normalize_value`, `unique_id`, Anzeigename |

| Klasse | Funktionen | CC (Basispfade) | Pfade vorher | Pfade jetzt (obere Schranke) | Zeilen | Zweige | nie ausgeführt |
|---|---|---|---|---|---|---|---|
| **K1 kritisch** | 24 | 195 | 22 % | **66 %** (128 von 195) | 96 % | 96 % | 0 |
| **K2 hoch** | 38 | 335 | 24 % | **60 %** (202 von 335) | 96 % | 91 % | 0 |
| **K3 mittel** | 33 | 171 | 1 % | **64 %** (109 von 171) | 78 % | 72 % | 6 |
| **K4 niedrig** | 25 | 93 | 34 % | **48 %** (45 von 93) | 71 % | 57 % | 8 |

Lesehilfe: „Pfade jetzt“ ist die obere Schranke der Basispfadabdeckung (Abschnitt 2). Die Spalten „Zeilen“ und „Zweige“ stehen für dieselben Funktionen und liegen viel höher; der Unterschied zeigt, wie viel strenger die Pfadabdeckung ist.

### 5.1 Offene Lücken in K1 und K2

Funktionen, bei denen **sicher** Basispfade fehlen (beobachtete Pfade unter der CC), geordnet nach Klasse und Zahl der fehlenden Pfade. „Fehlerpfad“ markiert nicht genommene Zweige, deren Zeile nach einem Fehlerfall aussieht (Schlüsselwörter wie `except`, `raise`, `error`, `warning`); das ist eine Heuristik.

**K1 kritisch**

| Funktion | CC | Pfade | fehlen mind. | Aufrufe | Warum kritisch | Nicht genommene Zweige |
|---|---|---|---|---|---|---|
| `check_and_write_to_16a` | 29 | 8 | 21 | 8 | schreibt beim Start Stromgrenzen an den Charger | Z.218 `if hass is not None:` (Normalpfad)<br>Z.220 `if a_entity_reg is not None:` (Normalpfad)<br>Z.271 `if a_res_key not in keys_to_patch:` (Normalpfad)<br>Z.280 `if a_res_key not in keys_to_patch:` (Normalpfad) |
| `async_migrate_entry` | 11 | 3 | 8 | 3 | löscht Geräte und damit Entitäten | Z.75 `if config_entry.data is not None and len(confi` (Normalpfad)<br>Z.77 `if config_entry.options is not None and len(co` (Normalpfad)<br>Z.89 `if a_device_reg is not None:` (Normalpfad) |
| `GoeChargerNumber.async_set_native_value` | 17 | 9 | 8 | 11 | schreibt Zahlenwerte (Ströme, Grenzen) | – |
| `GoeChargerApiV2Bridge._write_values_int` | 18 | 11 | 7 | 30 | wertet die Antwort des Chargers auf Schreibbefehle aus | – |
| `GoeChargerApiV2Bridge.write_multiple_values_to_keys` | 8 | 2 | 6 | 3 | schreibt mehrere Werte (Fahrzeugauswahl) | – |
| `GoeChargerNumber.check_amp_min_max` | 9 | 4 | 5 | 11 | löst automatisch das Setzen von amp aus | Z.143 `if amp_value_exceeds_limit:` (Normalpfad) |
| `GoeChargerSelect.async_select_option` | 16 | 13 | 3 | 15 | schreibt Auswahl, inklusive Fahrzeugprofil mit mehreren Werten | – |
| `GoeChargerApiV2Service.set_pv_data` | 14 | 11 | 3 | 19 | sendet PV-Daten; steuert das PV-Laden | – |
| `GoeChargerDataUpdateCoordinator.handle_write_result` | 9 | 7 | 2 | 11 | übernimmt das Schreibergebnis in die Daten | – |
| `_is_finite_number` | 3 | 1 | 2 | 28 | verhindert ungültige Werte an den Charger | Z.23 `if not isinstance(value, Number):` (Normalpfad) |
| `GoeChargerDataUpdateCoordinator.async_write_multiple_keys` | 5 | 4 | 1 | 4 | Mehrfach-Schreibpfad mit Fehlerpause | – |
| `GoeChargerApiV2Bridge.write_value_to_key` | 12 | 11 | 1 | 36 | schreibt einen Wert an den Charger (HTTP oder WebSocket) | – |

**K2 hoch**

| Funktion | CC | Pfade | fehlen mind. | Aufrufe | Warum kritisch | Nicht genommene Zweige |
|---|---|---|---|---|---|---|
| `GoeChargerApiV2Bridge.ws_connect` | 61 | 27 | 34 | 36 | Anmeldung und Nachrichtenschleife der WebSocket-Verbindung | Z.786 `if a_event is not None and not a_event.is_set(` (Normalpfad)<br>Z.807 `if a_event is not None and not a_event.is_set(` (Normalpfad)<br>Z.830 `if 'type' in self._ws_device_info:` (Normalpfad)<br>Z.841 `if a_event is not None and not a_event.is_set(` (Normalpfad) |
| `GoeChargerDataUpdateCoordinator.read_versions` | 37 | 21 | 16 | 28 | erkennt Gerätetyp, 16-A-Limit und Karten | Z.713 `if lc_model_type is not None:` (Normalpfad) |
| `GoeChargerApiV2Bridge.read_all_states` | 22 | 11 | 11 | 17 | Statuslesen mit Hibernation | Z.338 `elif self.isController:` (Normalpfad)<br>Z.377 `if len(self._states) > 0:` (Normalpfad) |
| `GoeChargerApiV2Bridge.extract_ws_message_data` | 20 | 11 | 9 | 25 | verarbeitet alle Daten und Antworten vom WebSocket | Z.1050 `if 'requestId' in data:` (Normalpfad)<br>Z.1056 `if status_data and len(status_data) > 0:` (Normalpfad)<br>Z.1059 `if the_request_payload is not None:` (Normalpfad)<br>Z.1064 `if the_request_payload is not None:` (Fehlerpfad) |
| `GoeChargerApiV2FlowHandler._test_host` | 14 | 7 | 7 | 18 | prüft Zugang beim Einrichten | – |
| `GoeChargerApiV2Bridge.read_all_config` | 11 | 5 | 6 | 8 | Konfigurationslesen mit Wiederholungs-Pause | Z.404 `if a_key in self._ws_states:` (Normalpfad) |
| `async_setup_entry` | 16 | 11 | 5 | 17 | Start der Integration | – |
| `GoeChargerDataUpdateCoordinator._async_update_data` | 10 | 5 | 5 | 19 | Lesezyklus mit Fehlerpause | Z.609 `if self.bridge.ws_connected and self._force_cl` (Normalpfad)<br>Z.623 `if new_data is not None and len(new_data) > 0:` (Normalpfad) |
| `GoeChargerApiV2Bridge.read_versions` | 14 | 9 | 5 | 18 | liest Geräte- und Versionsdaten beim Start | – |
| `GoeChargerApiV2Bridge.__init__` | 15 | 11 | 4 | 466 | bildet Adressen für LAN, Cloud und WebSocket | – |
| `GoeChargerApiV2Bridge._read_all_data` | 9 | 5 | 4 | 6 | Lesen aller Daten per HTTP | – |
| `bcryptjs_base64_encode_serial` | 6 | 2 | 4 | 8 | Salz für die bcrypt-Anmeldung | Z.1095 `while i < length:` (Normalpfad)<br>Z.1105 `if i >= length:` (Normalpfad) |
| `GoeChargerApiV2FlowHandler.async_step_user_wan` | 8 | 5 | 3 | 11 | Einrichtung Cloud | Z.209 `if len(a_user_pwd) == 0 and CONF_PASSWORD in u` (Normalpfad) |
| `GoeChargerApiV2FlowHandler._check_ws_connection_and_flags` | 7 | 4 | 3 | 4 | prüft WebSocket beim Einrichten | Z.284 `if ready_event.is_set():` (Normalpfad) |


## 6. Kritische Funktionen (nach Komplexität)

Kernmodule (`__init__.py` mit Koordinator, `pygoecharger_ha/__init__.py` mit Bridge, `service.py`, `config_flow.py`), sortiert nach Komplexität, gezeigt ab CC 4. „Pfade“ = beobachtete verschiedene Pfade, „CC“ = Basispfade.

| Funktion | CC | Aufrufe | Pfade | Zeilen | Zweige | Bewertung |
|---|---|---|---|---|---|---|
| `GoeChargerApiV2Bridge.ws_connect` (Bridge) | 61 | 36 | 27 | 96 % | 77 % | es fehlen mindestens 34 Basispfade |
| `GoeChargerDataUpdateCoordinator.read_versions` (Koordinator) | 37 | 28 | 21 | 100 % | 98 % | es fehlen mindestens 16 Basispfade |
| `check_and_write_to_16a` (Setup) | 29 | 8 | 8 | 100 % | 92 % | es fehlen mindestens 21 Basispfade |
| `GoeChargerApiV2Bridge.read_all_states` (Bridge) | 22 | 17 | 11 | 100 % | 93 % | es fehlen mindestens 11 Basispfade |
| `GoeChargerApiV2Bridge.extract_ws_message_data` (Bridge) | 20 | 25 | 11 | 95 % | 85 % | es fehlen mindestens 9 Basispfade |
| `GoeChargerApiV2Bridge._write_values_int` (Bridge) | 18 | 30 | 11 | 72 % | 100 % | es fehlen mindestens 7 Basispfade |
| `async_setup_entry` (Setup) | 16 | 17 | 11 | 100 % | 100 % | es fehlen mindestens 5 Basispfade |
| `GoeChargerApiV2Bridge.__init__` (Bridge) | 15 | 466 | 11 | 100 % | 100 % | es fehlen mindestens 4 Basispfade |
| `GoeChargerApiV2FlowHandler._test_host` (Flow) | 14 | 18 | 7 | 94 % | 100 % | es fehlen mindestens 7 Basispfade |
| `GoeChargerApiV2Bridge.read_versions` (Bridge) | 14 | 18 | 9 | 100 % | 100 % | es fehlen mindestens 5 Basispfade |
| `GoeChargerApiV2Service.set_pv_data` (Dienst) | 14 | 19 | 11 | 100 % | 100 % | es fehlen mindestens 3 Basispfade |
| `GoeChargerBaseEntity.__init__` (Entität) | 13 | 1908 | 13 | 100 % | 94 % | Pfadzahl nicht widerlegt |
| `GoeChargerApiV2Bridge._read_filtered_data` (Bridge) | 12 | 57 | 10 | 81 % | 100 % | es fehlen mindestens 2 Basispfade |
| `GoeChargerApiV2Bridge.write_value_to_key` (Bridge) | 12 | 36 | 11 | 100 % | 100 % | es fehlen mindestens 1 Basispfade |
| `async_migrate_entry` (Setup) | 11 | 3 | 3 | 86 % | 75 % | es fehlen mindestens 8 Basispfade |
| `GoeChargerDataUpdateCoordinator.call_later_update_device_registry` (Koordinator) | 11 | 5 | 5 | 94 % | 79 % | es fehlen mindestens 6 Basispfade |
| `GoeChargerDataUpdateCoordinator.is_valid_charger_entity` (Koordinator) | 11 | 14 | 7 | 100 % | 100 % | es fehlen mindestens 4 Basispfade |
| `GoeChargerApiV2Bridge.read_all_config` (Bridge) | 11 | 8 | 5 | 100 % | 94 % | es fehlen mindestens 6 Basispfade |
| `GoeChargerDataUpdateCoordinator._async_update_data` (Koordinator) | 10 | 19 | 5 | 88 % | 75 % | es fehlen mindestens 5 Basispfade |
| `GoeChargerBaseEntity._friendly_name_internal` (Entität) | 10 | 0 | 0 | 0 % | 0 % | nie ausgeführt |
| `GoeChargerDataUpdateCoordinator.__init__` (Koordinator) | 9 | 286 | 5 | 98 % | 90 % | es fehlen mindestens 4 Basispfade |
| `GoeChargerDataUpdateCoordinator.handle_write_result` (Koordinator) | 9 | 11 | 7 | 100 % | 100 % | es fehlen mindestens 2 Basispfade |
| `GoeChargerApiV2Bridge._read_all_data` (Bridge) | 9 | 6 | 5 | 71 % | 100 % | es fehlen mindestens 4 Basispfade |
| `GoeChargerApiV2Bridge._ws_normalize_value` (Bridge) | 9 | 271 | 6 | 100 % | 100 % | es fehlen mindestens 3 Basispfade |
| `GoeChargerApiV2FlowHandler.async_step_user_wan` (Flow) | 8 | 11 | 5 | 96 % | 90 % | es fehlen mindestens 3 Basispfade |
| `GoeChargerApiV2Bridge.write_multiple_values_to_keys` (Bridge) | 8 | 3 | 2 | 100 % | 100 % | es fehlen mindestens 6 Basispfade |
| `GoeChargerApiV2Service.stop_charging` (Dienst) | 8 | 11 | 9 | 100 % | 100 % | Pfadzahl nicht widerlegt |
| `GoeChargerDataUpdateCoordinator.start_websocket_and_wait_for_first_data` (Koordinator) | 7 | 6 | 6 | 96 % | 88 % | es fehlen mindestens 1 Basispfade |
| `GoeChargerApiV2FlowHandler.async_step_user_lan` (Flow) | 7 | 27 | 5 | 96 % | 90 % | es fehlen mindestens 2 Basispfade |
| `GoeChargerApiV2FlowHandler._check_ws_connection_and_flags` (Flow) | 7 | 4 | 4 | 86 % | 75 % | es fehlen mindestens 3 Basispfade |
| `bcryptjs_base64_encode_serial` (Bridge) | 6 | 8 | 2 | 92 % | 75 % | es fehlen mindestens 4 Basispfade |
| `async_unload_entry` (Setup) | 5 | 14 | 5 | 100 % | 100 % | Pfadzahl nicht widerlegt |
| `GoeChargerDataUpdateCoordinator.async_write_key` (Koordinator) | 5 | 7 | 5 | 100 % | 100 % | Pfadzahl nicht widerlegt |
| `GoeChargerDataUpdateCoordinator.async_write_multiple_keys` (Koordinator) | 5 | 4 | 4 | 82 % | 100 % | es fehlen mindestens 1 Basispfade |
| `TargetedEvent.check_and_set` (Bridge) | 5 | 5 | 2 | 100 % | 100 % | es fehlen mindestens 3 Basispfade |
| `GoeChargerApiV2Service.get_coordinator` (Dienst) | 5 | 38 | 5 | 100 % | 100 % | Pfadzahl nicht widerlegt |
| `GoeChargerDataUpdateCoordinator.force_async_update_now` (Koordinator) | 4 | 4 | 4 | 100 % | 100 % | Pfadzahl nicht widerlegt |
| `GoeChargerDataUpdateCoordinator._check_for_ws_task_and_cancel_if_running` (Koordinator) | 4 | 10 | 3 | 100 % | 100 % | es fehlen mindestens 1 Basispfade |
| `GoeChargerDataUpdateCoordinator._async_watchdog_check` (Koordinator) | 4 | 4 | 3 | 100 % | 83 % | es fehlen mindestens 1 Basispfade |
| `TargetedEvent.__init__` (Bridge) | 4 | 30 | 2 | 100 % | 75 % | es fehlen mindestens 2 Basispfade |
| `ExpiringStore._cleanup` (Bridge) | 4 | 22 | 2 | 100 % | 100 % | es fehlen mindestens 2 Basispfade |
| `GoeChargerApiV2Bridge.ws_close` (Bridge) | 4 | 25 | 3 | 100 % | 100 % | es fehlen mindestens 1 Basispfade |
| `GoeChargerApiV2Bridge._ws_decode_message` (Bridge) | 4 | 88 | 4 | 86 % | 83 % | Pfadzahl nicht widerlegt |

### 6.1 Nicht genommene Zweige in den wichtigsten Pfaden
Je Funktion die Zeilen, an denen mindestens ein Ausgang nie genommen wurde (bis zu sechs, Auswahl der Funktionen mit CC ab 8).

**`GoeChargerApiV2Bridge.ws_connect`** (pygoecharger_ha/__init__.py): Z. 786 `if a_event is not None and not a_event.is_set():`; Z. 807 `if a_event is not None and not a_event.is_set():`; Z. 830 `if 'type' in self._ws_device_info:`; Z. 841 `if a_event is not None and not a_event.is_set():`; Z. 860 `if a_event is not None and not a_event.is_set():`; Z. 865 `if not hasattr(self, 'access_password') or not self.access_password:`

**`GoeChargerDataUpdateCoordinator.read_versions`** (__init__.py): Z. 713 `if lc_model_type is not None:`

**`check_and_write_to_16a`** (__init__.py): Z. 218 `if hass is not None:`; Z. 220 `if a_entity_reg is not None:`; Z. 271 `if a_res_key not in keys_to_patch:`; Z. 280 `if a_res_key not in keys_to_patch:`

**`GoeChargerApiV2Bridge.read_all_states`** (pygoecharger_ha/__init__.py): Z. 338 `elif self.isController:`; Z. 377 `if len(self._states) > 0:`

**`GoeChargerApiV2Bridge.extract_ws_message_data`** (pygoecharger_ha/__init__.py): Z. 1050 `if 'requestId' in data:`; Z. 1056 `if status_data and len(status_data) > 0:`; Z. 1059 `if the_request_payload is not None:`; Z. 1064 `if the_request_payload is not None:`

**`GoeChargerBaseEntity.__init__`** (__init__.py): Z. 881 `elif len(description.tuple_idx) > 0:`

**`async_migrate_entry`** (__init__.py): Z. 75 `if config_entry.data is not None and len(config_entry.data) > 0:`; Z. 77 `if config_entry.options is not None and len(config_entry.options):`; Z. 89 `if a_device_reg is not None:`

**`GoeChargerDataUpdateCoordinator.call_later_update_device_registry`** (__init__.py): Z. 380 `if self.hass is not None:`; Z. 386 `if a_device_reg is not None:`; Z. 387 `if hasattr(a_device_reg, "async_get_device_by_identifier"):`

**`GoeChargerApiV2Bridge.read_all_config`** (pygoecharger_ha/__init__.py): Z. 404 `if a_key in self._ws_states:`

**`GoeChargerDataUpdateCoordinator._async_update_data`** (__init__.py): Z. 609 `if self.bridge.ws_connected and self._force_classic_requests is False:`; Z. 623 `if new_data is not None and len(new_data) > 0:`

**`GoeChargerDataUpdateCoordinator.__init__`** (__init__.py): Z. 363 `if config_entry.data.get(CONF_DELAY, False):`

**`GoeChargerApiV2FlowHandler.async_step_user_wan`** (config_flow.py): Z. 209 `if len(a_user_pwd) == 0 and CONF_PASSWORD in user_input:`

## 7. Nicht ausgeführte Funktionen im Kern

Funktionen der Kernmodule, die kein Test erreicht.

| Funktion | CC |
|---|---|
| `GoeChargerBaseEntity._friendly_name_internal` (__init__.py) | 10 |
| `GoeChargerBaseEntity._name_internal` (__init__.py) | 1 |
| `GoeChargerBaseEntity.device_info` (__init__.py) | 1 |
| `GoeChargerBaseEntity.available` (__init__.py) | 1 |

## 8. Plattformen und Hilfsdateien

Die Plattformen sind jetzt getestet (Wertdarstellung und Schreiben der Entitäten). Nicht ausgeführt bleiben das Anlegen der Entitäten (`async_setup_entry` je Plattform) und der Anzeigename in `entity.py`: `binary_sensor.py: async_setup_entry`, `button.py: async_setup_entry`, `entity.py: CustomFriendlyNameEntity._Entity__async_calculate_state`, `number.py: async_setup_entry`, `number.py: GoeChargerNumber.async_added_to_hass`, `select.py: async_setup_entry`, `sensor.py: async_setup_entry`, `switch.py: async_setup_entry`.

## 9. Einordnung

- **Pfadabdeckung:** Vollständige Pfadabdeckung ist hier weder erreichbar noch ein sinnvolles Ziel. Mit 98 von 580 Basispfaden der Kernmodule (17 %) bestimmen `ws_connect` (CC 61) und `read_versions` des Koordinators (CC 37) die Kennzahl; für sie wurden 27 und 21 verschiedene Pfade beobachtet. Funktionen mit sehr hoher CC sind in dieser Form schwer vollständig zu testen. Das ist ein Hinweis auf die Struktur des Codes, kein Vorwurf an die Tests.
- **Das Ziel von 60 % ist erreicht** (alle Funktionen 61 %, Kernmodule 62 %), aber die Zahl ist eine **obere Schranke** und lässt sich durch Tests mit nur leicht verschiedenen Eingaben steigern, ohne dass die Prüfung besser wird. Deshalb gelten die Mutationsprüfungen als Gegenprobe: 33 gezielte Code-Änderungen, alle wurden von den Tests erkannt (eine Lücke wurde erst nach einem zusätzlichen Test geschlossen).
- **Zeilen- und Zweigabdeckung sagen nichts über die Qualität der Prüfungen.** Alle Tests laufen mit Attrappen und sagen nichts darüber, ob der echte Charger sich so verhält.

## 10. Empfehlungen (nach Wirkung)

1. K1 und K2 zuerst: die Tabellen in Abschnitt 5.1 listen, wo noch Basispfade sicher fehlen. Dort stehen auch nicht genommene Fehlerpfade.
2. Fehlende Tests für bekannte Risiken: R20 (alte Werte nach fehlgeschlagenem Lesen, Cloud-Betrieb) und R7 (Konfigurationsintervall).
3. Lesenden Abgleich am echten Charger durchführen; erst er belegt, dass die Attrappen dem Gerät entsprechen.
4. Eine Untergrenze für die Abdeckung in den Lauf einbauen (zum Beispiel Zweigabdeckung der Kernmodule), damit sie nicht unbemerkt sinkt.
5. `ws_connect` und `read_versions` zerlegen, wenn sie später geändert werden; erst dann lassen sich ihre Pfade sinnvoll einzeln prüfen.
