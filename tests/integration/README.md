# Regression tests

Tests for the integration without a charger, without network access and without credentials: the test
framework blocks real sockets, HTTP is mocked, the WebSocket connection is a fake object. Bridge and
coordinator are the real code.

```sh
python3.14 -m venv .venv && . .venv/bin/activate
python -m pip install -r requirements_dev.txt
python -m pytest tests/integration -q
```

Python 3.14 is required by the current `pytest-homeassistant-custom-component`, which also pins the
Home Assistant release it was built for. `msgpack` is listed in the manifest, but the test framework
does not install manifest requirements, so it is part of `requirements_dev.txt`.

## What is covered

| File | Area | Basis |
|---|---|---|
| `test_bridge_http.py` | HTTP requests and answers: filter, value encoding, cloud URL and token, error statuses | official go-e docs (`http-en.md`, `cloudapi-en.md`) |
| `test_ws_protocol.py` | WebSocket messages, password hashing, message signing, start condition | current implementation (protocol is not officially documented) |
| `test_versions_16a.py` | When a charger is limited to 16 A (cable limit, adapter, variant, option) | decision table; rows after 98af3e0 pin the current behaviour |
| `test_entity_ids.py` | Entity IDs and unique IDs stay stable (snapshot, uniqueness, LAN/WAN prefix) | snapshot in `snapshots/entity_ids.json` |
| `test_ws_login_failures.py` | WebSocket login failures: no serial, device offline, unknown hash, missing tokens, wrong password, timeout, unreachable device, dropped connection (plus a positive control) | current implementation |
| `test_coordinator_failures.py` | Error counter, 2 minute pause, restart after more than 5 errors, writes during an outage, `ConfigEntryNotReady` at start | code |
| `test_config_flow_failures.py` | Wrong, silent or unreachable devices and wrong cloud token end the flow with `auth_lan` / `auth_wan` and create no entry (plus a positive control) | code |
| `test_api_contract.py` | Official key table against the code: every documented key supported or classified, undocumented keys explained, read/write flag and category equal to the docs | `contract/api_keys.json` (generated from the official table) |
| `test_platform_values.py`, `test_platform_actions.py` | Entities: how raw values become states (sensor, number, select, switch, binary sensor) and what a write sends (number, select incl. car profiles, switch, button) | code |
| `test_bridge_polling.py` | Read cycle: hibernation, configuration refresh, versions, state housekeeping | code, README (hibernation) |
| `test_bridge_write_paths.py` | Every path from a value to the charger and back (HTTP, WebSocket, answers) | official docs, code |
| `test_ws_connect_paths.py` | Successful WebSocket logins and the message loop; address building | current implementation |
| `test_coordinator_runtime.py` | Write results, 16 A limiter, device detection, WebSocket start, reconnect, watchdog, housekeeping | code |
| `test_services_and_setup.py` | `set_pv_data`, `stop_charging`, charger lookup, setup and unload of entries | code |
| `test_config_flow_paths.py` | Successful setups, interval rules, reconfiguration, WebSocket check | code |
| `test_migration.py` | Config entry migration 1 -> 2.1 and 2.0 -> 2.1 | code |
| `test_services_and_unload.py` | `stop_charging`, multi-charger registry, unloading entries | reported bugs |
| `test_service.py` | `set_pv_data` input validation | reported bugs |
| `test_bridge.py`, `test_coordinator_errors.py` | write errors, connection error counting | reported bugs |

## Known bugs fail on purpose

A test marked `@pytest.mark.known_bug("...")` describes behaviour that is wrong today, so the run is
red until the bug is fixed. To get a green run without them: `python -m pytest tests/integration -m "not known_bug"`.
List them with `python -m pytest tests/integration -m known_bug -q`. When a bug is fixed, remove the marker.

## Markers

| Marker | Meaning | Blocking? |
|---|---|---|
| `known_bug` | the code has a bug that is not fixed yet | yes: the run is red until it is fixed |
| `needs_decision` | documentation and code differ; not yet decided whether this is intended or a documentation gap | no: fails on purpose, but is not blocking |

Blocking set only: `python -m pytest tests/integration -m "not known_bug and not needs_decision"`.
A new difference to the documentation has no marker, so it is blocking.

## Contract data (`contract/`)

- `api_keys.json`: key names, R/W, type and category from the official key table (no descriptions). Regenerate with `generate_api_keys.py` when go-e publishes a new version, and review the diff.
- `classification.json`: documented keys without a `Tag` (unsupported, decision open) and keys the code uses that the official table does not list, each with a reason.
- `deviations.json`: known differences between documentation and code (status `needs_decision`).

## Entity ID snapshot

If an entity ID changes on purpose, regenerate the file and review the diff:
`UPDATE_SNAPSHOT=1 python -m pytest tests/integration/test_entity_ids.py -k snapshot`
Changing an ID breaks dashboards, automations and statistics of existing users.

## Helpers

`factories.py` builds config entries, real coordinators and bridges (with an optional fake WebSocket connection) for the tests.
