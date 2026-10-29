"""Builds the static site for GitHub Pages from the latest results.

Usage: python build_site.py <site dir> --report <dir with testreport.md and html-all> \
           --testcases <testcases.md> [--regression <summary.md>]
Needs the package `markdown`. Every input is optional except the site directory; a missing part is left out.
"""
import argparse
import html
import shutil
from datetime import datetime, timezone
from pathlib import Path

import markdown

CSS = """
:root{--bg:#fff;--fg:#1f2328;--muted:#59636e;--line:#d1d9e0;--head:#f6f8fa;--link:#0969da}
@media (prefers-color-scheme:dark){:root{--bg:#0d1117;--fg:#e6edf3;--muted:#9198a1;--line:#3d444d;--head:#151b23;--link:#4493f8}}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.55 system-ui,sans-serif}
main{max-width:60rem;margin:0 auto;padding:1rem 16px 4rem}
nav{border-bottom:1px solid var(--line);background:var(--head)}
nav div{max-width:60rem;margin:0 auto;padding:.7rem 16px;display:flex;gap:1.2rem;flex-wrap:wrap}
a{color:var(--link)}h1,h2,h3{line-height:1.25}
table{border-collapse:collapse;display:block;overflow-x:auto;max-width:100%}
th,td{border:1px solid var(--line);padding:.3rem .6rem;text-align:left;vertical-align:top}
th{background:var(--head)}code{background:var(--head);padding:.1rem .3rem;border-radius:4px}
footer{color:var(--muted);font-size:.9rem;margin-top:3rem}
"""
PAGES = [("index.html", "Übersicht"), ("testreport.html", "Testbericht"), ("testcases.html", "Testfälle"),
         ("coverage/index.html", "Abdeckung im Detail")]


def render(site, name, title, body_md, available):
    nav = "".join(f'<a href="{href}">{label}</a>' for href, label in PAGES if href in available)
    body = markdown.markdown(body_md, extensions=["tables", "fenced_code"])
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    (site / name).write_text(
        f'<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{html.escape(title)}</title><style>{CSS}</style></head><body><nav><div>{nav}</div></nav>"
        f"<main>{body}<footer>Erzeugt am {stamp}. Die Tests wurden mit KI-Unterstützung (Claude Code) erstellt und von Oliver geprüft. "
        f'Quelle: <a href="https://github.com/OliEder/ha-goecharger-api2/tree/tests/regression-suite">Fork OliEder/ha-goecharger-api2</a>.'
        f"</footer></main></body></html>")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("site")
    ap.add_argument("--report")
    ap.add_argument("--testcases")
    ap.add_argument("--regression")
    a = ap.parse_args()
    site = Path(a.site)
    site.mkdir(parents=True, exist_ok=True)
    pages = {}
    if a.report and (Path(a.report) / "testreport.md").exists():
        pages["testreport.html"] = ("Testbericht", (Path(a.report) / "testreport.md").read_text())
        if (Path(a.report) / "html-all").exists():
            shutil.copytree(Path(a.report) / "html-all", site / "coverage", dirs_exist_ok=True)
    if a.testcases and Path(a.testcases).exists():
        pages["testcases.html"] = ("Testfälle", Path(a.testcases).read_text())
    index = ["# Regressionstests für ha-goecharger-api2", "",
             "Tests und Berichte zur Home-Assistant-Integration [marq24/ha-goecharger-api2](https://github.com/marq24/ha-goecharger-api2) "
             "(go-eCharger). Die Tests laufen in einem Fork gegen den Code des Original-Repos und ändern dieses nicht.", ""]
    if a.regression and Path(a.regression).exists():
        index += ["## Letzter Lauf gegen eine Version des Original-Repos", "", Path(a.regression).read_text().replace("\n## ", "\n### ")
                  .replace("## Regression", "### Regression", 1), ""]
    index += ["## Seiten", "", "- [Testbericht](testreport.html): Zeilen-, Zweig- und Pfadabdeckung, Kritikalität",
              "- [Testfälle](testcases.html): jede Testfunktion in einer Zeile",
              "- [Abdeckung im Detail](coverage/index.html): Zeile für Zeile",
              "- Dokumente (arc42, Testkonzept): [docs/quality](https://github.com/OliEder/ha-goecharger-api2/tree/tests/regression-suite/docs/quality)"]
    available = set(pages) | {"index.html"} | ({"coverage/index.html"} if (site / "coverage").exists() else set())
    for name, (title, body) in pages.items():
        render(site, name, title, body, available)
    render(site, "index.html", "Regressionstests", "\n".join(index), available)
    (site / ".nojekyll").write_text("")
    print("site written to", site)


main()
