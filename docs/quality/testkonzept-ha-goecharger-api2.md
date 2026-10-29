# Testkonzept: `ha-goecharger-api2`

| | |
|---|---|
| **Gegenstand** | Automatisierte Tests der Home-Assistant-Integration `goecharger_api2` (go-eCharger, go-eController) |
| **Stand** | 2026-10-29, Fork `OliEder/ha-goecharger-api2`, Branch `tests/regression-suite` (Branch `tests/regression-suite`), aufbauend auf `main` bei `98af3e0` |
| **Bezug** | Architektur und Risiken: `arc42-ha-goecharger-api2.md` (Risiken R1 bis R29). Regeln: `CLAUDE.md` / `AGENTS.md` der Arbeitsumgebung. |
| **Status der Tests** | Die Tests liegen im Fork. Es gibt keinen PR an das Upstream-Repository. Das Dokument wurde mit KI-Unterstützung (Claude Code) erstellt und von Oliver geprüft. |

**Lesehinweis.** Alle Tests laufen mit Attrappen. Sie belegen, was der Code tut und was die Doku sagt, **nicht**, was ein echter Charger tut. Wo das für eine Aussage wichtig ist, steht es dabei.

---

## 1. Zweck und Geltungsbereich

**Zweck.** Die Tests sollen Regressionen in der Integration früh melden, bekannte Fehler sichtbar halten und die Übereinstimmung mit der offiziellen go-e-API-Dokumentation prüfen. Sie sind auch die Grundlage für spätere Änderungen und für Gespräche mit dem Maintainer.

**Im Geltungsbereich**
- Bridge (`pygoecharger_ha`): HTTP lokal und Cloud, WebSocket (Anmeldung, Nachrichten, Befehle).
- Koordinator: Lesen, Schreiben, Fehlerzähler, Pause, Neustart, Start (`ConfigEntryNotReady`).
- Dienste (`set_pv_data`, `stop_charging`), Multi-Charger-Register, Entladen von Entries.
- Config-Flow (Anlegen, Fehlerfälle), Migration der Config-Entries.
- Stabilität der Entity-IDs.
- Vertrag zwischen offizieller Schlüsseltabelle und `keys.py`.
- Das PV-Blueprint hat eigene Tests (240 Fälle, Branch `proposal/invalid-data-policy`). Sie sind **nicht** Teil dieses Konzepts.

**Nicht im Geltungsbereich (bewusst)**
- Prüfung gegen einen echten Charger im Dauerbetrieb, Last- und Leistungstests.
- Oberfläche von Home Assistant (Dashboards, Übersetzungen).
- MQTT, Modbus, OCPP-Protokolle und Grid-API (nutzt die Integration nicht).
- go-eController: Seine Schlüssel stehen nicht in der Charger-Doku, es fehlt eine Quelle für einen Vertrag.

---

## 2. Qualitätsziele, die geprüft werden

Aus den Qualitätsszenarien des arc42-Dokuments (Abschnitt 10.2):

| arc42 | Szenario | Wie geprüft |
|---|---|---|
| Q1 | Charger ist nicht erreichbar: keine Dauerlast, Erholung | `test_coordinator_failures.py` (Fehlerzähler, Pause, einmaliger Neustart) |
| Q2 | Firmware ändert Schlüssel | `test_versions_16a.py`, `test_api_contract.py` (nur Namen und Flags, nicht Inhalte) |
| Q3 | PV-Automation fällt aus: kein ungewolltes Netzladen | **nicht Teil dieser Suite** (liegt im Blueprint), nur `set_pv_data`-Eingaben in `test_service.py` |
| Q4 | `stop_charging` im WebSocket-Modus | `test_services_and_unload.py` |
| Q5 | Zwei Charger in einer Instanz | `test_services_and_unload.py` |
| Q6 | Zugangsdaten nicht lesbar | **nicht geprüft** |

---

## 3. Risikobasierte Priorisierung

Reihenfolge der Testtiefe nach Auswirkung auf den Betrieb (steuert ein physisches Gerät) und nach Eintrittswahrscheinlichkeit.

| Priorität | Bereich | Begründung |
|---|---|---|
| 1 | Steuerpfade: `stop_charging`, `set_pv_data`, Schreiben von Einstellungen | Wirken auf Stromfluss und Fahrzeug |
| 2 | Verbindungsverlust und Erholung (HTTP und WebSocket) | Häufigster Fehler im Alltag (WLAN, Router, Firmware-Update) |
| 3 | Anmeldung per WebSocket | Nachgebaut, nicht offiziell dokumentiert, bricht bei Firmware-Änderungen |
| 4 | Stabilität der Entity-IDs und Migration | Ein Fehler trifft alle Bestandsnutzer auf einmal |
| 5 | Vertrag zur offiziellen API | Früherkennung von Doku- und Code-Drift |
| 6 | Eingabevalidierung der Entitäten | Geringe Wirkung, Gerät begrenzt selbst |

**Abdeckung der Risiken aus arc42 (Abschnitt 11)**

| Risiko | Test | Stand |
|---|---|---|
| R1 `stop_charging` WebSocket (`TypeError`) | `test_stop_charging_in_websocket_mode_sends_lock_and_unlock` | behoben, Test grün |
| R1 Flag `_stop_in_progress` bleibt hängen | `test_failed_lock_write_...`, `test_failed_unlock_write_...` | `known_bug`, rot |
| R2 Multi-Charger-Register | `test_second_charger_is_reachable_...`, `test_reloaded_charger_...` | behoben, grün |
| R2 Standard-Charger wechselt nach Reload | `test_default_charger_does_not_change_after_reload` | `known_bug`, rot |
| R3 Zähler `ACTIVE_CHARGER_COUNTER` | zwei Tests in `test_services_and_unload.py` | `known_bug`, rot |
| R4 `__init__.py:674` | `test_write_multiple_keys_connection_error_is_counted` | behoben, grün |
| R5 `pgrid` ohne Endlichkeitsprüfung | `test_non_finite_grid_value_is_rejected` | `known_bug`, rot |
| R6 keine `unique_id` im Config-Flow (kein Schutz vor Doppelanlage) | – | **nicht abgedeckt** |
| R7 README „24 h“, Code „1 h“ | `test_read_all_reads_the_configuration_only_every_hour` | Code-Verhalten festgehalten (Abweichung zum README bleibt) |
| R8 Zugangsdaten | – | bewusst nicht Teil der Tests |
| R15 Cloud-Antwort 202 | `test_cloud_write_accepts_http_202` | `known_bug`, rot (nur nach Doku) |
| R16 WebSocket nicht dokumentiert | `test_ws_protocol.py`, `test_ws_login_failures.py` | Verhalten festgehalten |
| R17 Cloud `age` nicht gesetzt | – | **nicht abgedeckt** |
| R18 `ppv` negativ (Standby) | – | **nicht abgedeckt** |
| R20 alte Werte nach fehlgeschlagenem Lesen | `test_failed_full_read_keeps_the_previous_states` | Verhalten festgehalten, Absicht ungeklärt |
| R21 Migration löscht Geräte | `test_version_2_0_deletes_the_devices_and_moves_to_2_1` | Verhalten festgehalten |
| Fehlermeldung bei `ConfigEntryNotReady` wird überdeckt (neu) | `test_missing_device_data_is_reported_with_its_own_message` | `known_bug`, rot |
| Fehlertext des Chargers gilt als Erfolg (neu) | `test_write_rejected_by_charger_returns_err` | `known_bug`, rot |

---

## 4. Teststufen und Testarten

| Stufe / Art | Zweck | Dateien |
|---|---|---|
| **Vertrag (Schema)** | Offizielle Schlüsseltabelle gegen `keys.py`, Filter und Entitäten | `test_api_contract.py`, `contract/` |
| **Komponente** | Bridge gegen gemockte HTTP-Schicht oder Attrappe der WebSocket-Verbindung | `test_bridge_http.py`, `test_ws_protocol.py`, `test_bridge.py` |
| **Nahtstelle (Seam)** | Koordinator, Bridge und Dienste im Zusammenspiel; Dienste gegen Register | `test_coordinator_failures.py`, `test_services_and_unload.py`, `test_coordinator_errors.py` |
| **Ablauf** | Config-Flow über die Home-Assistant-Flow-Verwaltung; Migration | `test_config_flow_failures.py`, `test_migration.py` |
| **Regression (Snapshot)** | Entity-IDs bleiben stabil | `test_entity_ids.py`, `snapshots/entity_ids.json` |
| **Entscheidungstabelle** | 16-A-Limit | `test_versions_16a.py` |
| **Negativ / Fehlerpfade** | Fehlschläge enden sauber | in allen Dateien, Schwerpunkt `test_ws_login_failures.py`, `test_coordinator_failures.py`, `test_config_flow_failures.py` |

Nicht vorhanden: Ende-zu-Ende gegen ein echtes Gerät, Komponententests der Entitäten (Wertdarstellung), Last- und Dauertests.

---

## 5. Teststrategie und Regeln

Verbindlich nach `CLAUDE.md` / `AGENTS.md`. Der Stand wird hier ehrlich festgehalten:

| Regel | Stand | Maßnahme |
|---|---|---|
| **Arrange-Act-Assert** für jeden Funktionstest | **Teilweise.** Der Aufbau ist meist erkennbar, aber nicht überall mit Leerzeilen oder Kommentaren getrennt. Es gibt keine Prüfung. | Neue Tests strikt so schreiben; vorhandene bei Gelegenheit umstellen |
| **Mindestens zwei Fehlerfälle** je Netzwerk- oder Dateizugriff | **Erfüllt** für HTTP-Lesen (3 Status plus ungültiges JSON), WebSocket-Anmeldung (über 10 Fälle), Config-Flow (6). **Knapp** für HTTP-Schreiben (Fehlertext, 500 ohne Inhalt, Zeitüberschreitung fehlen teilweise). Dateizugriffe gibt es nicht. | HTTP-Schreiben und Cloud-Statuscodes ergänzen |
| **Grenzwerte** (Null, negativ, maximale Länge) | **Nicht erfüllt.** Nur NaN/inf bei `set_pv_data`. | Siehe Abschnitt 10, soweit die Doku Bereiche nennt |
| **Seam-Tests** an neuen Nahtstellen | **Erfüllt** für Koordinator mit Bridge und Dienste mit Register. **Offen:** Entität mit Koordinator (Schreibpfad). | Entitäten-Tests ergänzen |
| **Formale API-Schemas** einbetten | **Teilweise.** Schlüsseltabelle als `api_keys.json`. **Offen:** Schema der HTTP-Endpunkte (lokal, Cloud). | Endpunkt-Schema aus `http-en.md` und `cloudapi-en.md` ableiten |

**Weitere Regeln dieses Konzepts**
1. Ein bekannter Fehler bekommt einen Test, der **rot** läuft (Marker `known_bug`). Kein `xfail`, damit der Fehler im Lauf sichtbar bleibt.
2. Jede Aussage über das Verhalten des Chargers braucht eine Quelle: offizielle Doku, Beobachtung am Gerät oder ausdrücklich „Vermutung“. Tests, die eine Vermutung festhalten, sagen das im Docstring.
3. Positivkontrolle: Jede Attrappe, die Fehler simuliert, hat einen Test, der zeigt, dass gültige Eingaben durchgehen.
4. Keine Tests gegen das Netzwerk. Das Test-Framework blockiert echte Sockets.

---

## 6. Testumgebung

- **Software:** Python 3.14.3, Home Assistant 2026.10.4 (festgelegt durch `pytest-homeassistant-custom-component`), `pytest`, `pytest-asyncio` (Modus `auto`). `msgpack` muss zusätzlich installiert werden, weil das Test-Framework die Anforderungen aus dem Manifest nicht installiert.
- **Ort:** lokale virtuelle Umgebung (Python 3.14, `pip install -r requirements_dev.txt`); die Tests laufen im Branch `tests/regression-suite`. Messbericht und Werkzeuge: `tests/reports/`, `tests/tools/`.
- **Aufruf:**
  - alles: `python -m pytest tests/integration`
  - blockierende Menge: `python -m pytest tests/integration -m "not known_bug and not needs_decision"`
- **Dauer:** rund 10 Sekunden für alle Tests.
- **Voraussetzungen:** kein Charger, kein Netzwerk, keine Zugangsdaten.

---

## 7. Testdaten und Attrappen

| Attrappe | Wofür | Grenze |
|---|---|---|
| `aioclient_mock` (Home Assistant) | HTTP-Antworten lokal und Cloud | Die Attrappe liefert kein `content_length`; Fälle mit `500` ohne/mit Inhalt stehen in `test_bridge.py` mit einer eigenen Antwort-Klasse |
| `FakeSocket`, `FakeSession` (`test_ws_login_failures.py`) | Skript der Anmeldung und der Nachrichten | Das Skript bildet die **nachgebaute** Anmeldung ab. Eine Änderung durch go-e erkennt sie nicht. |
| Fake-WebSocket-Objekt (`send_json`) | Ausgehende Befehle | wie oben |
| `MockConfigEntry` | Config-Entries für Koordinator, Migration, Flow | – |
| `api_keys.json` | Offizielle Schlüsseltabelle (Namen, R/W, Typ, Kategorie) | Bei 98 von 272 Zeilen steht als Typ nur `TYPE`; keine Beschreibungen gespeichert (kein Lizenztext im offiziellen Repo) |
| Beispieldaten | `123456`, `192.0.2.10` (reservierter Bereich), erfundene Tokens | enthalten keine echten Daten |

**Grenze aller Attrappen:** Sie kodieren unsere Annahmen. Dass der Charger sich so verhält, belegt erst der lesende Abgleich am echten Gerät (Abschnitt 10, Punkt 4).

---

## 8. Marker und Blockier-Regeln

| Marker | Bedeutung | Blockiert? |
|---|---|---|
| `known_bug` | Der Code hat einen nicht behobenen Fehler; der Test beschreibt das richtige Verhalten | Ja: der Gesamtlauf ist rot, bis der Fehler behoben ist |
| `needs_decision` | Doku und Code weichen ab; unklar, ob gewollt oder Doku-Lücke | Nein: rot, aber nicht blockierend, bis entschieden ist |
| (kein Marker) | Verhalten, das funktionieren muss | Ja |

- Eine **neue** Abweichung zur Doku hat keinen Marker und blockiert sofort.
- Wird ein Fehler behoben, schlägt das Entfernen des Markers nicht automatisch an. Der Test wird **grün**, der Marker bleibt stehen und muss von Hand entfernt werden. Das ist ein Nachteil gegenüber `xfail(strict)`. Mitigation: nach jedem Update von `main` die Marker prüfen (`-m known_bug -q`).
- Blockierende Menge heute: grün (958 bestanden). Bekannte Fehler: 29 (15 `known_bug`, 14 `needs_decision`).

---

## 9. Aktueller Stand

Stand 2026-10-29 (Messung nach dem Ausbau um Controller-Vertrag, Wertebereiche und Transportvergleich), Branch `tests/regression-suite` im Fork. Details und Rohdaten: `tests/reports/2026-10-29/testreport.md`.

| Kennzahl | Wert |
|---|---|
| Tests gesammelt | 987, davon 420 parametrisierte Vertragsprüfungen je Schlüssel; **567 Verhaltens- und Fehlertests** |
| Ergebnis | 958 bestanden, 29 beabsichtigt rot (15 `known_bug`, 14 `needs_decision`); blockierende Menge 958 von 958 grün |
| Zeilenabdeckung | 92,9 % (vorher 55,2 %) |
| Zweigabdeckung | 84,9 % (vorher 31,8 %) |
| **Pfadabdeckung** (obere Schranke der Basispfade) | **61 %** alle Funktionen, **62 %** Kernmodule (vorher 20 % und 27 %) |
| Pfadabdeckung nach Kritikalität | K1 kritisch 66 %, K2 hoch 60 %, K3 mittel 64 %, K4 niedrig 48 % |

**Hinweis zur Pfadabdeckung:** `coverage.py` misst keine Pfade. Die Zahl stammt aus einem eigenen Plugin (`tests/tools/pathtracer.py`) und ist eine obere Schranke: Je Funktion zählt `min(beobachtete verschiedene Pfade, zyklomatische Komplexität)`. Sie lässt sich durch viele leicht verschiedene Eingaben steigern, ohne dass die Prüfung besser wird. Als Gegenprobe dienen die Mutationsprüfungen (Abschnitt 11).

| Datei | Inhalt |
|---|---|
| `test_api_contract.py` | Schlüsseltabelle gegen Code (420 Prüfungen) |
| `test_platform_values.py`, `test_platform_actions.py` | Wertdarstellung und Schreiben der Entitäten |
| `test_bridge_http.py`, `test_bridge_write_paths.py`, `test_bridge_polling.py` | HTTP-Anfragen, Schreibpfade, Lesezyklus |
| `test_ws_protocol.py`, `test_ws_login_failures.py`, `test_ws_connect_paths.py` | WebSocket: Nachrichten, Anmeldefehler, erfolgreiche Anmeldung und Schleife |
| `test_coordinator_failures.py`, `test_coordinator_runtime.py`, `test_coordinator_errors.py` | Fehlerzähler und Pause, Laufzeitpfade, Schreibfehler |
| `test_services_and_unload.py`, `test_services_and_setup.py`, `test_service.py` | Dienste, Register, Start und Ende eines Entries |
| `test_config_flow_failures.py`, `test_config_flow_paths.py`, `test_migration.py` | Config-Flow, Migration |
| `test_versions_16a.py`, `test_versions_transport_parity.py`, `test_entity_ids.py`, `test_bridge.py` | 16-A-Entscheidung (je nach Code-Stand), gleiches Ergebnis über HTTP und WebSocket, Entity-IDs, Schreibfehler der Bridge |
| `test_controller_contract.py` | Controller-Schlüssel gegen die Tabelle der go-eController-API (59 Prüfungen, 3 davon beabsichtigt rot) |
| `test_value_ranges.py` | Wertebereiche und Optionslisten aus dem Modbus-Profil (`amp`, `ama`, `lbr`, `frc`, `psm` u. a.) |

**Kritikalität der Pfade.** Jede Funktion ist einer Klasse zugeordnet (K1 ändert den Charger oder die Konfiguration, K2 Verbindung, Anmeldung, Start, K3 Anzeige, K4 Hilfsfunktionen). Die Zuordnung mit Begründung steht in `tests/tools/criticality.py`; der Report listet je Klasse die offenen Lücken (Abschnitt 5.1).

---

## 10. Lücken und Reihenfolge der nächsten Schritte

Erledigt seit der ersten Fassung: Plattformen, Lesezyklus im Polling, Schreibpfade, Koordinator-Laufzeit (16-A-Begrenzer, Wiederverbindung, Watchdog), Start und Ende eines Entries, erfolgreiche Anmeldung per WebSocket, Config-Flow-Pfade.

1. **K1 und K2 zuerst:** Der Report (Abschnitt 5.1) nennt je Funktion, wo sicher noch Basispfade fehlen, zum Beispiel in `check_and_write_to_16a`, `async_migrate_entry`, `ws_connect`, `read_versions` des Koordinators und `read_all_states`.
2. **R20 (alte Werte nach fehlgeschlagenem Lesen, Cloud) und R7 (Konfigurationsintervall):** Das Verhalten wird jetzt als Charakterisierung festgehalten (`test_failed_full_read_keeps_the_previous_states`); ein Test auf das gewünschte Verhalten fehlt, weil der Maintainer die Absicht nicht geklärt hat.
3. **Endpunkt-Verträge:** Cloud 403, 404, 422, 202, `age`, `last-modified`, `token` als GET-Parameter, mehrere Schlüssel in einem `set`; dazu ein Schema der Endpunkte aus `http-en.md` und `cloudapi-en.md`.
4. **Schreib-Kodierung je Schlüsseltyp** und **Grenzwerte** (Regel „explizite Grenzen“): nur dort, wo die Doku Typ oder Bereich nennt. Bei 98 Schlüsseln mit Platzhalter-Typ geht das nicht.
5. **Lesender Abgleich am echten Charger:** die Vertragsdaten (Statuscodes, Schlüssel, Typen) gegen `GET /api/status` prüfen. Nur lesend, kein `frc`, kein `ids`. Erst das belegt, dass die Attrappen dem Gerät entsprechen.
6. **Lese-Seite je Firmware:** Beispiel-Antworten aus den Listen für 59.4, 60.2, 60.3 und 60.4.
7. **Entity-Anlage:** `async_setup_entry` je Plattform und `entity.py` (Anzeigename) sind noch nicht ausgeführt.
8. **Verbindungsverlust im laufenden WebSocket-Betrieb:** Verfügbarkeit der Entitäten.
9. **R6 (`unique_id`):** Doppelanlage verhindern.
10. **Struktur:** Arrange-Act-Assert konsequent anwenden (die neuen Tests folgen dem Muster weitgehend, ohne dass es geprüft wird); Abdeckungs-Untergrenze und Marker-Warnung automatisieren.

---

## 11. Qualität der Tests selbst

- **Mutationsprüfung von Hand:** An verschiedenen Stellen wurden gezielt Fehler in den Code eingebaut und geprüft, ob ein Test rot wird. Bisher **33 Änderungen, alle erkannt**: 19 für die erste Suite (Wertkodierung, Präfixe, HMAC, Löschen der Geräte, 16-A-Grenze, Token, Anmeldeprüfungen, Neustart-Schwelle, Pausen, Flow-Abbruchgrund, Start-Prüfung, Schlüsselzuordnung) und 14 für die erweiterte Suite (Sensorfaktor, Fahrzeugprofil, Schalter-Regeln, Hibernation-Grenze, Konfigurations-Wiederholung, 16-A-Grenze im Begrenzer, Cloud-Fahrzeugprüfung, Zähler, Mindestintervall, Standard-Hash, Temperatur-Sensoren des Core, `ids`-Flag, Null-als-Null). **Eine** Änderung (Temperatur-Sensoren des Core) wurde zuerst nicht erkannt; ein zusätzlicher Testfall schloss die Lücke. Die Prüfung ist **nicht automatisiert** und deckt nicht den gesamten Code ab.
- **Positivkontrollen** für die Attrappen (Anmeldung, Config-Flow).
- **Stabilität:** Die blockierende Menge lief dreimal hintereinander grün (kein flackerndes Verhalten festgestellt).
- **Unabhängige Zweitprüfung:** für die Tests selbst nicht durchgeführt.
- **Bekannte Schwächen:** Die Zahl 420 in der Vertragsdatei verzerrt die Gesamtzahl; die Pfadzahl ist eine obere Schranke und steigerbar; die Attrappen kodieren unsere Annahmen.

---

## 12. Pflege und Änderungsprozess

| Anlass | Vorgehen |
|---|---|
| go-e veröffentlicht neue Doku | `generate_api_keys.py` mit neuem Commit ausführen, Diff prüfen, `classification.json` und `deviations.json` anpassen |
| Upstream behebt einen Fehler | Marker `known_bug` entfernen, Test muss grün sein; ggf. Eintrag in `deviations.json` oder `classification.json` streichen |
| Upstream ändert Entity-IDs absichtlich | Snapshot mit `UPDATE_SNAPSHOT=1` neu erzeugen und den Diff prüfen; ein Änderungsvorschlag an Nutzer wäre ein Bruch für Bestandsnutzer |
| Neue Entität oder neuer Schlüssel | Vertragstest schlägt an; Schlüssel zuordnen oder in die Klassifikation aufnehmen |
| Abweichung `needs_decision` geklärt | Eintrag entfernen oder Doku-Lücke vermerken und Marker entfernen |

**Zuständig:** Oliver (Fork und Tests). Änderungen am Upstream-Repository macht ausschließlich der Maintainer.

---

## 13. Eintritts- und Abschlusskriterien

- **Vor jedem Push in den Fork:** blockierende Menge grün (`-m "not known_bug and not needs_decision"`).
- **Vor jedem Update auf einen neuen Upstream-Stand:** `main` holen, Gesamtlauf starten, neue Rotfälle einordnen (neuer Fehler oder behobener bekannter Fehler).
- **Abschluss des Testkonzepts „offizielle API“:** Punkte 1 bis 3 aus Abschnitt 10 umgesetzt, Punkt 4 mindestens einmal durchgeführt und dokumentiert.

---

## 14. Annahmen, Grenzen, offene Entscheidungen

- Die Tests prüfen den Code gegen Doku und gegen unsere Annahmen, nicht gegen das Gerät.
- Ob die 11 `known_bug`- und 14 `needs_decision`-Fälle Fehler sind, ist teils offen (siehe `tests/integration/contract/deviations.json`).
- Offen: Soll es Mutationstests automatisiert geben (zum Beispiel `mutmut`)? Das wäre ein Aufwand von einem halben bis einem Tag, ohne Gewähr für Nutzen bei einer Codebasis dieser Struktur.
