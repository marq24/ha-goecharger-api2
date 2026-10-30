# Test tools

| File | Purpose |
|---|---|
| `pathtracer.py` | pytest plugin (`-p pathtracer`) that records which distinct execution paths each function takes (needs Python 3.12+, uses `sys.monitoring`). Empirical, not a proof of path coverage. |
| `criticality.py` | Criticality class (K1 to K4) of every function, with a reason. A judgement, not a measurement. |
| `pathmetric.py` | Prints the path coverage (upper bound of basis paths) per criticality class from a path-trace file. |
| `build_report.py` | Builds `testreport.md` from coverage, junit and path-trace data. |
| `measure.sh` | Runs everything and builds the report. |
| `release_check.sh` | Tests a release (or branch) of the upstream integration with the tests of this branch. Run by hand, for example to test an older release with the current tests. |

Needs `pytest-cov` and `radon` in addition to `requirements_dev.txt`.

## Running the tests automatically

`.github/workflows/tests.yaml` runs the blocking tests (`-m "not known_bug and not needs_decision"`) on every push to `main` and on every pull request that touches `custom_components/`, `tests/` or `requirements_dev.txt`. A second, non-blocking step runs the tests marked `known_bug` or `needs_decision` and lists them in the job summary; a test that passes there means the finding looks fixed and its marker can go.

`.github/workflows/test-report.yaml` builds the full report (coverage, paths, criticality) by hand for a release or branch.

Things to know:
- The tests follow `main`. An older release can fail a test that pins behaviour introduced later (for example the 16 A rule since commit `98af3e0` fails on release 2026.10.8), and a release that lacks functions the tests import cannot be collected.
- Test an older release by hand: `tests/tools/release_check.sh [tag-or-branch]` (needs the test dependencies and the GitHub CLI for the latest release).

## Home Assistant version of the tests

`requirements_dev.txt` pins `pytest-homeassistant-custom-component` (currently 0.13.375, which brings Home Assistant 2026.10.4). A red run is therefore a change in the code under test, not a new Home Assistant. To see what a Home Assistant update breaks, install the newest framework (`python -m pip install --upgrade pytest-homeassistant-custom-component`) and run the blocking set. To move the pin on purpose: run the suite with the new version, fix what broke, then raise the number in `requirements_dev.txt`. The tests run against the newest Home Assistant only; the minimum version named in `hacs.json` (2023.8.0) is not tested.
