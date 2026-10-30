"""Builds testcases.md: every test function on one line, with the number of cases and the result.

Usage: python build_testcases.py <junit xml> <tests dir> <output file>

The text of a line is the first line of the docstring of the test function; without a docstring it is the
function name written as a sentence. Parametrized tests are one line with the number of cases. A case that
fails on purpose (marker known_bug or needs_decision) is counted as "red on purpose".
"""
import ast
import sys
import xml.etree.ElementTree as ET
from collections import OrderedDict
from pathlib import Path

junit, tests_dir, output = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])


def sentence(name):
    text = name.removeprefix("test_").replace("_", " ")
    return text[:1].upper() + text[1:]


results = OrderedDict()  # (module, function) -> [total, red, skipped]
for case in ET.parse(junit).getroot().iter("testcase"):
    function = case.get("name").split("[")[0]
    entry = results.setdefault((case.get("classname").split(".")[-1], function), [0, 0, 0])
    entry[0] += 1
    if case.find("failure") is not None or case.find("error") is not None:
        entry[1] += 1
    elif case.find("skipped") is not None:
        entry[2] += 1

lines = ["# Test cases", "",
         "One line per test function. The text is the first line of its docstring in the code, or the function name written as a sentence. "
         "\"Red\" means the result is intentionally red (known defect or open decision) and does not block a release.", ""]
total = red = skipped = 0
for path in sorted(tests_dir.glob("test_*.py")):
    tree = ast.parse(path.read_text())
    module_doc = (ast.get_docstring(tree) or path.stem).splitlines()[0]
    rows = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
            n, r, s = results.get((path.stem, node.name), [0, 0, 0])
            if n == 0:
                continue
            doc = (ast.get_docstring(node) or "").splitlines()
            text = (doc[0] if doc else sentence(node.name)).replace("|", "\\|")
            status = "red" if r == n else (f"{r} red" if r else ("skipped" if s == n else "green"))
            rows.append(f"| {text} | {n} | {status} |")
            total, red, skipped = total + n, red + r, skipped + s
    if rows:
        lines += [f"## `{path.name}`", "", module_doc, "", "| Checks | Cases | Result |", "|---|---|---|", *rows, ""]
lines.insert(3, f"**{total} cases**, of which {red} intentionally red and {skipped} skipped.\n")
output.write_text("\n".join(lines) + "\n")
print(f"{total} cases in {output}")
