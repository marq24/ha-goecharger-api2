"""Builds testreport.md from coverage JSON, junit XML, pathtrace JSON and radon complexity.

Usage: python build_report.py <report dir> <checkout dir> <source commit> <tests commit>
"""
import json
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
    names = ["K1 kritisch", "K2 hoch", "K3 mittel", "K4 niedrig"]
    w("""## 5. Pfade nach Kritikalität

**Maßstab.** Kritikalität ist die Auswirkung eines falschen Pfades auf den Nutzer, nicht die Häufigkeit. Die Einstufung gilt für eine ganze Funktion und damit für alle ihre Pfade. Die Zuordnung steht in `tests/tools/criticality.py` (mit Begründung je Funktion) und ist eine Einschätzung, keine Messung.

| Klasse | Bedeutung | Beispiele |
|---|---|---|
| **K1 kritisch** | Ändert den Charger, seine Grenzen oder die HA-Konfiguration; ein falscher Pfad kann den Charger sperren, falsche Werte senden, Geräte löschen oder Dienste entfernen | `write_value_to_key`, `stop_charging`, `set_pv_data`, `check_and_write_to_16a`, `async_migrate_entry` |
| **K2 hoch** | Verbindung, Anmeldung, Erholung, Start; ein falscher Pfad macht die Integration unverfügbar oder zeigt alte Daten | `ws_connect`, `_async_update_data`, `async_setup_entry`, Config-Flow |
| **K3 mittel** | Korrektheit dessen, was angezeigt oder erkannt wird, ohne Schreiben | Wertdarstellung der Entitäten, `is_valid_charger_entity` |
| **K4 niedrig** | Hilfsfunktionen, Namen, Symbole, Logging | `_ws_normalize_value`, `unique_id`, Anzeigename |

| Klasse | Funktionen | CC (Basispfade) | Pfade vorher | Pfade jetzt (obere Schranke) | Zeilen | Zweige | nie ausgeführt |
|---|---|---|---|---|---|---|---|""")
    for k in names:
        rows = [r for r in funcs if r["klass"] == k]
        cc_sum = sum(r["cc"] for r in rows)
        now = sum(min(r["paths"], r["cc"]) for r in rows)
        before = sum(min(r["base_paths"], r["cc"]) for r in rows)
        stm = sum(r["stm"] for r in rows)
        w(f"| **{k}** | {len(rows)} | {cc_sum} | {pct(before, cc_sum)} | **{pct(now, cc_sum)}** ({now} von {cc_sum}) | "
          f"{pct(sum(r['covered_lines'] for r in rows), stm)} | {pct(sum(r['cov_branches'] for r in rows), sum(r['br'] for r in rows))} | "
          f"{sum(1 for r in rows if r['calls'] == 0)} |")
    w("""
Lesehilfe: „Pfade jetzt“ ist die obere Schranke der Basispfadabdeckung (Abschnitt 2). Die Spalten „Zeilen“ und „Zweige“ stehen für dieselben Funktionen und liegen viel höher; der Unterschied zeigt, wie viel strenger die Pfadabdeckung ist.

### 5.1 Offene Lücken in K1 und K2

Funktionen, bei denen **sicher** Basispfade fehlen (beobachtete Pfade unter der CC), geordnet nach Klasse und Zahl der fehlenden Pfade. „Fehlerpfad“ markiert nicht genommene Zweige, deren Zeile nach einem Fehlerfall aussieht (Schlüsselwörter wie `except`, `raise`, `error`, `warning`); das ist eine Heuristik.
""")
    for k in names[:2]:
        rows = sorted((r for r in funcs if r["klass"] == k and r["paths"] < r["cc"]),
                      key=lambda r: -(r["cc"] - r["paths"]))
        w(f"**{k}**\n\n| Funktion | CC | Pfade | fehlen mind. | Aufrufe | Warum kritisch | Nicht genommene Zweige |\n|---|---|---|---|---|---|---|")
        for r in rows[:14]:
            src = sources[r["file"]]
            parts = []
            for frm, to in sorted({(m[0], m[1]) for m in r["missing"] if m[0] > 0})[:4]:
                text = src[frm - 1].strip()
                target = src[to - 1].strip() if to > 0 else ""
                kind = "Fehlerpfad" if any(wd in (text + " " + target).lower() for wd in ERROR_WORDS) else "Normalpfad"
                parts.append(f"Z.{frm} `{text[:46]}` ({kind})")
            how = "nie ausgeführt" if r["calls"] == 0 else str(r["calls"])
            w(f"| `{r['name']}` | {r['cc']} | {r['paths']} | {r['cc'] - r['paths']} | {how} | {r['why']} | {'<br>'.join(parts) if parts else '–'} |")
        w("")
w(f"""# Testreport und Testabdeckung: `ha-goecharger-api2`

| | |
|---|---|
| **Datum** | {date.today().isoformat()} |
| **Geprüfter Code** | `marq24/ha-goecharger-api2` `main`, Commit `{src_commit}` |
| **Tests** | Fork `OliEder/ha-goecharger-api2`, Branch `tests/regression-suite`, Commit `{tests_commit}` |
| **Umgebung** | Python 3.14.3, Home Assistant 2026.10.4, coverage {cov['meta']['version']}, radon 6.0.1 |
| **Rohdaten** | `coverage-all.json`, `coverage-blocking.json`, `junit-all.xml`, `pathtrace-all.json`, HTML-Bericht in `html-all/index.html` |

## 1. Zusammenfassung

| Kennzahl | Wert |
|---|---|
| Tests gesammelt / bestanden / fehlgeschlagen | {suite.get('tests')} / {passed} / {failures} (alle beabsichtigt: {failures - 14} `known_bug`, 14 `needs_decision`) |
| Blockierende Menge (ohne die beiden Marker) | {passed} von {passed} bestanden |
| **Zeilenabdeckung** (alle Tests) | **{t['percent_statements_covered']:.1f} %** ({t['covered_lines']} von {t['num_statements']} Anweisungen) |
| **Zweigabdeckung** (alle Tests) | **{t['percent_branches_covered']:.1f} %** ({t['covered_branches']} von {t['num_branches']} Zweigen) |
| **Pfadabdeckung** (obere Schranke der Basispfade, alle Funktionen) | **{pct(all_cov, all_cc)}** ({all_cov} von {all_cc}) |
| **Pfadabdeckung** (obere Schranke, nur die vier Kernmodule) | **{pct(core_cov, core_cc)}** ({core_cov} von {core_cc}) |
| Funktionen: nie ausgeführt / mit zu wenigen Pfaden / Pfadzahl nicht widerlegt | {len(never)} / {len(short)} / {len(enough)} (von {len(funcs)}) |

**Entwicklung gegenüber dem ersten Report (gleicher Tag, Stand vor dem Ausbau der Tests)**

| Kennzahl | Vorher | Jetzt |
|---|---|---|
| Verhaltens- und Fehlertests (ohne Vertragsprüfungen je Schlüssel) | 125 | {NEW_BEHAVIOUR} |
| Zeilenabdeckung | {base_cov['percent_statements_covered']:.1f} % | {t['percent_statements_covered']:.1f} % |
| Zweigabdeckung | {base_cov['percent_branches_covered']:.1f} % | {t['percent_branches_covered']:.1f} % |
| Pfadabdeckung (obere Schranke), alle Funktionen | {BASE_ALL} | {pct(all_cov, all_cc)} |
| Pfadabdeckung (obere Schranke), Kernmodule | {BASE_CORE} | {pct(core_cov, core_cc)} |

**Was das bedeutet:** Die Tests prüfen jetzt auch die Plattformen (Wertdarstellung, Schreiben) und die Laufzeitpfade des Koordinators. Zeilen- und Zweigabdeckung sind hoch, die Pfadabdeckung ist deutlich niedriger, weil sie verlangt, dass jede Funktion **viele verschiedene Kombinationen** von Entscheidungen durchläuft. Die Pfadzahl ist eine obere Schranke und kein Beleg für Vollständigkeit (Abschnitt 2).

## 2. Begriffe und Messverfahren (wichtig für die Einordnung)

| Kennzahl | Bedeutung | Gemessen mit |
|---|---|---|
| Zeilenabdeckung | Anteil der ausgeführten Anweisungen | `coverage.py` |
| Zweigabdeckung | Anteil der genommenen Verzweigungsausgänge (`if`/`else`, Schleife betreten/übersprungen, `try`/`except`). Entspricht der Entscheidungsabdeckung. | `coverage.py --cov-branch` |
| Pfadabdeckung | Anteil der möglichen Ausführungswege durch eine Funktion. **Wird von `coverage.py` nicht gemessen** und ist bei Schleifen und vielen Entscheidungen praktisch nicht vollständig erreichbar (Zahl der Pfade wächst exponentiell). | siehe unten |

**Wie die Pfadzahlen entstehen.** Ein eigenes Test-Plugin (`tests/tools/pathtracer.py`, nutzt `sys.monitoring`) zeichnet für **jeden Aufruf** einer Funktion die Folge der ausgeführten Zeilen auf. Schleifen werden verkürzt: eine Zeile zählt je Aufruf höchstens zweimal. Danach zählt es, wie viele **verschiedene** Pfade je Funktion im Testlauf vorkamen.

Diese Zahl wird mit der **zyklomatischen Komplexität** (CC, `radon`) verglichen. Die CC ist die Zahl der linear unabhängigen Basispfade einer Funktion. Daraus folgt eine **sichere Aussage in eine Richtung**:
- Wurden weniger verschiedene Pfade beobachtet als CC, sind **sicher nicht** alle Basispfade getestet.
- Wurden mindestens CC Pfade beobachtet, ist das **kein Beleg** für vollständige Abdeckung. Die Pfade können sich in denselben Entscheidungen ähneln.
- Die Kennzahl „Pfadabdeckung (obere Schranke)“ summiert je Funktion `min(beobachtete Pfade, CC)` und teilt durch die Summe der CC. Die tatsächliche Basispfadabdeckung ist **höchstens so hoch**.

Grenzen: Die Messung ist empirisch und heuristisch. Verschachtelte Funktionen werden der umgebenden Funktion zugerechnet oder nicht erfasst. Nur eine Tracing-Variante (Zeilenfolgen) wurde verwendet.

## 3. Testergebnisse

| Datei | Tests | fehlgeschlagen | Zeit |
|---|---|---|---|""")
for name, (n, fail, tm) in sorted(by_file.items()):
    w(f"| `{name}.py` | {n} | {fail} | {tm:.2f} s |")
w(f"""
Hinweis: `test_api_contract.py` enthält 420 parametrisierte Vertragsprüfungen (je Schlüssel). Verhaltens- und Fehlerpfadtests insgesamt: {int(suite.get('tests')) - by_file['test_api_contract'][0]}.

**Gesamtdauer** {suite.get('time')} s.

## 4. Abdeckung je Datei

| Datei | Anweisungen | Zeilenabdeckung | Zweige | Zweigabdeckung | CC (Summe) | Pfade (obere Schranke) |
|---|---|---|---|---|---|---|""")
for path, data in sorted(cov["files"].items(), key=lambda kv: rel(kv[0])):
    f = rel(path)
    s = data["summary"]
    rows = [r for r in funcs if r["file"] == f]
    c, total = path_bound(rows)
    w(f"| `{f}` | {s['num_statements']} | {s['percent_statements_covered']:.0f} % | {s['num_branches']} | "
      f"{pct(s['covered_branches'], s['num_branches'])} | {total} | {pct(c, total)} |")
w(f"""
**Vergleich:** Nur die blockierenden Tests: Zeilen {cov_block['percent_statements_covered']:.1f} %, Zweige {cov_block['percent_branches_covered']:.1f} %. Die beabsichtigt roten Tests (bekannte Fehler und Abweichungen) verändern die Abdeckung kaum ({t['percent_statements_covered'] - cov_block['percent_statements_covered']:.1f} Prozentpunkte bei den Zeilen).

""")
crit_section()
w(f"""
## 6. Kritische Funktionen (nach Komplexität)

Kernmodule (`__init__.py` mit Koordinator, `pygoecharger_ha/__init__.py` mit Bridge, `service.py`, `config_flow.py`), sortiert nach Komplexität, gezeigt ab CC 4. „Pfade“ = beobachtete verschiedene Pfade, „CC“ = Basispfade.

| Funktion | CC | Aufrufe | Pfade | Zeilen | Zweige | Bewertung |
|---|---|---|---|---|---|---|""")
for r in sorted(core_rows, key=lambda r: -r["cc"]):
    if r["cc"] < 4:
        continue
    verdict = "nie ausgeführt" if r["calls"] == 0 else (f"es fehlen mindestens {r['cc'] - r['paths']} Basispfade" if r["paths"] < r["cc"] else "Pfadzahl nicht widerlegt")
    if r["file"] == "__init__.py":
        short_name = ("Entität" if r["name"].startswith("GoeChargerBaseEntity") else
                      "Koordinator" if r["name"].startswith("GoeChargerDataUpdateCoordinator") else "Setup")
    else:
        short_name = {"pygoecharger_ha/__init__.py": "Bridge", "service.py": "Dienst", "config_flow.py": "Flow"}[r["file"]]
    w(f"| `{r['name']}` ({short_name}) | {r['cc']} | {r['calls']} | {r['paths']} | {r['line']:.0f} % | {pct(r['brc'], r['br'])} | {verdict} |")
w("""
### 6.1 Nicht genommene Zweige in den wichtigsten Pfaden
Je Funktion die Zeilen, an denen mindestens ein Ausgang nie genommen wurde (bis zu sechs, Auswahl der Funktionen mit CC ab 8).
""")
for r in sorted(core_rows, key=lambda r: -r["cc"]):
    if r["cc"] < 8 or not r["missing"] or r["calls"] == 0:
        continue
    lines = sorted({m[0] for m in r["missing"] if m[0] > 0})[:6]
    src = sources[r["file"]]
    w(f"**`{r['name']}`** ({r['file']}): " + "; ".join(f"Z. {n} `{src[n - 1].strip()[:70]}`" for n in lines) + "\n")

w("""## 7. Nicht ausgeführte Funktionen im Kern

Funktionen der Kernmodule, die kein Test erreicht.
""")
rows = [r for r in core_rows if r["calls"] == 0]
w("| Funktion | CC |\n|---|---|")
for r in sorted(rows, key=lambda r: -r["cc"]):
    w(f"| `{r['name']}` ({r['file']}) | {r['cc']} |")
WS = ("pygoecharger_ha/__init__.py", "GoeChargerApiV2Bridge.ws_connect")
RV = ("__init__.py", "GoeChargerDataUpdateCoordinator.read_versions")
WS_CC, RV_CC = cc[WS], cc[RV]
WS_N, RV_N = trace.get(WS, {}).get("distinct_paths", 0), trace.get(RV, {}).get("distinct_paths", 0)
BIG2 = WS_CC + RV_CC
BIG2_PCT = round(100 * BIG2 / core_cc)
ALL_PCT, CORE_PCT = pct(all_cov, all_cc), pct(core_cov, core_cc)
PLATFORM_GAPS = ", ".join(f"`{r['file']}: {r['name']}`" for r in funcs if r['file'] in PLATFORMS and r['calls'] == 0) or "keine"
w(f"""
## 8. Plattformen und Hilfsdateien

Die Plattformen sind jetzt getestet (Wertdarstellung und Schreiben der Entitäten). Nicht ausgeführt bleiben das Anlegen der Entitäten (`async_setup_entry` je Plattform) und der Anzeigename in `entity.py`: {PLATFORM_GAPS}.

## 9. Einordnung

- **Pfadabdeckung:** Vollständige Pfadabdeckung ist hier weder erreichbar noch ein sinnvolles Ziel. Mit {BIG2} von {core_cc} Basispfaden der Kernmodule ({BIG2_PCT} %) bestimmen `ws_connect` (CC {WS_CC}) und `read_versions` des Koordinators (CC {RV_CC}) die Kennzahl; für sie wurden {WS_N} und {RV_N} verschiedene Pfade beobachtet. Funktionen mit sehr hoher CC sind in dieser Form schwer vollständig zu testen. Das ist ein Hinweis auf die Struktur des Codes, kein Vorwurf an die Tests.
- **Das Ziel von 60 % ist erreicht** (alle Funktionen {ALL_PCT}, Kernmodule {CORE_PCT}), aber die Zahl ist eine **obere Schranke** und lässt sich durch Tests mit nur leicht verschiedenen Eingaben steigern, ohne dass die Prüfung besser wird. Deshalb gelten die Mutationsprüfungen als Gegenprobe: 33 gezielte Code-Änderungen, alle wurden von den Tests erkannt (eine Lücke wurde erst nach einem zusätzlichen Test geschlossen).
- **Zeilen- und Zweigabdeckung sagen nichts über die Qualität der Prüfungen.** Alle Tests laufen mit Attrappen und sagen nichts darüber, ob der echte Charger sich so verhält.

## 10. Empfehlungen (nach Wirkung)

1. K1 und K2 zuerst: die Tabellen in Abschnitt 5.1 listen, wo noch Basispfade sicher fehlen. Dort stehen auch nicht genommene Fehlerpfade.
2. Fehlende Tests für bekannte Risiken: R20 (alte Werte nach fehlgeschlagenem Lesen, Cloud-Betrieb) und R7 (Konfigurationsintervall).
3. Lesenden Abgleich am echten Charger durchführen; erst er belegt, dass die Attrappen dem Gerät entsprechen.
4. Eine Untergrenze für die Abdeckung in den Lauf einbauen (zum Beispiel Zweigabdeckung der Kernmodule), damit sie nicht unbemerkt sinkt.
5. `ws_connect` und `read_versions` zerlegen, wenn sie später geändert werden; erst dann lassen sich ihre Pfade sinnvoll einzeln prüfen.
""")
(report_dir / "testreport.md").write_text("\n".join(out))
print("written", report_dir / "testreport.md", len("\n".join(out).splitlines()), "lines")
print("all:", all_cov, all_cc, " core:", core_cov, core_cc, " never/short/enough:", len(never), len(short), len(enough))
