#!/usr/bin/env python3
"""Render role placeholders to attr_list-classed inline elements.

convert.py emits each semantic RST role (and option-list term) as a compact,
markdown-inert Private-Use-Area placeholder so the attr_list markup never flows
through the cross-reference / heading / table / anchor passes (which would
mangle it or demote role-bearing headings). This script is the FINAL pipeline
fix step: it runs after every other converter and fix pass and renders each
placeholder to its carrier:

    <PH_OPEN> s <content> <PH_CLOSE>  ->  *content*{.setting}
    ... n ...                          ->  *content*{.name}
    ... o ...                          ->  `content`{.option}
    ... f ...                          ->  `content`{.file}
    ... c ...                          ->  `content`{.codesc}

Backticks inside content (codesc) are carried as a sentinel and restored here,
with a wide-enough code fence. Idempotent: files with no placeholders are left
untouched.

Usage:
    python render_roles.py            # apply
    python render_roles.py --dry-run  # report only
"""

import argparse
import re
import sys
from pathlib import Path

DOCS_DIR = Path(__file__).parent.parent / "docs"

PH_OPEN = chr(0xE000)
PH_CLOSE = chr(0xE001)
BACKTICK = chr(0xE002)
PH_SEP = chr(0xE003)
UNDERSCORE = chr(0xE004)
FILLER = chr(0xE005)

# placeholder role char -> (carrier, css class)
CARRIER = {
    's': ('em', 'setting'),
    'n': ('em', 'name'),
    'o': ('code', 'option'),
    'f': ('code', 'file'),
    'c': ('code', 'codesc'),
}

# Content excludes OPEN/CLOSE/newline so a match can never span across another
# placeholder or a row boundary. If a table pass drops a CLOSE, that placeholder
# simply fails to match (recovered as plain text) instead of swallowing its
# neighbours. Content is always single-line (convert.py collapses wraps).
_PLACEHOLDER_RE = re.compile(
    PH_OPEN + r'(.)' + PH_SEP + r'([^' + PH_OPEN + PH_CLOSE + r'\n]*?)' + PH_CLOSE)


def _inline_code(text: str) -> str:
    """Wrap text in an inline code span with a fence wide enough for any
    backticks it contains (CommonMark rule). Pad a space when the content starts
    or ends with a backtick OR a space — CommonMark strips one leading and one
    trailing space from a code span, so the pad preserves an intended edge space
    (e.g. the spaced pipe ` | ` from `:codesc:`\\ |\\ ``)."""
    runs = [len(m) for m in re.findall(r'`+', text)]
    fence = '`' * ((max(runs) + 1) if runs else 1)
    edge = (text[:1] in ('`', ' ')) or (text[-1:] in ('`', ' '))
    pad = ' ' if (edge and text.strip()) else ''
    return f'{fence}{pad}{text}{pad}{fence}'


_ORPHAN_PREFIX = re.compile(PH_OPEN + r'.?' + PH_SEP)
_SENTINELS = (PH_OPEN, PH_CLOSE, PH_SEP, FILLER)


def render(text: str) -> str:
    def repl(match):
        char, inner = match.group(1), match.group(2)
        inner = inner.replace(FILLER, '').replace(BACKTICK, '`').replace(UNDERSCORE, '_')
        carrier, cls = CARRIER.get(char, ('code', 'codesc'))
        if carrier == 'em':
            return f'*{inner}*{{.{cls}}}'
        return f'{_inline_code(inner)}{{.{cls}}}'

    text = _PLACEHOLDER_RE.sub(repl, text)

    # Defensive recovery: a downstream table fixer can split or duplicate a cell
    # and thereby orphan a placeholder fragment (e.g. a duplicated `OPEN+char+SEP`
    # prefix). Strip any orphan prefix and lone sentinels so nothing invisible
    # ever ships; decode content sentinels back to real characters.
    if any(ch in text for ch in _SENTINELS):
        text = _ORPHAN_PREFIX.sub('', text)
        for ch in _SENTINELS:
            text = text.replace(ch, '')
        text = text.replace(BACKTICK, '`').replace(UNDERSCORE, '_')
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="Report only; do not write")
    args = parser.parse_args()

    if not DOCS_DIR.is_dir():
        print(f"ERROR: docs directory not found: {DOCS_DIR}", file=sys.stderr)
        return 1

    changed = 0
    rendered = 0
    for md in sorted(DOCS_DIR.rglob("*.md")):
        text = md.read_text(encoding="utf-8")
        if PH_OPEN not in text:
            continue
        n = len(_PLACEHOLDER_RE.findall(text))
        new_text = render(text)
        rendered += n
        if new_text != text:
            changed += 1
            if not args.dry_run:
                md.write_text(new_text, encoding="utf-8")

    # Safety: no placeholder characters should ever remain.
    leftovers = 0
    if not args.dry_run:
        for md in DOCS_DIR.rglob("*.md"):
            t = md.read_text(encoding="utf-8")
            if any(ch in t for ch in (PH_OPEN, PH_CLOSE, BACKTICK, PH_SEP, UNDERSCORE, FILLER)):
                leftovers += 1
                print(f"  WARNING: leftover placeholder chars in {md.relative_to(DOCS_DIR)}", file=sys.stderr)

    print(f"render_roles: rendered {rendered} role placeholder(s) across {changed} file(s)"
          + (f"; {leftovers} file(s) with leftovers" if leftovers else ""))
    return 1 if leftovers else 0


if __name__ == "__main__":
    sys.exit(main())
