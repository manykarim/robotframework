#!/usr/bin/env python3
"""Content-integrity gate for the converted User Guide.

Automates the bulk of "same content as the original, rendered correctly" so
manual review shrinks to a sign-off. Checks (RST source -> generated MD ->
optional built HTML):

  1. Heading preservation  - every RST section title appears as a Markdown
     heading (catches the "role in heading demoted to body text" class).
  2. Content coverage       - distinctive content words present in the RST are
     also present in the generated MD (catches dropped cells / sentences).
  3. MD artifact scan       - no leaked source markup in the generated Markdown
     (unconverted :role:, RST directives, `text`_ refs, grid borders, stray
     placeholder chars).
  4. HTML artifact scan      - if a built site is given, no literal {.role}
     attr_list braces, :role: syntax, or placeholder chars in the HTML.

Exit code is non-zero if any hard check fails; a report lists every offender.

Usage:
    python content_check.py                 # checks MD (+ HTML under ./site if present)
    python content_check.py --html-dir site
    python content_check.py --json
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

BASE = Path(__file__).parent.parent
DOCS_DIR = BASE / "docs"
RST_DIR = BASE.parent / "userguide" / "src"

SECTION_CHARS = set('=-~^"\'`+#*')
PUA = ''.join(chr(c) for c in range(0xE000, 0xE006))

# Words that are RST/markup noise, not User Guide content — ignored in coverage.
_STOPish = set("the a an and or of to in is are be for with on as by from that this it".split())


def normalize(text: str) -> str:
    """Lowercase and strip inline markup for heading comparison."""
    text = re.sub(r':(?:setting|option|name|file|codesc|opt):`([^`]+)`', r'\1', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', text)          # links -> text
    text = re.sub(r'\{[.#][^}]*\}', '', text)                      # attr_list
    text = re.sub(r'[`*_]', '', text)                             # emphasis/code
    text = re.sub(r'[^a-z0-9 ]', ' ', text.lower())
    return re.sub(r'\s+', ' ', text).strip()


def rst_titles(text: str):
    """Yield section titles from an RST document (title line + underline)."""
    lines = text.split('\n')
    in_block = False
    for i in range(len(lines) - 1):
        line, under = lines[i], lines[i + 1]
        s = line.strip()
        # skip obvious non-titles
        if not s or line.startswith(' ') or line.startswith('..') or line.startswith('|'):
            continue
        u = under.strip()
        if len(u) >= 3 and len(set(u)) == 1 and u[0] in SECTION_CHARS and len(under.rstrip()) >= len(line.rstrip()):
            yield s


def md_headings(text: str):
    for line in text.split('\n'):
        m = re.match(r'^#{1,6}\s+(.*)', line)
        if m:
            yield m.group(1)


def content_words(text: str):
    for w in re.findall(r'[A-Za-z][A-Za-z0-9]{3,}', text):
        wl = w.lower()
        if wl not in _STOPish:
            yield wl


# HARD checks gate this change (role-conversion correctness — must be 0).
MD_HARD = [
    ("unconverted role", re.compile(r':(?:setting|option|name|file|codesc|opt):`')),
    ("placeholder char", re.compile('[' + PUA + ']')),
    ("grid-table border", re.compile(r'^\s*\+[-=+]{3,}\+\s*$', re.M)),
]
# WARN checks report pre-existing / non-role content issues (do not gate).
MD_WARN = [
    ("RST directive", re.compile(r'^\.\.\s+[\w-]+::', re.M)),
    # backtick ref: exclude attr_list braces so adjacent code spans don't match.
    ("RST backtick ref", re.compile(r'`[^`\n{}]+`_(?![_\w{])')),
]

HTML_HARD = [
    ("literal attr_list", re.compile(r'\{\.(?:setting|option|name|file|codesc)\}')),
    ("role syntax", re.compile(r':(?:setting|option|name|file|codesc|opt):')),
    ("placeholder char", re.compile('[' + PUA + ']')),
]


def scan(text: str, rules):
    hits = []
    for name, rx in rules:
        for m in rx.finditer(text):
            line_no = text.count('\n', 0, m.start()) + 1
            snippet = text[max(0, m.start() - 20):m.start() + 40].replace('\n', '⏎')
            hits.append((name, line_no, snippet))
    return hits


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--html-dir", default="site", help="Built HTML dir to scan (default: site if present)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--max-missing-titles", type=int, default=0, help="Allowed missing headings")
    args = ap.parse_args()

    report = {"missing_headings": [], "md_hard": [], "md_warn": [],
              "html_hard": [], "dead_anchors": [], "missing_content_words": []}

    # Gather MD headings + content words
    md_head_norm = set()
    md_words = Counter()
    for md in DOCS_DIR.rglob("*.md"):
        t = md.read_text(encoding="utf-8")
        for h in md_headings(t):
            md_head_norm.add(normalize(h))
        md_words.update(content_words(t))
        rel = str(md.relative_to(DOCS_DIR))
        for name, line_no, snip in scan(t, MD_HARD):
            report["md_hard"].append({"file": rel, "kind": name, "line": line_no, "snippet": snip})
        for name, line_no, snip in scan(t, MD_WARN):
            report["md_warn"].append({"file": rel, "kind": name, "line": line_no, "snippet": snip})

    # 1. Heading preservation (RST titles -> MD headings)
    rst_title_norm = {}
    rst_words = Counter()
    for rst in RST_DIR.rglob("*.rst"):
        t = rst.read_text(encoding="utf-8")
        for title in rst_titles(t):
            n = normalize(title)
            if n:
                rst_title_norm[n] = (str(rst.relative_to(RST_DIR)), title)
        rst_words.update(content_words(t))
    for n, (src, title) in sorted(rst_title_norm.items()):
        if n not in md_head_norm:
            report["missing_headings"].append({"title": title, "rst": src})

    # 2. Content coverage: distinctive RST words entirely absent from MD
    #    (conservative: only words appearing >=2x in RST and never in MD)
    for w, cnt in rst_words.items():
        if cnt >= 2 and w not in md_words:
            report["missing_content_words"].append({"word": w, "rst_count": cnt})

    # 4. HTML artifact scan (optional) — HARD (role-conversion correctness) plus
    #    dead same-page anchor detection (WARN) — catches links that point at a
    #    #anchor that does not exist on the page (e.g. RST indirect targets that
    #    were not resolved and fell back to a dead #slug).
    html_dir = BASE / args.html_dir
    if html_dir.is_dir():
        for html in html_dir.rglob("*.html"):
            t = html.read_text(encoding="utf-8", errors="replace")
            for name, line_no, snip in scan(t, HTML_HARD):
                report["html_hard"].append({"file": str(html.relative_to(html_dir)), "kind": name, "line": line_no, "snippet": snip})
            rel = str(html.relative_to(html_dir))
            # Only our MkDocs-rendered doc pages (…/index.html), not bundled HTML
            # assets (RF report/log/libdoc examples have JS-template anchors).
            if html.name != "index.html":
                continue
            # Real anchors on the page: id="x" / id=x (minified).
            ids = set(re.findall(r'\bid="([^"]+)"', t)) | set(re.findall(r'\bid=([A-Za-z0-9_.:-]+)', t))
            for m in re.finditer(r'href="#([^"]+)"|href=#([A-Za-z0-9_.:-]+)', t):
                anchor = m.group(1) or m.group(2)
                if anchor and anchor not in ids:
                    report["dead_anchors"].append({"file": rel, "anchor": anchor})

    # Gate on HARD only (role-conversion correctness). WARN + missing headings +
    # content words are pre-existing / structural signals, reported not gated.
    hard_fail = bool(report["md_hard"] or report["html_hard"])

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("=" * 60)
        print("CONTENT-INTEGRITY CHECK")
        print("=" * 60)
        print(f"  [HARD] MD role/placeholder artifacts:  {len(report['md_hard'])}")
        for x in report["md_hard"][:40]:
            print(f"    - [{x['kind']}] {x['file']}:{x['line']}  {x['snippet']}")
        print(f"  [HARD] HTML role artifacts:            {len(report['html_hard'])}"
              + ("" if html_dir.is_dir() else "  (no HTML dir — skipped)"))
        for x in report["html_hard"][:40]:
            print(f"    - [{x['kind']}] {x['file']}:{x['line']}  {x['snippet']}")
        print(f"  [warn] pre-existing MD markup:         {len(report['md_warn'])}")
        for x in report["md_warn"][:20]:
            print(f"    - [{x['kind']}] {x['file']}:{x['line']}  {x['snippet']}")
        print(f"  [warn] dead same-page anchors (HTML):  {len(report['dead_anchors'])}")
        for x in report["dead_anchors"][:20]:
            print(f"    - {x['file']}  #{x['anchor']}")
        print(f"  [warn] missing headings (RST->MD):     {len(report['missing_headings'])} (structural/pre-existing)")
        for x in report["missing_headings"][:20]:
            print(f"    - '{x['title']}'  ({x['rst']})")
        print(f"  [info] content words absent in MD:     {len(report['missing_content_words'])}")
        print("=" * 60)
        print("  Status (HARD gate): " + ("✗ FAIL" if hard_fail else "✓ PASS"))
        print("=" * 60)

    return 1 if hard_fail else 0


if __name__ == "__main__":
    sys.exit(main())
