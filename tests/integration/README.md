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
| `test_migration.py` | Config entry migration 1 -> 2.1 and 2.0 -> 2.1 | code |
| `test_services_and_unload.py` | `stop_charging`, multi-charger registry, unloading entries | reported bugs |
| `test_service.py` | `set_pv_data` input validation | reported bugs |
| `test_bridge.py`, `test_coordinator_errors.py` | write errors, connection error counting | reported bugs |

## Known bugs fail on purpose

A test marked `@pytest.mark.known_bug("...")` describes behaviour that is wrong today, so the run is
red until the bug is fixed. To get a green run without them: `python -m pytest tests/integration -m "not known_bug"`.
List them with `python -m pytest tests/integration -m known_bug -q`. When a bug is fixed, remove the marker.

## Entity ID snapshot

If an entity ID changes on purpose, regenerate the file and review the diff:
`UPDATE_SNAPSHOT=1 python -m pytest tests/integration/test_entity_ids.py -k snapshot`
Changing an ID breaks dashboards, automations and statistics of existing users.
