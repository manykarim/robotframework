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
        m = re.match(r'^(`{3,}|~{3,})(.*)$', line)
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
# Body: 3 or 4 leading spaces, first non-space NOT ':' (to stay idempotent),
# and not a list marker.
_BODY_RE = re.compile(r'^( {3,4})(?![:\s])(\S[^\n]*)$')


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

    i = 0
    while i < n - 2:
        prev_blank = (i == 0) or (mask_lines[i].strip() == '')
        if not prev_blank:
            i += 1
            continue
        # Term candidate is i+1; body candidate is i+2
        term_idx = i + 1
        body_idx = i + 2
        if term_idx >= n or body_idx >= n:
            break

        term_line_masked = mask_lines[term_idx]
        body_line_masked = mask_lines[body_idx]

        # Term/body must both be in unmasked region (mask sets fenced lines to '').
        # If either was inside a fence, masked == ''.
        if term_line_masked == '' or body_line_masked == '':
            i += 1
            continue

        if not _TERM_RE.match(term_line_masked):
            i += 1
            continue
        if _is_list_marker(term_line_masked):
            i += 1
            continue
        body_match = _BODY_RE.match(body_line_masked)
        if not body_match:
            i += 1
            continue

        # Skip table rows (pipes), HTML tags, bare URLs, admonition headers.
        term_stripped = term_line_masked.strip()
        if term_stripped.startswith('|') or term_stripped.startswith('<'):
            i += 1
            continue
        if re.match(r'^https?://', term_stripped):
            i += 1
            continue
        if term_stripped.startswith('!!!') or term_stripped.startswith('???'):
            i += 1
            continue

        body_text = body_match.group(2)
        # def_list extension expects ': ' at column 0; use the canonical form.
        out[body_idx] = f': {body_text}'
        conversions += 1

        # Skip past body so we don't re-evaluate continuation lines.
        j = body_idx + 1
        while j < n:
            cont = mask_lines[j]
            if cont == '':
                # blank line might end def or be inside a multi-paragraph def;
                # safest: treat blank as end-of-def for next-iteration scan.
                break
            if re.match(r'^( {3,4})\S', cont):
                # continuation line stays as-is
                j += 1
                continue
            break
        i = j

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
