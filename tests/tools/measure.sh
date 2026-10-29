#!/bin/sh
# Measures coverage and path coverage of the integration with the tests in tests/integration.
# Usage (from the repository root, with the test dependencies installed):
#   tests/tools/measure.sh [report-dir]
# Optional environment: TESTS_COMMIT (commit of the tests, default: HEAD), SOURCE_REF (name of the measured version in the report).
# Writes coverage, junit and path-trace data and builds testreport.md in the report directory.
set -e
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
OUT="${1:-$ROOT/tests/reports/$(date +%Y-%m-%d)}"
mkdir -p "$OUT"
COMMIT="$(git rev-parse --short HEAD)"

python -m pytest tests/integration -p no:cacheprovider -q \
  --cov=custom_components.goecharger_api2 --cov-branch \
  --cov-report=json:"$OUT/coverage-all.json" --cov-report=html:"$OUT/html-all" \
  --junitxml="$OUT/junit-all.xml" || true
python -m pytest tests/integration -p no:cacheprovider -q -m "not known_bug and not needs_decision" \
  --cov=custom_components.goecharger_api2 --cov-branch \
  --cov-report=json:"$OUT/coverage-blocking.json" --junitxml="$OUT/junit-blocking.xml"
PYTHONPATH="$ROOT/tests/tools" PATHTRACE_OUT="$OUT/pathtrace-all.json" \
  python -m pytest tests/integration -p pathtracer -p no:cacheprovider -q || true

# the report compares with a baseline; without one, the current data is used as baseline
[ -f "$OUT/coverage-baseline.json" ] || cp "$OUT/coverage-all.json" "$OUT/coverage-baseline.json"
[ -f "$OUT/pathtrace-baseline.json" ] || cp "$OUT/pathtrace-all.json" "$OUT/pathtrace-baseline.json"
python tests/tools/build_report.py "$OUT" "$ROOT" "$COMMIT" "${TESTS_COMMIT:-$COMMIT}"
