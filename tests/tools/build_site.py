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

import build_risk_register as risks_lib

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
table.heat{display:table;width:100%;table-layout:fixed;text-align:center}
table.heat td{height:3.2rem;text-align:center;vertical-align:middle;font-size:.9rem}
table.heat td a{color:inherit;font-weight:600;margin:0 .15rem}
table.heat td.low{background:#c9eed3;color:#0b3d1c}table.heat td.medium{background:#fbe9a3;color:#4a3700}table.heat td.high{background:#f6b3ad;color:#5a0b04}
@media (prefers-color-scheme:dark){table.heat td.low{background:#1d4a2c;color:#c9eed3}table.heat td.medium{background:#5a4a12;color:#fbe9a3}table.heat td.high{background:#6b2620;color:#f6b3ad}}
"""
PAGES = [("index.html", "Overview"), ("testreport.html", "Test report"), ("testcases.html", "Test cases"),
         ("testkonzept.html", "Test concept"), ("arc42.html", "Architecture (arc42)"), ("risks.html", "Risk register"),
         ("adr.html", "Decisions (ADR)"), ("coverage/index.html", "Coverage in detail")]
# the diagrams of the arc42 document are Mermaid; the library is loaded from a CDN with a fixed version
MERMAID = ('<script type="module">import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11.4.0/dist/mermaid.esm.min.mjs";'
           'mermaid.initialize({startOnLoad:true,theme:matchMedia("(prefers-color-scheme: dark)").matches?"dark":"default"});</script>')
# page -> (title, file relative to the docs directory); the documents are looked up by their folder
# (architecture, quality) and, for older layouts, directly in the docs directory
DOC_FILES = {"arc42.html": ("Architecture (arc42)", "architecture/arc42-ha-goecharger-api2.md"),
             "testkonzept.html": ("Test concept", "quality/testkonzept-ha-goecharger-api2.md")}
# collections of single documents (one file per decision or risk, with an index in README.md): one page is built from the
# index and the files, e.g. docs/architecture/adr -> adr.html
COLLECTIONS = {"adr": ("architecture/adr", "Architecture decisions (ADR)", r"\d{4}-"),
               "risks": ("architecture/risks", "Risk register", r"R\d{3}-")}
LINK_TARGETS = {"arc42-ha-goecharger-api2.md": "arc42.html", "testkonzept-ha-goecharger-api2.md": "testkonzept.html"}


def find_doc(docs, rel):
    root = Path(docs)
    for candidate in (root / rel, root / Path(rel).name):
        if candidate.exists():
            return candidate
    return None


def collection_files(docs, folder, pattern):
    directory = Path(docs) / folder
    if not directory.is_dir():
        return []
    return sorted(f for f in directory.glob("*.md") if re.match(pattern, f.name))


def collection_anchors(docs):
    """(collection, file name) -> heading id on the page (the first line of each file, after the front matter, is its heading)."""
    from markdown.extensions.toc import slugify
    anchors = {}
    for coll, (folder, _, pattern) in COLLECTIONS.items():
        for f in collection_files(docs, folder, pattern):
            heading = risks_lib.parse_front_matter(f.read_text())[1].splitlines()[0]
            anchors[(coll, f.name)] = slugify(heading.lstrip("# ").strip(), "-")
    return anchors


def rewrite_links(md_text, page, anchors):
    """Links between the Markdown documents point to the generated pages."""
    page_coll = next((c for c in COLLECTIONS if page.startswith(c)), None)

    def fix(m):
        path, name, frag = m.group(1), m.group(2), m.group(3) or ""
        if name in LINK_TARGETS:
            return f"]({LINK_TARGETS[name]}{frag})"
        coll = next((c for c, v in COLLECTIONS.items() if re.match(v[2], name)), None)
        if name == "README.md":
            # a README of a collection, or the one next to this page's file; any other README stays as it is
            coll = next((c for c in COLLECTIONS if f"{c}/" in path), page_coll if path.strip("./") == "" else None)
        if coll is None:
            return m.group(0)
        if name == "README.md":
            return f"]({coll}.html{frag})"
        anchor = anchors.get((coll, name))
        return f"]({coll}.html#{anchor})" if anchor else m.group(0)
    return re.sub(r"\]\(([^)#]*?)([A-Za-z0-9_.-]+\.md)(#[^)]*)?\)", fix, md_text)


def risk_document(text):
    """A risk file without its front matter; the data of the front matter is shown as a table below the heading."""
    fm, body = risks_lib.parse_front_matter(text)
    if fm is None:
        return text
    head, _, rest = body.partition("\n")
    return head + "\n\n" + risks_lib.front_matter_table(fm) + rest


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
        body = body.replace("</h1>", f"</h1><details><summary>Contents</summary><ol>{items}</ol></details>", 1)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    footer = (f"Generated {stamp}. The tests and documents were written with AI assistance (Claude Code) and reviewed by a human. "
              'Source: <a href="https://github.com/marq24/ha-goecharger-api2">marq24/ha-goecharger-api2</a> (tests/, docs/).')
    (site / name).write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{html.escape(title)}</title><style>{CSS}</style></head><body><nav><div>{nav}</div></nav>"
        f"<main>{body}{MERMAID if mermaid else ''}<footer>{footer}</footer></main></body></html>")


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
        pages["testreport.html"] = ("Test report", (Path(a.report) / "testreport.md").read_text())
        if (Path(a.report) / "html-all").exists():
            shutil.copytree(Path(a.report) / "html-all", site / "coverage", dirs_exist_ok=True)
    if a.testcases and Path(a.testcases).exists():
        pages["testcases.html"] = ("Test cases", Path(a.testcases).read_text())
    anchors = collection_anchors(a.docs) if a.docs else {}
    for name, (title, filename) in DOC_FILES.items():
        found = find_doc(a.docs, filename) if a.docs else None
        if found is not None:
            pages[name] = (title, rewrite_links(found.read_text(), name, anchors), True)
    for coll, (folder, title, pattern) in COLLECTIONS.items():
        files = collection_files(a.docs, folder, pattern) if a.docs else []
        index = (Path(a.docs) / folder / "README.md") if a.docs else None
        if not (files and index is not None and index.exists()):
            continue
        if coll == "risks":
            items = risks_lib.load(Path(a.docs) / folder)
            link = lambda r: "#" + anchors.get((coll, r["file"]), r["id"].lower())  # noqa: E731
            index_text = index.read_text()
            for key, residual in (("heatmap-current", False), ("heatmap-residual", True)):
                index_text = re.sub(rf"<!-- risk:{key} -->.*?<!-- /risk:{key} -->",
                                    lambda m, res=residual: "\n" + risks_lib.heatmap_html(items, res, link) + "\n", index_text, flags=re.S)
            parts = [index_text] + [risk_document(f.read_text()) for f in files]
        else:
            parts = [index.read_text()] + [f.read_text() for f in files]
        joined = re.sub(r"<!-- /?risk:[a-z-]+ -->\n?", "", "\n\n---\n\n".join(parts))
        pages[f"{coll}.html"] = (title, rewrite_links(joined, f"{coll}.html", anchors))
    index = ["# Regression tests for ha-goecharger-api2", "",
             "Tests, reports and documents of the Home Assistant integration [marq24/ha-goecharger-api2](https://github.com/marq24/ha-goecharger-api2) "
             "(go-eCharger). The tests are in the repository under `tests/integration` and do not change the code; this site is built from a fork.", ""]
    if a.regression and Path(a.regression).exists():
        index += ["## Latest run", "", Path(a.regression).read_text().replace("\n## ", "\n### ")
                  .replace("## Regression", "### Regression", 1), ""]
    index += ["## Pages", "", "- [Test report](testreport.html): line, branch and path coverage, criticality",
              "- [Test cases](testcases.html): every test function in one line",
              "- [Coverage in detail](coverage/index.html): line by line",
              "- [Test concept](testkonzept.html): goals, methods, figures and their limits",
              "- [Architecture (arc42)](arc42.html): structure of the integration, flows, decisions",
              "- [Risk register](risks.html): risks and technical debt with status and heat maps",
              "- [Decisions (ADR)](adr.html): architecture decisions, each with its reasoning and consequences"]
    available = set(pages) | {"index.html"} | ({"coverage/index.html"} if (site / "coverage").exists() else set())
    for name, (title, body, *toc) in pages.items():
        render(site, name, title, body, available, bool(toc))
    render(site, "index.html", "Regression tests", "\n".join(index), available)
    (site / ".nojekyll").write_text("")


if __name__ == "__main__":
    main()
