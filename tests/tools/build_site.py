"""Builds the static site for GitHub Pages from the latest results.

Usage: python build_site.py <site dir> --report <dir with testreport.md and html-all> \
           --testcases <testcases.md> [--regression <summary.md>] [--docs <dir with arc42 and test concept>]
Needs the package `markdown`. Every input is optional except the site directory; a missing part is left out.
"""
import argparse
import html
import re
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
         ("testkonzept.html", "Testkonzept"), ("arc42.html", "Architektur (arc42)"),
         ("coverage/index.html", "Abdeckung im Detail")]
# the diagrams of the arc42 document are Mermaid; the library is loaded from a CDN with a fixed version
MERMAID = ('<script type="module">import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11.4.0/dist/mermaid.esm.min.mjs";'
           'mermaid.initialize({startOnLoad:true,theme:matchMedia("(prefers-color-scheme: dark)").matches?"dark":"default"});</script>')
DOC_FILES = {"arc42.html": ("Architektur (arc42)", "arc42-ha-goecharger-api2.md"),
             "testkonzept.html": ("Testkonzept", "testkonzept-ha-goecharger-api2.md")}


def render(site, name, title, body_md, available, toc_levels=False):
    nav = "".join(f'<a href="{href}">{label}</a>' for href, label in PAGES if href in available)
    md = markdown.Markdown(extensions=["tables", "fenced_code", "toc"])
    body = md.convert(body_md)
    mermaid = '<code class="language-mermaid">' in body
    if mermaid:
        body = re.sub(r'<pre><code class="language-mermaid">(.*?)</code></pre>', r'<pre class="mermaid">\1</pre>', body, flags=re.S)
    if toc_levels:
        entries = [t for top in md.toc_tokens for t in (top["children"] if top["level"] == 1 else [top])]
        items = "".join(f'<li><a href="#{t["id"]}">{html.escape(t["name"])}</a></li>' for t in entries)
        body = body.replace("</h1>", f"</h1><details><summary>Inhalt</summary><ol>{items}</ol></details>", 1)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    (site / name).write_text(
        f'<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{html.escape(title)}</title><style>{CSS}</style></head><body><nav><div>{nav}</div></nav>"
        f"<main>{body}{MERMAID if mermaid else ''}<footer>Erzeugt am {stamp}. Die Tests wurden mit KI-Unterstützung (Claude Code) erstellt und von Oliver geprüft. "
        f'Quelle: <a href="https://github.com/OliEder/ha-goecharger-api2/tree/tests/regression-suite">Fork OliEder/ha-goecharger-api2</a>.'
        f"</footer></main></body></html>")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("site")
    ap.add_argument("--report")
    ap.add_argument("--testcases")
    ap.add_argument("--regression")
    ap.add_argument("--docs")
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
    for name, (title, filename) in DOC_FILES.items():
        if a.docs and (Path(a.docs) / filename).exists():
            pages[name] = (title, (Path(a.docs) / filename).read_text(), True)
    index = ["# Regressionstests für ha-goecharger-api2", "",
             "Tests und Berichte zur Home-Assistant-Integration [marq24/ha-goecharger-api2](https://github.com/marq24/ha-goecharger-api2) "
             "(go-eCharger). Die Tests laufen in einem Fork gegen den Code des Original-Repos und ändern dieses nicht.", ""]
    if a.regression and Path(a.regression).exists():
        index += ["## Letzter Lauf gegen eine Version des Original-Repos", "", Path(a.regression).read_text().replace("\n## ", "\n### ")
                  .replace("## Regression", "### Regression", 1), ""]
    index += ["## Seiten", "", "- [Testbericht](testreport.html): Zeilen-, Zweig- und Pfadabdeckung, Kritikalität",
              "- [Testfälle](testcases.html): jede Testfunktion in einer Zeile",
              "- [Abdeckung im Detail](coverage/index.html): Zeile für Zeile",
              "- [Testkonzept](testkonzept.html): Ziele, Methoden, Kennzahlen und ihre Grenzen",
              "- [Architektur (arc42)](arc42.html): Aufbau der Integration, Risiken, Entscheidungen"]
    available = set(pages) | {"index.html"} | ({"coverage/index.html"} if (site / "coverage").exists() else set())
    for name, (title, body, *toc) in pages.items():
        render(site, name, title, body, available, bool(toc))
    render(site, "index.html", "Regressionstests", "\n".join(index), available)
    (site / ".nojekyll").write_text("")
    print("site written to", site)


main()
