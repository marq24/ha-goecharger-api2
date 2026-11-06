# Test concept: `ha-goecharger-api2`

| | |
|---|---|
| **Subject** | Automated tests of the Home Assistant integration `goecharger_api2` (go-eCharger, go-eController) |
| **State** | 2026-10-30, `main` at `e6ee0c3` |
| **Reference** | Architecture: [`arc42-ha-goecharger-api2.md`](../architecture/arc42-ha-goecharger-api2.md); risk register: [`risks/`](../architecture/risks/README.md) ([R001](../architecture/risks/R001-stop-charging-locks-the-charger-after-a-write-error.md) to [R030](../architecture/risks/R030-max-ampere-is-reset-at-every-restart.md)); decisions: [`adr/`](../architecture/adr/README.md). Test strategy and rules: section 5. |
| **Status of the tests** | The tests have been in this repository since PR #178 (`738c3c6`); `.github/workflows/tests.yaml` has run them on pushes to `main` and on pull requests since PR #179. The document was written with AI assistance (Claude Code) and reviewed by a human. |

**Note.** All tests run with fakes. They show what the code does and what the documentation says, **not** what a real charger does. Where this matters for a statement, it is noted there.

---

## 1. Purpose and scope

**Purpose.** The tests should report regressions in the integration early, keep known defects visible and check the agreement with the official go-e API documentation. They are also the basis for later changes and for discussions with the maintainer.

**In scope**
- Bridge (`pygoecharger_ha`): HTTP local and cloud, WebSocket (login, messages, commands).
- Coordinator: reading, writing, error counter, pause, restart, start (`ConfigEntryNotReady`).
- Services (`set_pv_data`, `stop_charging`; `set_temporary_current_limit` not yet, see section 10), multi-charger registry, unloading entries.
- Config flow (create, error cases), migration of config entries.
- Stability of the entity IDs.
- Contract between the official key table and `keys.py`.
- The PV blueprint is **not** tested by this suite.

**Not in scope (deliberately)**
- Checks against a real charger in continuous operation, load and performance tests.
- User interface of Home Assistant (dashboards, translations).
- MQTT, Modbus, OCPP protocols and grid API (the integration does not use them).
- go-eController: its keys are not in the charger documentation, there is no source for a contract.

---

## 2. Quality goals that are checked

From the quality scenarios of the arc42 document (section 10.2):

| arc42 | Scenario | How checked |
|---|---|---|
| Q1 | Charger is not reachable: no permanent load, recovery | `test_coordinator_failures.py` (error counter, pause, single restart) |
| Q2 | Firmware changes keys | `test_versions_16a.py`, `test_api_contract.py` (names and flags only, not contents) |
| Q3 | PV automation fails: no unwanted grid charging | **not part of this suite** (lies in the blueprint), only `set_pv_data` inputs in `test_service.py` |
| Q4 | `stop_charging` in WebSocket mode | `test_services_and_unload.py` |
| Q5 | Two chargers in one instance | `test_services_and_unload.py` |
| Q6 | Credentials not readable | **not checked** |

---

## 3. Risk-based prioritisation

Order of test depth by impact on operation (controls a physical device) and by probability of occurrence.

| Priority | Area | Reason |
|---|---|---|
| 1 | Control paths: `stop_charging`, `set_pv_data`, writing settings | Act on current flow and vehicle |
| 2 | Connection loss and recovery (HTTP and WebSocket) | Most frequent error in daily use (WLAN, router, firmware update) |
| 3 | Login via WebSocket | Reverse engineered, not officially documented, breaks with firmware changes |
| 4 | Stability of the entity IDs and migration | A defect hits all existing users at once |
| 5 | Contract with the official API | Early detection of documentation and code drift |
| 6 | Input validation of the entities | Low impact, the device limits itself |

**Coverage of the risks from the [risk register](../architecture/risks/README.md)**

| Risk | Test | State |
|---|---|---|
| [R001](../architecture/risks/R001-stop-charging-locks-the-charger-after-a-write-error.md) `stop_charging` WebSocket (`TypeError`) | `test_stop_charging_in_websocket_mode_sends_lock_and_unlock` | fixed, test green |
| [R001](../architecture/risks/R001-stop-charging-locks-the-charger-after-a-write-error.md) flag `_stop_in_progress` stays stuck | `test_failed_lock_write_...`, `test_failed_unlock_write_...` | fixed since `9e7d62a`, green |
| [R002](../architecture/risks/R002-multi-charger-registry-incomplete.md) multi-charger registry | `test_second_charger_is_reachable_...`, `test_reloaded_charger_...` | fixed, green |
| [R002](../architecture/risks/R002-multi-charger-registry-incomplete.md) / ADR-0010 no silent default charger | `test_without_configid_and_with_two_chargers_no_charger_is_guessed`, `test_with_an_empty_registry_no_charger_can_be_chosen` | decision ADR-0010, green (skipped on versions before `4702213`) |
| [R003](../architecture/risks/R003-active-charger-counter-with-controller-entries.md) counter `ACTIVE_CHARGER_COUNTER` | two tests in `test_services_and_unload.py` | fixed since `eb5da46`, green |
| [R004](../architecture/risks/R004-error-handling-for-multiple-writes-calls-the-wrong-sign.md) wrong signature in the error handling of multiple writes (`__init__.py:674`) | `test_write_multiple_keys_connection_error_is_counted` | fixed, green |
| [R005](../architecture/risks/R005-pgrid-without-a-finiteness-check.md) `pgrid` without finiteness check | `test_non_finite_grid_value_is_rejected` | fixed since `eb5da46`, green |
| [R006](../architecture/risks/R006-no-unique-id-in-the-config-flow.md) no `unique_id` in the config flow (no protection against creating twice) | – | **not covered** |
| [R007](../architecture/risks/R007-readme-and-code-state-different-read-intervals-for-the.md) README "24 h", code "1 h" | `test_read_all_reads_the_configuration_only_every_hour` | code behaviour recorded (deviation from the README remains) |
| [R008](../architecture/risks/R008-credentials-are-stored-in-plain-text-in-the-config-entr.md) credentials | – | deliberately not part of the tests |
| [R015](../architecture/risks/R015-cloud-documentation-names-http-202-for-api-set.md) cloud answer | `test_cloud_write_succeeds_with_http_200` | green; documentation says 202, the maintainer confirms 200 |
| [R016](../architecture/risks/R016-websocket-interface-is-not-officially-documented.md) WebSocket not documented | `test_ws_protocol.py`, `test_ws_login_failures.py` | behaviour recorded |
| [R017](../architecture/risks/R017-cloud-data-can-be-up-to-30-seconds-old.md) cloud `age` not set | – | **not covered** |
| [R018](../architecture/risks/R018-negative-ppv-standby-cannot-be-set.md) `ppv` negative (standby) | – | **not covered** |
| [R020](../architecture/risks/R020-old-values-stay-after-a-failed-read.md) old values after a failed read | `test_failed_full_read_keeps_the_previous_states` | behaviour recorded; intended according to the maintainer (#173) |
| [R021](../architecture/risks/R021-migration-from-2-0-to-2-1-deletes-all-devices.md) migration deletes devices | `test_version_2_0_deletes_the_devices_and_moves_to_2_1` | behaviour recorded |
| [R025](../architecture/risks/R025-specific-start-error-message-is-covered-up.md) message of `ConfigEntryNotReady` is covered up | `test_missing_device_data_is_reported_with_its_own_message` | fixed since `eb5da46`, green |
| [R024](../architecture/risks/R024-error-text-of-the-charger-counts-as-success.md) error text of the charger counts as success | `test_write_rejected_by_charger_returns_err` | green on `9e7d62a` |
| [R027](../architecture/risks/R027-false-error-after-a-successful-multiple-write.md) false `ERROR` after multiple write in WebSocket mode | `test_websocket_multi_write_logs_no_error_on_success` | fixed since `9e7d62a`, green |
| [R031](../architecture/risks/R031-stop-charging-does-not-check-the-unlock-and-may-report.md) `stop_charging` does not check the unlock | – | **not covered** |
| `set_temporary_current_limit`, `tcl`, acknowledged writing (PR #177) | – | **not covered** (section 10, item 11) |

---

## 4. Test levels and kinds

| Level / kind | Purpose | Files |
|---|---|---|
| **Contract (schema)** | Official key table against `keys.py`, filters and entities | `test_api_contract.py`, `contract/` |
| **Component** | Bridge against a mocked HTTP layer or a fake of the WebSocket connection | `test_bridge_http.py`, `test_ws_protocol.py`, `test_bridge.py` |
| **Interface (seam)** | Coordinator, bridge and services together; services against the registry | `test_coordinator_failures.py`, `test_services_and_unload.py`, `test_coordinator_errors.py` |
| **Flow** | Config flow through the Home Assistant flow manager; migration | `test_config_flow_failures.py`, `test_migration.py` |
| **Regression (snapshot)** | Entity IDs stay stable | `test_entity_ids.py`, `snapshots/entity_ids.json` |
| **Decision table** | 16 A limit | `test_versions_16a.py` |
| **Negative / error paths** | Failures end cleanly | in all files, focus on `test_ws_login_failures.py`, `test_coordinator_failures.py`, `test_config_flow_failures.py` |

Not present: end-to-end against a real device, component tests of the entities (value display), load and endurance tests.

---

## 5. Test strategy and rules

The basis is five test rules (Arrange-Act-Assert, two failure cases per external access, explicit boundary values, seam tests, formal API schemas). The state is recorded here honestly:

| Rule | State | Measure |
|---|---|---|
| **Arrange-Act-Assert** for every functional test | **Partly.** The structure is mostly recognisable but not everywhere separated by blank lines or comments. There is no check. | Write new tests strictly this way; convert existing ones when the occasion arises |
| **At least two failure cases** per network or file access | **Met** for HTTP reading (3 statuses plus invalid JSON), WebSocket login (more than 10 cases), config flow (6). **Tight** for HTTP writing (error text, 500 without content and timeout partly missing). There are no file accesses. | Add HTTP writing and cloud status codes |
| **Boundary values** (zero, negative, maximum length) | **Not met.** Only NaN/inf for `set_pv_data`. | See section 10, as far as the documentation names ranges |
| **Seam tests** at new interfaces | **Met** for coordinator with bridge and services with registry. **Open:** entity with coordinator (write path). | Add entity tests |
| **Embed formal API schemas** | **Partly.** Key table as `api_keys.json`. **Open:** schema of the HTTP endpoints (local, cloud). | Derive an endpoint schema from `http-en.md` and `cloudapi-en.md` |

**Further rules of this concept**
1. A known defect gets a test that runs **red** (marker `known_bug`). No `xfail`, so that the defect stays visible in the run.
2. Every statement about the behaviour of the charger needs a source: official documentation, observation on the device or explicitly "assumption". Tests that record an assumption say so in the docstring.
3. Positive control: every fake that simulates errors has a test that shows valid inputs go through.
4. No tests against the network. The test framework blocks real sockets.

---

## 6. Test environment

- **Software:** Python 3.14.3, Home Assistant 2026.10.4 (fixed by `pytest-homeassistant-custom-component`), `pytest`, `pytest-asyncio` (mode `auto`). `msgpack` must be installed in addition because the test framework does not install the requirements from the manifest.
- **Place:** local virtual environment (Python 3.14, `pip install -r requirements_dev.txt`); tools: `tests/tools/`; the measurement report is created by hand with `.github/workflows/test-report.yaml` (the stored reports under `tests/reports/` were removed).
- **Call:**
  - everything: `python -m pytest tests/integration`
  - blocking set: `python -m pytest tests/integration -m "not known_bug and not needs_decision"`
- **Duration:** about 10 seconds for all tests.
- **Prerequisites:** no charger, no network, no credentials.

---

## 7. Test data and fakes

| Fake | Used for | Limit |
|---|---|---|
| `aioclient_mock` (Home Assistant) | HTTP answers local and cloud | The fake provides no `content_length`; cases with `500` without/with content are in `test_bridge.py` with an own response class |
| `FakeSocket`, `FakeSession` (`test_ws_login_failures.py`) | Script of the login and the messages | The script reproduces the **reverse engineered** login. It does not detect a change by go-e. |
| Fake WebSocket object (`send_json`) | Outgoing commands | as above |
| `MockConfigEntry` | Config entries for coordinator, migration, flow | – |
| `api_keys.json` | Official key table (names, R/W, type, category) | For 98 of 272 rows the type is only `TYPE`; no descriptions are stored (no licence text in the official repo) |
| Sample data | `123456`, `192.0.2.10` (reserved range), invented tokens | contain no real data |

**Limit of all fakes:** they encode the assumptions of the tests. That the charger behaves this way is only proven by the reading comparison on a real device (section 10, item 4).

---

## 8. Markers and blocking rules

| Marker | Meaning | Blocks? |
|---|---|---|
| `known_bug` | The code has an unfixed defect; the test describes the correct behaviour | Yes: the full run is red until the defect is fixed |
| `needs_decision` | Documentation and code differ; unclear whether intended or a documentation gap | No: red, but not blocking until decided |
| (no marker) | Behaviour that must work | Yes |

- A **new** deviation from the documentation has no marker and blocks at once.
- When a defect is fixed, removing the marker does not trigger automatically. The test turns **green**, the marker stays and must be removed by hand. This is a disadvantage compared with `xfail(strict)`. Mitigation: check the markers after every update of `main` (`-m known_bug -q`).
- Blocking set today: green (972 passed, with PR #180). Open findings: 17, all `needs_decision` (14 deviations in `test_api_contract`, 3 controller keys). All `known_bug` are fixed and their markers removed.

---

## 9. Current state

State 2026-10-29 (measured after extending with controller contract, value ranges and transport comparison), `main` at `9e7d62a`. The coverage was measured before the latest bug fixes; `test-report.yaml` delivers a new report.

| Figure | Value |
|---|---|
| Tests collected | 989, of which 420 parametrised per-key contract checks; **569 behaviour and error tests** |
| Result | 972 passed, 17 intentionally red (all `needs_decision`); blocking set 972 of 972 green (with PR #180, otherwise 961 blocking and 28 red) |
| Line coverage | 92.9 % (before 55.2 %) |
| Branch coverage | 84.9 % (before 31.8 %) |
| **Path coverage** (upper bound of base paths) | **61 %** all functions, **62 %** core modules (before 20 % and 27 %) |
| Path coverage by criticality | K1 critical 66 %, K2 high 60 %, K3 medium 64 %, K4 low 48 % |

**Note on path coverage:** `coverage.py` does not measure paths. The figure comes from an own plugin (`tests/tools/pathtracer.py`) and is an upper bound: per function `min(observed distinct paths, cyclomatic complexity)` counts. It can be raised by many slightly different inputs without making the check better. The mutation checks serve as a counter-check (section 11).

| File | Content |
|---|---|
| `test_api_contract.py` | Key table against code (420 checks) |
| `test_platform_values.py`, `test_platform_actions.py` | Value display and writing of the entities |
| `test_bridge_http.py`, `test_bridge_write_paths.py`, `test_bridge_polling.py` | HTTP requests, write paths, read cycle |
| `test_ws_protocol.py`, `test_ws_login_failures.py`, `test_ws_connect_paths.py` | WebSocket: messages, login failures, successful login and loop |
| `test_coordinator_failures.py`, `test_coordinator_runtime.py`, `test_coordinator_errors.py` | Error counter and pause, runtime paths, write errors |
| `test_services_and_unload.py`, `test_services_and_setup.py`, `test_service.py` | Services, registry, start and end of an entry |
| `test_config_flow_failures.py`, `test_config_flow_paths.py`, `test_migration.py` | Config flow, migration |
| `test_versions_16a.py`, `test_versions_transport_parity.py`, `test_entity_ids.py`, `test_bridge.py` | 16 A decision (depending on the code state), same result over HTTP and WebSocket, entity IDs, write errors of the bridge |
| `test_controller_contract.py` | Controller keys against the table of the go-eController API (59 checks, 3 of them intentionally red) |
| `test_value_ranges.py` | Value ranges and option lists from the Modbus profile (`amp`, `ama`, `lbr`, `frc`, `psm` and others) |

**Criticality of the paths.** Every function is assigned to a class (K1 changes the charger or the configuration, K2 connection, login, start, K3 display, K4 helper functions). The assignment with reasons is in `tests/tools/criticality.py`; the report lists the open gaps per class (section 5.1).

---

## 10. Gaps and order of the next steps

Done since the first version: platforms, read cycle in polling, write paths, coordinator runtime (16 A limiter, reconnect, watchdog), start and end of an entry, successful login via WebSocket, config flow paths.

1. **K1 and K2 first:** the report (section 5.1) names per function where base paths are certainly still missing, for example in `check_and_write_to_16a`, `async_migrate_entry`, `ws_connect`, `read_versions` of the coordinator and `read_all_states`.
2. **[R020](../architecture/risks/R020-old-values-stay-after-a-failed-read.md) (old values after a failed read, cloud):** the behaviour is recorded as a characterisation (`test_failed_full_read_keeps_the_previous_states`); the maintainer confirmed in #173 that keeping the old values is intended, so no test for a different behaviour is planned. **[R007](../architecture/risks/R007-readme-and-code-state-different-read-intervals-for-the.md) (configuration interval):** the code behaviour is recorded; the README statement still differs.
3. **Endpoint contracts:** cloud 403, 404, 422, `age`, `last-modified`, `token` as a GET parameter, several keys in one `set`; plus a schema of the endpoints from `http-en.md` and `cloudapi-en.md`.
4. **Write encoding per key type** and **boundary values** (rule "explicit limits"): only where the documentation names type or range. For 98 keys with a placeholder type this is not possible.
5. **Reading comparison on a real charger:** check the contract data (status codes, keys, types) against `GET /api/status`. Reading only, no `frc`, no `ids`. Only this proves that the fakes correspond to the device.
6. **Read side per firmware:** sample answers from the lists for 59.4, 60.2, 60.3 and 60.4.
7. **Entity creation:** `async_setup_entry` per platform and `entity.py` (display name) are not yet exercised.
8. **Connection loss during running WebSocket operation:** availability of the entities.
9. **[R006](../architecture/risks/R006-no-unique-id-in-the-config-flow.md) (`unique_id`):** prevent creating a device twice.
10. **Structure:** apply Arrange-Act-Assert consistently (the new tests mostly follow the pattern without it being checked); automate a coverage lower bound and a marker warning.
11. **Temporary current limit and acknowledged writing (PR #177):** there are no tests of their own for `set_temporary_current_limit`, the `tcl` entity, the input check (`_TCLTagLogic`) and the acknowledged writing with a 3 second timeout (`require_ack`, `_ws_pending_ack`) (checked with `grep` in `tests/integration`). The test for `stop_charging` replaces `async_write_key` with a fake and therefore does not check the acknowledgement.

12. **Tests that assert the exact wording of messages ([R032](../architecture/risks/R032-tests-assert-the-exact-wording-of-messages.md)):** nine of the eleven uses of `match=` in `tests/integration` match a message text (two match an exception class name). A rewording by the maintainer breaks them without a change in behaviour (it did twice, see issue #172). Where the text is not the contract, assert the exception type and a stable part instead. To be discussed with the maintainer before anything is changed.

---

## 11. Quality of the tests themselves

- **Mutation check by hand:** faults were deliberately built into the code at various places and it was checked whether a test turns red. So far **33 changes, all detected**: 19 for the first suite (value encoding, prefixes, HMAC, deleting the devices, 16 A limit, token, login checks, restart threshold, pauses, flow abort reason, start check, key assignment) and 14 for the extended suite (sensor factor, vehicle profile, switch rules, hibernation limit, configuration retry, 16 A limit in the limiter, cloud vehicle check, counter, minimum interval, default hash, temperature sensors of the Core, `ids` flag, null as null). **One** change (temperature sensors of the Core) was not detected at first; an additional test case closed the gap. The check is **not automated** and does not cover the whole code.
- **Positive controls** for the fakes (login, config flow).
- **Stability:** the blocking set ran green three times in a row (no flaky behaviour observed).
- **Independent second check:** not carried out for the tests themselves.
- **Known weaknesses:** the number 420 in the contract file distorts the total; the path figure is an upper bound and can be raised; the fakes encode the assumptions of the tests.

---

## 12. Maintenance and change process

| Occasion | Procedure |
|---|---|
| go-e publishes new documentation | Run `generate_api_keys.py` with the new commit, check the diff, adjust `classification.json` and `deviations.json` |
| Upstream fixes a defect | Remove the marker `known_bug`, the test must be green; if applicable delete the entry in `deviations.json` or `classification.json` |
| Upstream changes entity IDs deliberately | Regenerate the snapshot with `UPDATE_SNAPSHOT=1` and check the diff; a change proposal to users would be a break for existing users |
| New entity or new key | The contract test fails; assign the key or add it to the classification |
| Deviation `needs_decision` clarified | Remove the entry or note the documentation gap and remove the marker |

**Responsible:** @OliEder (tests and documentation). Changes to the code are made by the maintainer.

---

## 13. Entry and exit criteria

- **Before every push and every pull request:** blocking set green (`-m "not known_bug and not needs_decision"`).
- **Before every update to a new upstream state:** fetch `main`, start the full run, classify new red cases (new defect or fixed known defect).
- **Completion of the test concept "official API":** items 1 to 3 from section 10 implemented, item 4 carried out and documented at least once.

---

## 14. Assumptions, limits, open decisions

- The tests check the code against documentation and against the assumptions of the tests, not against the device.
- Whether the 17 `needs_decision` cases (14 deviations from the key table, 3 controller keys) are defects is open (see `tests/integration/contract/deviations.json`).
- Open: should there be automated mutation tests (for example `mutmut`)? That would be an effort of half a day to one day, with no guarantee of benefit for a code base of this structure.
