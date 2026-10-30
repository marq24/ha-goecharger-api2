"""Keeps the risk documents in docs/architecture/risks consistent with their front matter.

Every risk file (R001-....md) starts with a small front matter block (id, date, category, probability, impact,
residual values, strategy, status, owner, review). This script generates everything that is derived from it:
- the assessment table and the status line inside each risk file (between the marker comments)
- the heat maps and the overview table in the README of the folder (between the marker comments)
- links: a reference like R15 in the documents under docs/architecture and docs/quality becomes a link to the risk file

Usage: python tests/tools/build_risk_register.py [docs/architecture/risks] [--check]
Without --check the files are rewritten. With --check nothing is written and the exit code is 1 when a file
is out of date (used in CI).
build_site.py imports heatmap_html(), front_matter_table(), load() and parse_front_matter() from here for the web page.
"""
import html
import os
import re
import sys
from pathlib import Path

CATEGORIES = {
    "ARCH": "Technology / architecture", "SEC": "Security & privacy", "INT": "Integration / third party",
    "QA": "Quality / testing", "DOC": "Documentation", "MAINT": "Maintainability",
}
STRATEGIES = {"mitigate": "Mitigate", "accept": "Accept", "avoid": "Avoid", "transfer": "Transfer"}
STATUS = {
    "open": "Open", "fixed": "Closed (fixed)", "settled": "Closed (settled, not a defect)",
    "superseded": "Closed (superseded)", "note": "Accepted (note)",
}
CLOSED = {"fixed", "settled", "superseded"}
BAND = {"low": ("low", "🟩"), "medium": ("medium", "🟨"), "high": ("high", "🟥")}
OWNER_NONE = "not named (to be set by the maintainer)"
REVIEW = {"release": "with every new release"}
SCALE = ("Scale: W 1 (very unlikely) to 5 (very likely), A 1 (low) to 5 (severe); "
         "score 1 to 5 low, 6 to 12 medium, 15 and above high.")


def band(score):
    return "low" if score <= 5 else "medium" if score <= 12 else "high"


def parse_front_matter(text):
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None, text
    fm = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        fm[k.strip()] = v.strip()
    return fm, text[m.end():]


def load(folder):
    risks = []
    for f in sorted(Path(folder).glob("R[0-9][0-9][0-9]-*.md")):
        fm, body = parse_front_matter(f.read_text())
        if fm is None:
            raise SystemExit(f"{f}: front matter missing")
        for k in ("id", "date", "category", "probability", "impact", "residual_probability", "residual_impact", "strategy", "status"):
            if k not in fm:
                raise SystemExit(f"{f}: front matter key '{k}' missing")
        for k, table in (("category", CATEGORIES), ("strategy", STRATEGIES), ("status", STATUS)):
            if fm[k] not in table:
                raise SystemExit(f"{f}: unknown {k} '{fm[k]}'")
        fm = dict(fm, w=int(fm["probability"]), a=int(fm["impact"]), rw=int(fm["residual_probability"]),
                  ra=int(fm["residual_impact"]), file=f.name, n=int(fm["id"][1:]), title=body.splitlines()[0].partition(":")[2].strip() or body.splitlines()[0].lstrip("# ").strip())
        risks.append(fm)
    return sorted(risks, key=lambda r: r["n"])


def front_matter_table(fm):
    owner = fm.get("owner") or OWNER_NONE
    review = REVIEW.get(fm.get("review", "release"), fm.get("review", ""))
    return (f"| Field | Value |\n|---|---|\n| ID | {fm['id']} |\n| Date recorded | {fm['date']} |\n"
            f"| Category | {CATEGORIES[fm['category']]} |\n| Status | {STATUS[fm['status']]} |\n"
            f"| Risk owner | {owner} |\n| Next review | {review} |\n")


def assessment_block(r):
    s, rs = r["w"] * r["a"], r["rw"] * r["ra"]
    return (f"| | W | A | Score (W × A) | |\n|---|---|---|---|---|\n"
            f"| Assessment | {r['w']} | {r['a']} | {s} | {BAND[band(s)][0]} |\n"
            f"| Residual risk after the countermeasure | {r['rw']} | {r['ra']} | {rs} | {BAND[band(rs)][0]} |\n\n"
            f"Risk strategy: **{STRATEGIES[r['strategy']]}**. {SCALE}")


def status_block(r):
    return STATUS[r["status"]]


def cells(risks, residual):
    grid = {}
    for r in risks:
        if r["status"] in CLOSED:
            continue
        w, a = (r["rw"], r["ra"]) if residual else (r["w"], r["a"])
        grid.setdefault((w, a), []).append(r)
    return grid


def heatmap_md(risks, residual):
    grid = cells(risks, residual)
    rows = ["| W \\ A | 1 | 2 | 3 | 4 | 5 |", "|---|---|---|---|---|---|"]
    for w in range(5, 0, -1):
        line = f"| **{w}** |"
        for a in range(1, 6):
            ids = ", ".join(f"[{r['id']}]({r['file']})" for r in grid.get((w, a), []))
            line += f" {BAND[band(w * a)][1]} {ids} |"
        rows.append(line)
    return "\n".join(rows)


def heatmap_html(risks, residual, link=lambda r: f"#{r['id'].lower()}"):
    """Colour grid for the web page; link(r) gives the target of an id."""
    grid = cells(risks, residual)
    out = ['<table class="heat"><thead><tr><th>W \\ A</th>' + "".join(f"<th>{a}</th>" for a in range(1, 6)) + "</tr></thead><tbody>"]
    for w in range(5, 0, -1):
        out.append(f"<tr><th>{w}</th>")
        for a in range(1, 6):
            ids = " ".join(f'<a href="{html.escape(link(r))}" title="{html.escape(r["title"])}">{r["id"]}</a>' for r in grid.get((w, a), []))
            out.append(f'<td class="{band(w * a)}" title="W {w} × A {a} = {w * a}">{ids}</td>')
        out.append("</tr>")
    out.append("</tbody></table>")
    return "".join(out)


def table_block(risks):
    rows = ["| ID | Title | Category | W | A | Score | Strategy | Status |", "|---|---|---|---|---|---|---|---|"]
    for r in risks:
        s = r["w"] * r["a"]
        rows.append(f"| [{r['id']}]({r['file']}) | {r['title']} | {CATEGORIES[r['category']]} | {r['w']} | {r['a']} | "
                    f"{s} ({BAND[band(s)][0]}) | {STRATEGIES[r['strategy']]} | {STATUS[r['status']]} |")
    return "\n".join(rows)


def replace_block(text, name, content, where):
    pattern = re.compile(rf"(<!-- risk:{name} -->\n).*?(\n<!-- /risk:{name} -->)", re.S)
    if not pattern.search(text):
        raise SystemExit(f"{where}: marker 'risk:{name}' missing")
    return pattern.sub(lambda m: m.group(1) + content + m.group(2), text)


REF = re.compile(r"(?<![\[\w/`-])R(\d{1,3})(?![\w\]`-])(?!\]\()")


def link_refs(text, path, files):
    """Turns plain references like R15 into links; skips the front matter, code blocks, headings and inline code."""
    lines = text.split("\n")
    in_front, fence = text.startswith("---\n"), False
    out = []
    for i, line in enumerate(lines):
        if in_front:
            if i > 0 and line == "---":
                in_front = False
            out.append(line)
            continue
        if line.startswith("```"):
            fence = not fence
        if fence or line.startswith("```") or line.lstrip().startswith("#") or "<!--" in line:
            out.append(line)
            continue

        def link(m):
            n = int(m.group(1))
            if n not in files or files[n] == path:
                return m.group(0)
            return f"[R{n:03d}]({Path(os.path.relpath(files[n], path.parent)).as_posix()})"
        # leave inline code alone
        parts = re.split(r"(`[^`]*`)", line)
        out.append("".join(p if p.startswith("`") else REF.sub(link, p) for p in parts))
    return "\n".join(out)


def link_all(folder, write):
    files = {int(f.name[1:4]): f for f in Path(folder).glob("R[0-9][0-9][0-9]-*.md")}
    docs = Path(folder).parent.parent
    stale = []
    for base in (docs / "architecture", docs / "quality"):
        for path in sorted(base.rglob("*.md")):
            text = path.read_text()
            new = link_refs(text, path, files)
            if new != text:
                stale.append(path)
                if write:
                    path.write_text(new)
    return stale


def process(folder, write):
    """Returns the list of files that are (or were) out of date."""
    risks = load(folder)
    stale = []
    for r in risks:
        path = Path(folder) / r["file"]
        text = path.read_text()
        new = replace_block(text, "assessment", assessment_block(r), path)
        new = replace_block(new, "status", status_block(r), path)
        if new != text:
            stale.append(path)
            if write:
                path.write_text(new)
    readme = Path(folder) / "README.md"
    text = readme.read_text()
    new = replace_block(text, "heatmap-current", heatmap_md(risks, False), readme)
    new = replace_block(new, "heatmap-residual", heatmap_md(risks, True), readme)
    new = replace_block(new, "table", table_block(risks), readme)
    if new != text:
        stale.append(readme)
        if write:
            readme.write_text(new)
    return stale


def main(argv):
    check = "--check" in argv
    args = [a for a in argv if not a.startswith("--")]
    folder = Path(args[0]) if args else Path("docs/architecture/risks")
    if not folder.is_dir():
        print(f"{folder} does not exist, nothing to do")
        return 0
    stale = process(folder, write=not check)
    stale += link_all(folder, write=not check)
    if stale:
        print(("out of date: " if check else "updated: ") + ", ".join(str(p) for p in stale))
        return 1 if check else 0
    print("risk documents are up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
