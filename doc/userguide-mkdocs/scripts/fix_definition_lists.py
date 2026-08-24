#!/usr/bin/env python3
"""
Convert Pandoc-style RST definition lists to Material `def_list` syntax.

Pandoc emits RST def-lists as:
    Term
        Description body...

Material's `def_list` extension recognises only:
    Term
    :   Description body...

This single-pass rewriter bridges the dialect gap. Idempotent: definitions
already starting with `:` are left untouched.

Usage:
    python fix_definition_lists.py            # apply
    python fix_definition_lists.py --dry-run  # preview
    python fix_definition_lists.py --report   # detailed
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple


DOCS_DIR = Path(__file__).parent.parent / "docs"


def mask_fenced_blocks(text: str) -> str:
    """Replace fenced-block content with blanks so line numbers stay aligned.

    CommonMark rule: closer must match the open fence's char/length and have
    no info string. A run-with-info inside an open fence is literal content.
    """
    out = []
    in_fence = False
    fence_char = None
    fence_count = 0
    for line in text.split('\n'):
        # Allow a leading indent so fences nested inside a list item are masked
        # too — otherwise the nested code's `def foo():` line is scanned as a
        # definition term and gets a bogus `: ` marker injected.
        m = re.match(r'^[ \t]*(`{3,}|~{3,})(.*)$', line)
        opening_now = False
        closing_now = False
        if m:
            run = m.group(1)
            info = m.group(2).strip()
            if not in_fence:
                in_fence = True
                fence_char = run[0]
                fence_count = len(run)
                opening_now = True
            elif run[0] == fence_char and len(run) >= fence_count and not info:
                in_fence = False
                closing_now = True
        if in_fence and not opening_now:
            out.append('')
        elif closing_now:
            out.append('')
        else:
            out.append(line)
    return '\n'.join(out)


# Term: anything not starting with whitespace, #, -, *, >, digit, :, |
# Backticks are allowed because backtick-wrapped names are common def-list
# terms in the RF guide (e.g. `\`robot:exit-on-failure\`` for reserved tags).
_TERM_RE = re.compile(r'^[^\s#\->\*\d:|][^\n]*$')
# Body: 2, 3 or 4 leading spaces, first non-space NOT ':' (to stay idempotent),
# and not a list marker. 2-space is the RST minimum indent — the
# ROBOT_LIBRARY_SCOPE list (`TEST`/`SUITE`/`GLOBAL`) uses it, and without it the
# term merged with its body into one paragraph instead of a <dl>.
_BODY_RE = re.compile(r'^( {2,4})(?![:\s])(\S[^\n]*)$')


def _is_list_marker(line: str) -> bool:
    return bool(re.match(r'^\s*([-*+]|\d+\.)\s', line))


def convert_definition_lists(content: str) -> Tuple[str, int]:
    """Rewrite `term\\n    body` to `term\\n: body` outside fenced blocks.

    Returns the rewritten content and the count of definitions converted.
    """
    masked = mask_fenced_blocks(content)
    src_lines = content.split('\n')
    mask_lines = masked.split('\n')
    out = list(src_lines)
    n = len(src_lines)
    conversions = 0

    conv = [0]  # boxed so the nested helper can increment it

    def convert_item(term_idx):
        """Convert one definition item (term at term_idx, body at term_idx+1).

        Returns the index just past the body (start of the next line), or None
        if term_idx is not a valid term+body pair. Does NOT require a blank line
        before the term, so CONSECUTIVE items (no blank between them) convert as
        part of the same definition list — matching docutils, which renders a run
        of `term\\n  body\\nterm\\n  body` as a single multi-item <dl>.
        """
        body_idx = term_idx + 1
        if term_idx >= n or body_idx >= n:
            return None
        term_m = mask_lines[term_idx]
        body_m = mask_lines[body_idx]
        if term_m == '' or body_m == '':          # inside a fence (masked blank)
            return None
        if not _TERM_RE.match(term_m) or _is_list_marker(term_m):
            return None
        bmatch = _BODY_RE.match(body_m)            # 2-4 space body, not `: ` already
        if not bmatch:
            return None
        ts = term_m.strip()
        if (ts.startswith('|') or ts.startswith('<') or ts.startswith('!!!')
                or ts.startswith('???') or re.match(r'^https?://', ts)):
            return None

        body_indent = len(bmatch.group(1))
        out[body_idx] = f': {bmatch.group(2)}'
        conv[0] += 1

        # Re-indent the rest of the definition body to 4 spaces so multi-line and
        # multi-paragraph definitions stay inside the <dd>. Internal blank lines
        # are kept while a following line is still indented to the body column; a
        # blank followed by a column-0 line (or a dedent) ends the definition.
        j = body_idx + 1
        while j < n:
            cont = mask_lines[j]
            if cont == '':
                k = j + 1
                while k < n and mask_lines[k] == '':
                    k += 1
                if k < n and re.match(r'^ {' + str(body_indent) + r',}\S', mask_lines[k]):
                    j += 1               # internal blank — keep, stay in def
                    continue
                break                    # blank ends the definition
            cm = re.match(r'^( +)(\S.*)$', cont)
            if cm and len(cm.group(1)) >= body_indent:
                extra = len(cm.group(1)) - body_indent
                src_m = re.match(r'^( +)(\S.*)$', src_lines[j])
                text = src_m.group(2) if src_m else src_lines[j].strip()
                out[j] = ' ' * (4 + extra) + text
                j += 1
                continue
            break
        return j

    i = 0
    while i < n - 2:
        prev_blank = (i == 0) or (mask_lines[i].strip() == '')
        if not prev_blank:
            i += 1
            continue
        end = convert_item(i + 1)
        if end is None:
            i += 1
            continue
        # Keep converting CONSECUTIVE items (no blank between them) as part of
        # the same <dl>; without this, only the blank-preceded first item was
        # converted and the rest collapsed into a run-on paragraph.
        while end < n - 1:
            nxt = convert_item(end)
            if nxt is None:
                break
            end = nxt
        i = end

    conversions = conv[0]
    return '\n'.join(out), conversions


def process_file(path: Path, dry_run: bool = False) -> int:
    original = path.read_text(encoding='utf-8')
    new_content, count = convert_definition_lists(original)
    if not dry_run and new_content != original:
        path.write_text(new_content, encoding='utf-8')
    return count


def main():
    parser = argparse.ArgumentParser(
        description='Convert Pandoc-style RST def-lists to Material def_list syntax.'
    )
    parser.add_argument('--dry-run', action='store_true',
                        help='Show changes without writing files')
    parser.add_argument('--report', action='store_true',
                        help='Detailed per-file report')
    parser.add_argument('--file', type=str, help='Process a single file')
    args = parser.parse_args()

    if args.file:
        files = [Path(args.file)]
    else:
        files = sorted(DOCS_DIR.rglob('*.md'))

    total = 0
    changed_files = 0
    for f in files:
        if not f.exists():
            continue
        # Skip CamelCase legacy directories
        try:
            parts = f.relative_to(DOCS_DIR).parts
            if any(p[0].isupper() for p in parts[:-1]):
                continue
        except ValueError:
            pass
        count = process_file(f, dry_run=args.dry_run)
        if count > 0:
            changed_files += 1
            total += count
            if args.report:
                rel = f.relative_to(DOCS_DIR) if str(f).startswith(str(DOCS_DIR)) else f
                print(f'  {rel}: {count} def(s) converted')

    mode = 'DRY RUN' if args.dry_run else 'APPLIED'
    print(f'[{mode}] {total} definitions converted across {changed_files} file(s).')
    return 0


if __name__ == '__main__':
    sys.exit(main())
