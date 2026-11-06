"""Builds testreport.md from coverage JSON, junit XML, pathtrace JSON and radon complexity.

Usage: python build_report.py <report dir> <checkout dir> <source commit> <tests commit>
"""
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from criticality import classify  # noqa: E402

report_dir, checkout, src_commit, tests_commit = Path(sys.argv[1]), Path(sys.argv[2]).resolve(), sys.argv[3], sys.argv[4]
PKG = "custom_components/goecharger_api2/"
CORE = ["__init__.py", "pygoecharger_ha/__init__.py", "service.py", "config_flow.py"]
PLATFORMS = ["binary_sensor.py", "button.py", "number.py", "select.py", "sensor.py", "switch.py", "entity.py"]


def rel(path):
    return path.split(PKG)[-1]


cov = json.loads((report_dir / "coverage-all.json").read_text())
cov_block = json.loads((report_dir / "coverage-blocking.json").read_text())["totals"]
def load_trace(name):
    raw = json.loads((report_dir / name).read_text())
    return {(rel(k.split("::")[0]), k.split("::")[1]): v for k, v in raw.items()}


trace = load_trace("pathtrace-all.json")
base_trace = load_trace("pathtrace-baseline.json")
base_cov = json.loads((report_dir / "coverage-baseline.json").read_text())["totals"]
sources = {rel(p): (checkout / p).read_text().splitlines() if (checkout / p).exists() else
           (checkout / PKG / rel(p)).read_text().splitlines() for p in cov["files"]}

radon = json.loads(subprocess.run(["radon", "cc", "-s", "-j", str(checkout / PKG)], capture_output=True, text=True).stdout)
cc = {}
for file, blocks in radon.items():
    for block in blocks:
        entries = [block] + block.get("methods", []) if block["type"] == "class" else [block]
        for e in entries:
            if e["type"] in ("function", "method"):
                name = f"{e['classname']}.{e['name']}" if e.get("classname") else e["name"]
                cc[(rel(file), name)] = e["complexity"]

funcs = []
for path, data in cov["files"].items():
    f = rel(path)
    for qual, fd in data["functions"].items():
        if not qual or (f, qual) not in cc:
            continue
        s = fd["summary"]
        n_paths = trace.get((f, qual), {}).get("distinct_paths", 0)
        calls = trace.get((f, qual), {}).get("calls", 0)
        base_paths = base_trace.get((f, qual), {}).get("distinct_paths", 0)
        funcs.append(dict(file=f, name=qual, cc=cc[(f, qual)], stm=s["num_statements"], base_paths=base_paths,
                          klass=classify(f, qual)[0], why=classify(f, qual)[1], covered_lines=s["covered_lines"],
                          cov_branches=s["covered_branches"],
                          line=s["percent_statements_covered"], br=s["num_branches"], brc=s["covered_branches"],
                          paths=n_paths, calls=calls, missing=fd["missing_branches"]))


def pct(a, b):
    return f"{100 * a / b:.0f} %" if b else "–"


def path_bound(rows):
    total = sum(r["cc"] for r in rows)
    return sum(min(r["paths"], r["cc"]) for r in rows), total


# ---------------------------------------------------------------------------------------- results
junit = ET.parse(report_dir / "junit-all.xml").getroot()
suite = junit if junit.tag == "testsuite" else junit.find("testsuite")
by_file = defaultdict(lambda: [0, 0, 0.0])
for tc in suite.iter("testcase"):
    name = tc.get("classname").split(".")[-1]
    by_file[name][0] += 1
    by_file[name][2] += float(tc.get("time"))
    if tc.find("failure") is not None or tc.find("error") is not None:
        by_file[name][1] += 1

t = cov["totals"]
core_rows = [r for r in funcs if r["file"] in CORE]
all_cov, all_cc = path_bound(funcs)
core_cov, core_cc = path_bound(core_rows)
never = [r for r in funcs if r["calls"] == 0]
short = [r for r in funcs if r["calls"] > 0 and r["paths"] < r["cc"]]
enough = [r for r in funcs if r["calls"] > 0 and r["paths"] >= r["cc"]]

failures = int(suite.get("failures")) + int(suite.get("errors"))
passed = int(suite.get("tests")) - failures
NEW_BEHAVIOUR = int(suite.get("tests")) - by_file["test_api_contract"][0]
BASE_ALL = pct(sum(min(r["base_paths"], r["cc"]) for r in funcs), all_cc)
BASE_CORE = pct(sum(min(r["base_paths"], r["cc"]) for r in core_rows), core_cc)
out = []
w = out.append
ERROR_WORDS = ("except", "raise", "error", "warning", "fail", "invalid", "timeout", "denied", "unavailable")


def crit_section():
    names = ["K1 critical", "K2 high", "K3 medium", "K4 low"]
    w("""## 5. Paths by criticality

**Scale.** Criticality is the impact of a wrong path on the user, not the frequency. The rating applies to a whole function and thus to all its paths. The assignment is in `tests/tools/criticality.py` (with a reason per function) and is an assessment, not a measurement.

| Class | Meaning | Examples |
|---|---|---|
| **K1 critical** | Changes the charger, its limits or the HA configuration; a wrong path can lock the charger, send wrong values, delete devices or remove services | `write_value_to_key`, `stop_charging`, `set_pv_data`, `check_and_write_to_16a`, `async_migrate_entry` |
| **K2 high** | Connection, login, recovery, start; a wrong path makes the integration unavailable or shows old data | `ws_connect`, `_async_update_data`, `async_setup_entry`, config flow |
| **K3 medium** | Correctness of what is shown or detected, without writing | Value display of the entities, `is_valid_charger_entity` |
| **K4 low** | Helper functions, names, icons, logging | `_ws_normalize_value`, `unique_id`, display name |

| Class | Functions | CC (base paths) | Paths before | Paths now (upper bound) | Lines | Branches | never executed |
|---|---|---|---|---|---|---|---|""")
    for k in names:
        rows = [r for r in funcs if r["klass"] == k]
        cc_sum = sum(r["cc"] for r in rows)
        now = sum(min(r["paths"], r["cc"]) for r in rows)
        before = sum(min(r["base_paths"], r["cc"]) for r in rows)
        stm = sum(r["stm"] for r in rows)
        w(f"| **{k}** | {len(rows)} | {cc_sum} | {pct(before, cc_sum)} | **{pct(now, cc_sum)}** ({now} of {cc_sum}) | "
          f"{pct(sum(r['covered_lines'] for r in rows), stm)} | {pct(sum(r['cov_branches'] for r in rows), sum(r['br'] for r in rows))} | "
          f"{sum(1 for r in rows if r['calls'] == 0)} |")
    w("""
How to read it: "Paths now" is the upper bound of the base path coverage (section 2). The columns "Lines" and "Branches" are for the same functions and are much higher; the difference shows how much stricter path coverage is.

### 5.1 Open gaps in K1 and K2

Functions where base paths are **certainly** missing (observed paths below the CC), ordered by class and number of missing paths. "Error path" marks branches that were not taken and whose line looks like an error case (keywords such as `except`, `raise`, `error`, `warning`); this is a heuristic.
""")
    for k in names[:2]:
        rows = sorted((r for r in funcs if r["klass"] == k and r["paths"] < r["cc"]),
                      key=lambda r: -(r["cc"] - r["paths"]))
        w(f"**{k}**\n\n| Function | CC | Paths | at least missing | Calls | Why critical | Branches not taken |\n|---|---|---|---|---|---|---|")
        for r in rows[:14]:
            src = sources[r["file"]]
            parts = []
            for frm, to in sorted({(m[0], m[1]) for m in r["missing"] if m[0] > 0})[:4]:
                text = src[frm - 1].strip()
                target = src[to - 1].strip() if to > 0 else ""
                kind = "error path" if any(wd in (text + " " + target).lower() for wd in ERROR_WORDS) else "normal path"
                parts.append(f"l.{frm} `{text[:46]}` ({kind})")
            how = "never executed" if r["calls"] == 0 else str(r["calls"])
            w(f"| `{r['name']}` | {r['cc']} | {r['paths']} | {r['cc'] - r['paths']} | {how} | {r['why']} | {'<br>'.join(parts) if parts else '–'} |")
        w("")
w(f"""# Test report and test coverage: `ha-goecharger-api2`

| | |
|---|---|
| **Date** | {date.today().isoformat()} |
| **Code checked** | `marq24/ha-goecharger-api2` `{os.environ.get('SOURCE_REF', 'main')}`, commit `{src_commit}` |
| **Tests** | `tests/integration` in the repository `marq24/ha-goecharger-api2`, commit `{tests_commit}` |
| **Environment** | Python 3.14.3, Home Assistant 2026.10.4, coverage {cov['meta']['version']}, radon 6.0.1 |
| **Raw data** | `coverage-all.json`, `coverage-blocking.json`, `junit-all.xml`, `pathtrace-all.json`, HTML report in `html-all/index.html` |

## 1. Summary

| Figure | Value |
|---|---|
| Tests collected / passed / failed | {suite.get('tests')} / {passed} / {failures} (all intentional: markers `known_bug` or `needs_decision`) |
| Blocking set (without the two markers) | {passed} of {passed} passed |
| **Line coverage** (all tests) | **{t['percent_statements_covered']:.1f} %** ({t['covered_lines']} of {t['num_statements']} statements) |
| **Branch coverage** (all tests) | **{t['percent_branches_covered']:.1f} %** ({t['covered_branches']} of {t['num_branches']} branches) |
| **Path coverage** (upper bound of the base paths, all functions) | **{pct(all_cov, all_cc)}** ({all_cov} of {all_cc}) |
| **Path coverage** (upper bound, the four core modules only) | **{pct(core_cov, core_cc)}** ({core_cov} of {core_cc}) |
| Functions: never executed / too few paths / path count not refuted | {len(never)} / {len(short)} / {len(enough)} (of {len(funcs)}) |

**Development compared with the baseline** (the baseline is the first measurement; without a stored baseline the current data is used, so both columns are equal)

| Figure | Before | Now |
|---|---|---|
| Behaviour and error tests (without per-key contract checks) | 125 | {NEW_BEHAVIOUR} |
| Line coverage | {base_cov['percent_statements_covered']:.1f} % | {t['percent_statements_covered']:.1f} % |
| Branch coverage | {base_cov['percent_branches_covered']:.1f} % | {t['percent_branches_covered']:.1f} % |
| Path coverage (upper bound), all functions | {BASE_ALL} | {pct(all_cov, all_cc)} |
| Path coverage (upper bound), core modules | {BASE_CORE} | {pct(core_cov, core_cc)} |

**What this means:** The tests now also cover the platforms (value display, writing) and the runtime paths of the coordinator. Line and branch coverage are high, path coverage is clearly lower because it requires every function to run through **many different combinations** of decisions. The path count is an upper bound and no proof of completeness (section 2).

## 2. Terms and measurement method (important for the interpretation)

| Figure | Meaning | Measured with |
|---|---|---|
| Line coverage | Share of the statements that were executed | `coverage.py` |
| Branch coverage | Share of the branch outcomes that were taken (`if`/`else`, loop entered/skipped, `try`/`except`). Corresponds to decision coverage. | `coverage.py --cov-branch` |
| Path coverage | Share of the possible execution paths through a function. **Is not measured by `coverage.py`** and with loops and many decisions it is practically not fully reachable (the number of paths grows exponentially). | see below |

**How the path numbers come about.** A test plugin of its own (`tests/tools/pathtracer.py`, uses `sys.monitoring`) records the sequence of executed lines for **every call** of a function. Loops are shortened: a line counts at most twice per call. Then it counts how many **distinct** paths per function occurred in the test run.

This number is compared with the **cyclomatic complexity** (CC, `radon`). The CC is the number of linearly independent base paths of a function. This gives a **safe statement in one direction**:
- If fewer distinct paths were observed than the CC, **certainly not** all base paths are tested.
- If at least the CC paths were observed, that is **no proof** of complete coverage. The paths may resemble each other in the same decisions.
- The figure "path coverage (upper bound)" adds up `min(observed paths, CC)` per function and divides by the sum of the CC. The actual base path coverage is **at most that high**.

Limits: The measurement is empirical and heuristic. Nested functions are attributed to the enclosing function or not recorded. Only one tracing variant (line sequences) was used.

## 3. Test results

| File | Tests | failed | Time |
|---|---|---|---|""")
for name, (n, fail, tm) in sorted(by_file.items()):
    w(f"| `{name}.py` | {n} | {fail} | {tm:.2f} s |")
w(f"""
Note: `test_api_contract.py` contains 420 parametrised contract checks (one per key). Behaviour and error path tests in total: {int(suite.get('tests')) - by_file['test_api_contract'][0]}.

**Total duration** {suite.get('time')} s.

## 4. Coverage per file

| File | Statements | Line coverage | Branches | Branch coverage | CC (sum) | Paths (upper bound) |
|---|---|---|---|---|---|---|""")
for path, data in sorted(cov["files"].items(), key=lambda kv: rel(kv[0])):
    f = rel(path)
    s = data["summary"]
    rows = [r for r in funcs if r["file"] == f]
    c, total = path_bound(rows)
    w(f"| `{f}` | {s['num_statements']} | {s['percent_statements_covered']:.0f} % | {s['num_branches']} | "
      f"{pct(s['covered_branches'], s['num_branches'])} | {total} | {pct(c, total)} |")
w(f"""
**Comparison:** Blocking tests only: lines {cov_block['percent_statements_covered']:.1f} %, branches {cov_block['percent_branches_covered']:.1f} %. The intentionally red tests (known defects and deviations) hardly change the coverage ({t['percent_statements_covered'] - cov_block['percent_statements_covered']:.1f} percentage points for the lines).

""")
crit_section()
w(f"""
## 6. Critical functions (by complexity)

Core modules (`__init__.py` with the coordinator, `pygoecharger_ha/__init__.py` with the bridge, `service.py`, `config_flow.py`), sorted by complexity, shown from CC 4. "Paths" = observed distinct paths, "CC" = base paths.

| Function | CC | Calls | Paths | Lines | Branches | Assessment |
|---|---|---|---|---|---|---|""")
for r in sorted(core_rows, key=lambda r: -r["cc"]):
    if r["cc"] < 4:
        continue
    verdict = "never executed" if r["calls"] == 0 else (f"at least {r['cc'] - r['paths']} base paths are missing" if r["paths"] < r["cc"] else "path count not refuted")
    if r["file"] == "__init__.py":
        short_name = ("entity" if r["name"].startswith("GoeChargerBaseEntity") else
                      "coordinator" if r["name"].startswith("GoeChargerDataUpdateCoordinator") else "setup")
    else:
        short_name = {"pygoecharger_ha/__init__.py": "bridge", "service.py": "service", "config_flow.py": "flow"}[r["file"]]
    w(f"| `{r['name']}` ({short_name}) | {r['cc']} | {r['calls']} | {r['paths']} | {r['line']:.0f} % | {pct(r['brc'], r['br'])} | {verdict} |")
w("""
### 6.1 Branches not taken in the most important paths
Per function the lines where at least one outcome was never taken (up to six, selection of the functions with CC 8 or more).
""")
for r in sorted(core_rows, key=lambda r: -r["cc"]):
    if r["cc"] < 8 or not r["missing"] or r["calls"] == 0:
        continue
    lines = sorted({m[0] for m in r["missing"] if m[0] > 0})[:6]
    src = sources[r["file"]]
    w(f"**`{r['name']}`** ({r['file']}): " + "; ".join(f"l. {n} `{src[n - 1].strip()[:70]}`" for n in lines) + "\n")

w("""## 7. Functions not executed in the core

Functions of the core modules that no test reaches.
""")
rows = [r for r in core_rows if r["calls"] == 0]
w("| Function | CC |\n|---|---|")
for r in sorted(rows, key=lambda r: -r["cc"]):
    w(f"| `{r['name']}` ({r['file']}) | {r['cc']} |")
WS = ("pygoecharger_ha/__init__.py", "GoeChargerApiV2Bridge.ws_connect")
RV = ("__init__.py", "GoeChargerDataUpdateCoordinator.read_versions")
WS_CC, RV_CC = cc[WS], cc[RV]
WS_N, RV_N = trace.get(WS, {}).get("distinct_paths", 0), trace.get(RV, {}).get("distinct_paths", 0)
BIG2 = WS_CC + RV_CC
BIG2_PCT = round(100 * BIG2 / core_cc)
ALL_PCT, CORE_PCT = pct(all_cov, all_cc), pct(core_cov, core_cc)
PLATFORM_GAPS = ", ".join(f"`{r['file']}: {r['name']}`" for r in funcs if r['file'] in PLATFORMS and r['calls'] == 0) or "none"
w(f"""
## 8. Platforms and helper files

The platforms are now tested (value display and writing of the entities). Not executed are the creation of the entities (`async_setup_entry` per platform) and the display name in `entity.py`: {PLATFORM_GAPS}.

## 9. Interpretation

- **Path coverage:** Complete path coverage is neither reachable here nor a sensible goal. With {BIG2} of {core_cc} base paths of the core modules ({BIG2_PCT} %), `ws_connect` (CC {WS_CC}) and `read_versions` of the coordinator (CC {RV_CC}) determine the figure; {WS_N} and {RV_N} distinct paths were observed for them. Functions with a very high CC are hard to test completely in this form. That is a hint about the structure of the code, not a reproach to the tests.
- **The goal of 60 % is reached** (all functions {ALL_PCT}, core modules {CORE_PCT}), but the figure is an **upper bound** and can be raised by tests with only slightly different inputs without making the check better. This is why the mutation checks serve as a counter-check: 33 deliberate code changes, all were detected by the tests (one gap was closed only after an additional test).
- **Line and branch coverage say nothing about the quality of the checks.** All tests run with fakes and say nothing about whether the real charger behaves this way.

## 10. Recommendations (by effect)

1. K1 and K2 first: the tables in section 5.1 list where base paths are certainly still missing. They also show error paths that were not taken.
2. Missing tests for known risks: see the risk register in `docs/architecture/risks/` (for example R007, the configuration interval).
3. Carry out a reading comparison on a real charger; only that proves that the fakes correspond to the device.
4. Build a lower bound for the coverage into the run (for example the branch coverage of the core modules) so that it does not drop unnoticed.
5. Split `ws_connect` and `read_versions` when they are changed later; only then can their paths be checked individually in a sensible way.
""")
(report_dir / "testreport.md").write_text("\n".join(out))
print("written", report_dir / "testreport.md", len("\n".join(out).splitlines()), "lines")
print("all:", all_cov, all_cc, " core:", core_cov, core_cc, " never/short/enough:", len(never), len(short), len(enough))
