"""Quick metric: path coverage (upper bound of basis paths) from a pathtrace JSON, per criticality.

Usage: python pathmetric.py <pathtrace.json> <checkout>
"""
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from criticality import classify  # noqa: E402

PKG = "custom_components/goecharger_api2/"
CORE = ["__init__.py", "pygoecharger_ha/__init__.py", "service.py", "config_flow.py"]
trace_file, checkout = sys.argv[1], Path(sys.argv[2]).resolve()


def rel(p):
    return p.split(PKG)[-1]


trace = {(rel(k.split("::")[0]), k.split("::")[1]): v for k, v in json.load(open(trace_file)).items()}
radon = json.loads(subprocess.run(["radon", "cc", "-s", "-j", str(checkout / PKG)], capture_output=True, text=True).stdout)
cc = {}
for file, blocks in radon.items():
    for b in blocks:
        for e in ([b] + b.get("methods", []) if b["type"] == "class" else [b]):
            if e["type"] in ("function", "method"):
                cc[(rel(file), f"{e['classname']}.{e['name']}" if e.get("classname") else e["name"])] = e["complexity"]
tot = defaultdict(lambda: [0, 0])
for (f, q), c in cc.items():
    n = trace.get((f, q), {}).get("distinct_paths", 0)
    k = classify(f, q)[0]
    for key in ("ALL", "CORE" if f in CORE else "PLAT", k):
        tot[key][0] += min(n, c)
        tot[key][1] += c
for key in ("ALL", "CORE", "PLAT", "K1 kritisch", "K2 hoch", "K3 mittel", "K4 niedrig"):
    a, b = tot[key]
    print(f"{key:12s} {a:4d}/{b:4d} = {100 * a / b:5.1f} %")
