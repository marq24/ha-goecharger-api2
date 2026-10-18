# Blueprint regression tests

From the repository root, in an isolated Python 3.12 environment:

```sh
python -m pip install -r tests/blueprints/requirements.txt
python -m pytest tests/blueprints -q
```

Tests load the actual blueprint YAML, resolve input defaults, render its Jinja
templates and evaluate the supported action/condition tree using synthetic
states and entity/config-entry registries. Routing tests additionally execute
the unchanged upstream `set_pv_data` method extracted from `service.py`, with
two fake LAN coordinators. No hardware, credentials or network is used.

This is not a Home Assistant runtime/schema validation or hardware test.
The state/registry helpers and action evaluator are test doubles; HA import,
selector UI and automation traces must still be checked in a disposable HA
instance before release. WAN filtering and firmware behaviour are outside
these tests. No claim is made that stopping transmission stops charging.
