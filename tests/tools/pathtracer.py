"""pytest plugin: records which distinct execution paths each function of the integration takes.

A path is the sequence of executed source lines of ONE call of a function (a coroutine's call spans
all its resumptions). Loops are shortened: a line counts at most twice per call. The result is an
empirical number of distinct paths seen during the test run; it is NOT a proof of path coverage.
Use: PYTHONPATH=tools PATHTRACE_OUT=out.json python -m pytest -p pathtracer ...
Needs Python 3.12+ (sys.monitoring).
"""
import json
import os
import sys
from collections import defaultdict

mon = sys.monitoring
TOOL = 3
PKG = "/custom_components/goecharger_api2/"
E = mon.events
active = {}                      # frame -> [code, lines, counts]
paths = defaultdict(set)         # (file, qualname) -> {tuple of lines}
calls = defaultdict(int)


def _relevant(code):
    return PKG in code.co_filename


def _start(code, offset):
    if not _relevant(code):
        return mon.DISABLE
    active[sys._getframe(1)] = [code, [], {}]
    calls[(code.co_filename, code.co_qualname)] += 1


def _line(code, line):
    if not _relevant(code):
        return mon.DISABLE
    entry = active.get(sys._getframe(1))
    if entry is None:
        return
    seen = entry[2].get(line, 0)
    entry[2][line] = seen + 1
    if seen < 2:
        entry[1].append(line)


def _finish(marker):
    def callback(code, offset, *args):
        if not _relevant(code):
            return None  # PY_UNWIND events cannot be disabled
        entry = active.pop(sys._getframe(1), None)
        if entry is not None:
            paths[(code.co_filename, code.co_qualname)].add(tuple(entry[1]) + (marker,))
    return callback


def pytest_configure(config):
    mon.use_tool_id(TOOL, "pathtracer")
    mon.register_callback(TOOL, E.PY_START, _start)
    mon.register_callback(TOOL, E.LINE, _line)
    mon.register_callback(TOOL, E.PY_RETURN, _finish("R"))
    mon.register_callback(TOOL, E.PY_UNWIND, _finish("X"))
    mon.set_events(TOOL, E.PY_START | E.LINE | E.PY_RETURN | E.PY_UNWIND)


def pytest_sessionfinish(session, exitstatus):
    mon.set_events(TOOL, 0)
    out = os.environ.get("PATHTRACE_OUT", "pathtrace.json")
    data = {f"{file}::{qual}": {"calls": calls[(file, qual)], "distinct_paths": len(p)}
            for (file, qual), p in paths.items()}
    for (file, qual), n in calls.items():
        data.setdefault(f"{file}::{qual}", {"calls": n, "distinct_paths": 0})
    json.dump(data, open(out, "w"), indent=1)
