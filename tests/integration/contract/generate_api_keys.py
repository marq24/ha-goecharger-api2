"""Builds api_keys.json from the official key table (go-eCharger-API-v2, API_KEYS_FIRMWARE/apikeys-en.md).

Only key names and flags are stored (R/W, type, category), not the descriptions.
Usage: python generate_api_keys.py <path to apikeys-en.md> <commit sha of the official repository> <date> [controller]
With the last argument the key table of the go-eController API (goecharger/go-eController-API) is read
and controller_keys.json is written instead.
"""
import json
import re
import sys
from pathlib import Path


def parse(path):
    keys = {}
    for line in Path(path).read_text().splitlines():
        if line.startswith("|--") or line.startswith("| Key") or "|" not in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 5:
            continue
        names = re.sub(r"\(.*?\)", "", cells[0]).split()
        for name in (n for n in names if re.fullmatch(r"[A-Za-z0-9_]+", n)):
            keys[name] = {"rw": cells[1], "type": re.sub(r"&lt;.*", "<...>", cells[2]), "category": cells[3]}
    return dict(sorted(keys.items()))


if __name__ == "__main__":
    source, commit, date = sys.argv[1:4]
    controller = len(sys.argv) > 4 and sys.argv[4] == "controller"
    origin = ("goecharger/go-eController-API", "apikeys-en.md") if controller else \
             ("goecharger/go-eCharger-API-v2", "API_KEYS_FIRMWARE/apikeys-en.md")
    out = {"source": {"repository": origin[0], "file": origin[1], "commit": commit, "date": date},
           "keys": parse(source)}
    target = Path(__file__).with_name("controller_keys.json" if controller else "api_keys.json")
    target.write_text(json.dumps(out, indent=1) + "\n")
    print(f"{len(out['keys'])} keys written to {target}")
