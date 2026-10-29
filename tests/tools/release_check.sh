#!/bin/sh
# Tests a version of the upstream integration with the tests of this branch.
#
# Usage: tests/tools/release_check.sh [ref] [work-dir]
#   ref       tag or branch of marq24/ha-goecharger-api2 (default: the latest release)
#   work-dir  directory for the clone and the results (default: a temporary directory)
# Environment: PYTHON (default: python), UPSTREAM (default: https://github.com/marq24/ha-goecharger-api2)
#
# The upstream source is cloned into <work-dir>/src and only the directory tests/integration of this
# branch is copied into it (no rebase, no merge, nothing is pushed anywhere). Two runs follow:
#   1. the blocking tests (everything except the markers known_bug and needs_decision)
#   2. the tests marked known_bug or needs_decision. They fail on purpose as long as a bug exists;
#      a test that PASSES here means the bug looks fixed in this version (remove its marker).
# Exit code: 0 when the blocking tests pass, 1 otherwise. A summary goes to <work-dir>/summary.md and,
# when running in GitHub Actions, to the job summary.
set -u
HERE="$(cd "$(dirname "$0")/../.." && pwd)"
PYTHON="${PYTHON:-python}"
UPSTREAM="${UPSTREAM:-https://github.com/marq24/ha-goecharger-api2}"
REF="${1:-}"
WORK="${2:-$(mktemp -d)}"

if [ -z "$REF" ]; then
  REF="$(gh api repos/marq24/ha-goecharger-api2/releases/latest --jq .tag_name)" || { echo "cannot determine the latest release"; exit 2; }
fi
mkdir -p "$WORK"
rm -rf "$WORK/src"
git -c advice.detachedHead=false clone --quiet --depth 1 --branch "$REF" "$UPSTREAM" "$WORK/src" || { echo "cannot clone $REF"; exit 2; }
SHA="$(git -C "$WORK/src" rev-parse --short HEAD)"
mkdir -p "$WORK/src/tests"
cp -R "$HERE/tests/integration" "$WORK/src/tests/"
find "$WORK/src/tests" -name __pycache__ -prune -exec rm -rf {} +

cd "$WORK/src" || exit 2
"$PYTHON" -m pytest tests/integration -p no:cacheprovider -q -m "not known_bug and not needs_decision" \
  --junitxml="$WORK/blocking.xml" > "$WORK/blocking.txt" 2>&1
BLOCKING=$?
"$PYTHON" -m pytest tests/integration -p no:cacheprovider -q -m "known_bug or needs_decision" \
  --junitxml="$WORK/known.xml" > "$WORK/known.txt" 2>&1

"$PYTHON" - "$WORK" "$REF" "$SHA" <<'PY'
import sys
import xml.etree.ElementTree as ET

work, ref, sha = sys.argv[1:4]


def read(name):
    root = ET.parse(f"{work}/{name}.xml").getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    cases = []
    for tc in suite.iter("testcase"):
        failed = tc.find("failure") is not None or tc.find("error") is not None
        cases.append((tc.get("classname").split(".")[-1] + "::" + tc.get("name"), failed))
    return cases


blocking, known = read("blocking"), read("known")
raw = open(f"{work}/blocking.txt").read()
if "ERROR collecting" in raw or "ImportError" in raw:
    text = "\n".join([f"## Regression tests for upstream `{ref}` (`{sha}`)", "",
        "**The tests could not be collected.** This version probably lacks functions the tests import "
        "(the tests follow upstream `main`; for example `add_config_entry_to_service` exists since 2026.10.8).",
        "", "```", "\n".join(raw.strip().splitlines()[-12:]), "```", ""])
    open(f"{work}/summary.md", "w").write(text + "\n")
    print(text)
    sys.exit(0)
failing = [n for n, f in blocking if f]
fixed = [n for n, f in known if not f]
still = [n for n, f in known if f]
lines = [f"## Regression tests for upstream `{ref}` (`{sha}`)", "",
         f"| | |", "|---|---|",
         f"| Blocking tests | **{len(blocking) - len(failing)} of {len(blocking)} passed** |",
         f"| Known bugs / open decisions still failing | {len(still)} |",
         f"| Known-bug tests that now PASS (bug looks fixed) | **{len(fixed)}** |", ""]
if failing:
    lines += ["### Blocking tests that fail (new regression or version-specific behaviour)", ""] + [f"- `{n}`" for n in failing] + [""]
if fixed:
    lines += ["### Known-bug tests that pass in this version (remove the marker)", ""] + [f"- `{n}`" for n in fixed] + [""]
text = "\n".join(lines)
open(f"{work}/summary.md", "w").write(text + "\n")
print(text)
PY
[ -n "${GITHUB_STEP_SUMMARY:-}" ] && cat "$WORK/summary.md" >> "$GITHUB_STEP_SUMMARY"
[ "$BLOCKING" -eq 0 ] && exit 0 || exit 1
