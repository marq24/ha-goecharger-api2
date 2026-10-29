# Test tools

| File | Purpose |
|---|---|
| `pathtracer.py` | pytest plugin (`-p pathtracer`) that records which distinct execution paths each function takes (needs Python 3.12+, uses `sys.monitoring`). Empirical, not a proof of path coverage. |
| `criticality.py` | Criticality class (K1 to K4) of every function, with a reason. A judgement, not a measurement. |
| `pathmetric.py` | Prints the path coverage (upper bound of basis paths) per criticality class from a path-trace file. |
| `build_report.py` | Builds `testreport.md` from coverage, junit and path-trace data. |
| `measure.sh` | Runs everything and builds the report. |
| `release_check.sh` | Tests a release (or branch) of the upstream integration with the tests of this branch. Used by the workflow `.github/workflows/regression-on-release.yaml`. |

Needs `pytest-cov` and `radon` in addition to `requirements_dev.txt`.

## Testing every new upstream release automatically

`.github/workflows/regression-on-release.yaml` checks every three hours for a new release of `marq24/ha-goecharger-api2`. A new release is cloned fresh, the tests of this branch are copied into the clone, and the blocking tests run (`release_check.sh`). The result appears in the job summary; a red run means a blocking test failed. After the run the tag `tested/<release>` is set in the fork, so a release is tested once. The summary also lists known-bug tests that now pass, which means the bug looks fixed in that version.

Things to know:
- GitHub cannot start a workflow in a fork when another repository publishes a release. The workflow therefore polls.
- Scheduled workflows only run from the **default branch**. Either make `tests/regression-suite` the default branch of the fork, or copy the workflow file to `main`. Actions must be enabled for the fork (Actions tab).
- Nothing is rebased or merged by the workflow. It always tests a fresh clone of the upstream version, so the test branch does not have to follow upstream. The last step tries to fast-forward the fork's `main` to upstream and may fail harmlessly.
- The tests follow upstream `main`. An older release can fail a test that pins behaviour introduced later (for example the 16 A rule since commit `98af3e0` fails on release 2026.10.8), and a release that lacks functions the tests import cannot be collected. The summary says which case happened.
- Run it by hand: `tests/tools/release_check.sh [tag-or-branch]` (needs the test dependencies and the GitHub CLI for the latest release).

## Home Assistant version of the tests

`requirements_dev.txt` pins `pytest-homeassistant-custom-component` (currently 0.13.375, which brings Home Assistant 2026.10.4). A red run is therefore a change in the code under test, not a new Home Assistant. To see what a Home Assistant update breaks, start `regression-on-release.yaml` by hand with `home_assistant = latest`. To move the pin on purpose: run the suite with the new version, fix what broke, then raise the number in `requirements_dev.txt`. The tests run against the newest Home Assistant only; the minimum version named in `hacs.json` (2023.8.0) is not tested.
