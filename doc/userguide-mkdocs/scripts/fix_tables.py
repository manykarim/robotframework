#!/usr/bin/env python3
"""Fix malformed Markdown tables converted from RST.

This script fixes tables that have:
- `#### |` prefixes corrupting table rows
- `   |` indented rows
- `.. table::` RST directives
- `:class:` and `:widths:` RST options
- Standalone `####` lines
- Missing separator rows after headers
- RST simple-table bodies leaked into MD as raw `===== =====` separators
- Indented `<table>` HTML blocks that MkDocs renders as `<pre>` instead of HTML
"""
import re
import sys
from pathlib import Path


# Matches a simple-table separator line: 2+ runs of `=` separated by spaces.
SIMPLE_TABLE_SEP_RE = re.compile(r'^(?P<indent>[ \t]*)=+(?:[ \t]+=+)+[ \t]*$')

# Matches a fenced code-block boundary line (3+ backticks, optional info string).
FENCE_RE = re.compile(r'^[ \t]*`{3,}.*$')


def _mask_fenced_blocks(content: str) -> tuple[str, list[str]]:
    """Replace fenced code blocks with placeholders so they aren't scanned.

    Returns (masked_content, saved_blocks). Use _unmask_fenced_blocks to
    restore the originals.
    """
    lines = content.split('\n')
    saved: list[str] = []
    out: list[str] = []
    in_fence = False
    fence_lines: list[str] = []

    for line in lines:
        if not in_fence and FENCE_RE.match(line):
            in_fence = True
            fence_lines = [line]
            continue
        if in_fence:
            fence_lines.append(line)
            if FENCE_RE.match(line):
                in_fence = False
                placeholder = f"<<<FENCED_BLOCK_{len(saved)}>>>"
                saved.append('\n'.join(fence_lines))
                out.append(placeholder)
                fence_lines = []
            continue
        out.append(line)

    if fence_lines:
        # Unterminated fence — keep original lines as-is.
        out.extend(fence_lines)

    return '\n'.join(out), saved


def _unmask_fenced_blocks(content: str, saved: list[str]) -> str:
    for i, block in enumerate(saved):
        content = content.replace(f"<<<FENCED_BLOCK_{i}>>>", block)
    return content


def remove_rst_table_directives(content: str) -> str:
    """Convert RST table directives to markdown headers or remove them."""
    # Convert `.. table:: Title` to nothing (title not needed, context clear)
    content = re.sub(r'^\.\. table::.*$\n', '', content, flags=re.MULTILINE)
    # Remove :class: and :widths: lines
    content = re.sub(r'^\s+:(class|widths):.*$\n', '', content, flags=re.MULTILINE)
    return content


def _column_spans(sep_line: str) -> list[tuple[int, int]]:
    """Return (start, end_exclusive) spans for each `=` run in the separator."""
    spans: list[tuple[int, int]] = []
    i = 0
    n = len(sep_line)
    while i < n:
        if sep_line[i] == '=':
            start = i
            while i < n and sep_line[i] == '=':
                i += 1
            spans.append((start, i))
        else:
            i += 1
    return spans


def _slice_row(row: str, spans: list[tuple[int, int]]) -> list[str]:
    """Slice a row into cells using column spans, but extend the last span
    to end-of-line so trailing cell content isn't truncated."""
    if not spans:
        return [row.strip()]
    cells: list[str] = []
    for idx, (start, end) in enumerate(spans):
        if idx == len(spans) - 1:
            # Stretch the last cell to capture any trailing content.
            cell = row[start:] if start < len(row) else ''
        else:
            next_start = spans[idx + 1][0]
            cell = row[start:next_start] if start < len(row) else ''
        cells.append(cell.strip())
    return cells


def _emit_pipe_table(header: list[str], body_rows: list[list[str]]) -> list[str]:
    """Emit a GFM pipe table from a parsed header + body rows."""
    ncols = len(header)
    # Pad/truncate body rows to header column count.
    norm_rows: list[list[str]] = []
    for row in body_rows:
        if len(row) < ncols:
            row = row + [''] * (ncols - len(row))
        elif len(row) > ncols:
            row = row[:ncols - 1] + [' '.join(row[ncols - 1:]).strip()]
        norm_rows.append(row)

    out = ['| ' + ' | '.join(c if c else ' ' for c in header) + ' |',
           '| ' + ' | '.join(['---'] * ncols) + ' |']
    for row in norm_rows:
        out.append('| ' + ' | '.join(c if c else ' ' for c in row) + ' |')
    return out


def convert_simple_table_body(content: str) -> tuple[str, int]:
    """Convert RST simple-table bodies (===== =====) into GFM pipe tables.

    Detects blocks of the form:
        [optional `.. table::` directive line]
        [optional title/blank line(s)]
        ===== =====   <- top separator
        h1    h2
        ===== =====   <- header divider
        a     b
        c     d
        ===== =====   <- bottom separator

    Multi-line body rows (continuation lines indented past the first cell
    boundary, no blank line) are joined with a single space.

    Idempotent: existing pipe tables and fenced code blocks are left alone.
    Returns (new_content, count_of_tables_converted).
    """
    masked, saved = _mask_fenced_blocks(content)
    lines = masked.split('\n')
    out: list[str] = []
    converted = 0
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        m = SIMPLE_TABLE_SEP_RE.match(line)
        if not m:
            out.append(line)
            i += 1
            continue

        indent = m.group('indent')
        sep_top_stripped = line[len(indent):]
        spans = _column_spans(sep_top_stripped)
        if len(spans) < 2:
            out.append(line)
            i += 1
            continue

        # Walk forward to find the matching middle and bottom separators.
        # Layout: top, header lines (1+), middle, body lines (1+), bottom.
        j = i + 1
        header_lines: list[str] = []
        while j < n and not SIMPLE_TABLE_SEP_RE.match(lines[j]):
            header_lines.append(lines[j])
            j += 1
        if j >= n or not header_lines:
            out.append(line)
            i += 1
            continue
        # Middle separator must use the same column structure as top.
        middle_stripped = lines[j][len(indent):] if lines[j].startswith(indent) else lines[j].lstrip()
        if _column_spans(middle_stripped) != spans:
            out.append(line)
            i += 1
            continue

        k = j + 1
        body_lines: list[str] = []
        while k < n and not SIMPLE_TABLE_SEP_RE.match(lines[k]):
            body_lines.append(lines[k])
            k += 1
        if k >= n:
            # No closing separator — bail, keep original.
            out.append(line)
            i += 1
            continue
        bottom_stripped = lines[k][len(indent):] if lines[k].startswith(indent) else lines[k].lstrip()
        if _column_spans(bottom_stripped) != spans:
            out.append(line)
            i += 1
            continue

        # Strip the matching indent prefix from each row line so spans line up.
        def _strip_indent(s: str) -> str:
            if indent and s.startswith(indent):
                return s[len(indent):]
            return s

        header_stripped = [_strip_indent(l) for l in header_lines]
        body_stripped = [_strip_indent(l) for l in body_lines]

        # Header: join multi-line header lines per column with a space.
        header_cells_per_line = [_slice_row(l, spans) for l in header_stripped if l.strip()]
        if not header_cells_per_line:
            out.append(line)
            i += 1
            continue
        ncols = len(spans)
        header: list[str] = []
        for col in range(ncols):
            parts = [row[col] for row in header_cells_per_line if col < len(row) and row[col]]
            header.append(' '.join(parts).strip())

        # Body: each non-blank line is a new row. A line whose first column
        # is empty (i.e. starts with whitespace covering the first span) is
        # treated as a continuation of the previous row and joined with a
        # single space per column. Blank lines flush the current row.
        body_rows: list[list[str]] = []
        current: list[list[str]] = []

        def _flush() -> None:
            if not current:
                return
            merged = []
            for col in range(ncols):
                parts = [r[col] for r in current if col < len(r) and r[col]]
                merged.append(' '.join(parts).strip())
            body_rows.append(merged)
            current.clear()

        first_col_start = spans[0][0]
        first_col_end = spans[0][1]
        for bl in body_stripped:
            if not bl.strip():
                _flush()
                continue
            cells = _slice_row(bl, spans)
            # Continuation row if the first-column slice is empty/whitespace.
            first_slice = bl[first_col_start:first_col_end] if len(bl) > first_col_start else ''
            is_continuation = current and not first_slice.strip()
            if is_continuation:
                current.append(cells)
            else:
                _flush()
                current.append(cells)
        _flush()

        # Drop the directive/title that immediately precedes (within last 3
        # output lines) — title lines are noise once we have a pipe table.
        # Specifically: remove a trailing single-line block that looks like
        # a title (no special prefix) plus its trailing blank.
        # Be conservative: only strip a blank line if present.
        while out and out[-1].strip() == '':
            out.pop()

        # Emit the pipe table at the original indent.
        emitted = _emit_pipe_table(header, body_rows)
        if indent:
            emitted = [indent + l for l in emitted]
        # Insert a leading blank line for readability.
        if out and out[-1].strip() != '':
            out.append('')
        out.extend(emitted)
        out.append('')
        converted += 1
        i = k + 1

    new_content = '\n'.join(out)
    new_content = _unmask_fenced_blocks(new_content, saved)
    return new_content, converted


def dedent_raw_html_tables(content: str) -> tuple[str, int]:
    """Dedent indented `<table ...>` HTML blocks to top level.

    MkDocs (with `pymdownx.extra` / `md_in_html`) only renders raw HTML
    blocks when they start at column 0. Indented blocks (e.g. those that
    survived inside an RST literal context) render as `<pre>` instead.

    Conservative scope: only handles the small known cases like
    `<table class="messages">`. Detects an indented `<table` opener and
    a matching `</table>` closer at the same indent, then dedents every
    line in between by that indent.

    Idempotent: a block already at column 0 is skipped.
    """
    masked, saved = _mask_fenced_blocks(content)
    lines = masked.split('\n')
    out: list[str] = []
    dedented = 0
    i = 0
    n = len(lines)
    open_re = re.compile(r'^(?P<indent>[ \t]+)<table\b')
    while i < n:
        line = lines[i]
        m = open_re.match(line)
        if not m:
            out.append(line)
            i += 1
            continue
        indent = m.group('indent')
        # Find matching </table> at same indent (or any indent — be lenient).
        j = i
        end = -1
        while j < n:
            stripped = lines[j].lstrip()
            if stripped.startswith('</table>'):
                end = j
                break
            j += 1
        if end == -1:
            out.append(line)
            i += 1
            continue
        # Dedent the range [i, end]: strip the common indent prefix.
        for k in range(i, end + 1):
            l = lines[k]
            if l.startswith(indent):
                l = l[len(indent):]
            else:
                l = l.lstrip()
            out.append(l)
        dedented += 1
        i = end + 1

    new_content = '\n'.join(out)
    new_content = _unmask_fenced_blocks(new_content, saved)
    return new_content, dedented


def remove_standalone_header_markers(content: str) -> str:
    """Remove standalone #### lines (with optional whitespace)."""
    # Remove lines that are just `#### ` followed by optional whitespace
    content = re.sub(r'^#### \s*$\n', '', content, flags=re.MULTILINE)
    return content


def fix_table_row_prefixes(content: str) -> str:
    """Remove #### | prefixes and fix indentation on table rows."""
    # Replace `#### |` at start of lines with just `|`
    content = re.sub(r'^#### \|', '|', content, flags=re.MULTILINE)
    # Replace leading whitespace before `|` at start of lines
    content = re.sub(r'^\s+\|', '|', content, flags=re.MULTILINE)
    return content


def remove_empty_lines_in_tables(content: str) -> str:
    """Remove blank lines between table rows.

    Tables should have contiguous rows without blank lines between them.
    """
    lines = content.split('\n')
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check if we're at a table row
        if line.strip().startswith('|') and line.strip().endswith('|'):
            result.append(line)
            i += 1

            # Skip empty lines until we hit another table row or non-table content
            while i < len(lines):
                next_line = lines[i]
                if next_line.strip() == '':
                    # Check if line after empty line is still a table row
                    if i + 1 < len(lines) and lines[i + 1].strip().startswith('|'):
                        # Skip this empty line
                        i += 1
                    else:
                        # Keep the empty line (end of table)
                        result.append(next_line)
                        i += 1
                        break
                elif next_line.strip().startswith('|'):
                    # Another table row, add it
                    result.append(next_line)
                    i += 1
                else:
                    # Non-table content
                    result.append(next_line)
                    i += 1
                    break
        else:
            result.append(line)
            i += 1

    return '\n'.join(result)


def is_table_row(line: str) -> bool:
    """Check if a line is a table row (starts and ends with |)."""
    stripped = line.strip()
    return stripped.startswith('|') and stripped.endswith('|')


def is_separator_row(line: str) -> bool:
    """Check if a line is a table separator row (only |, -, :, spaces)."""
    stripped = line.strip()
    return (stripped.startswith('|') and
            stripped.endswith('|') and
            all(c in '|-: ' for c in stripped) and
            '-' in stripped)


def count_columns(line: str) -> int:
    """Count the number of columns in a table row."""
    # Count pipes, subtract 2 for outer pipes
    return line.count('|') - 1


def create_separator_row(num_cols: int) -> str:
    """Create a separator row with the given number of columns."""
    return '|' + '|'.join(['---'] * num_cols) + '|'


def add_separator_rows(content: str) -> str:
    """Add separator rows after table headers that are missing them.

    Markdown tables require:
        | Header | Header |
        |--------|--------|
        | Cell   | Cell   |

    This function detects table starts (first row after non-table content)
    and adds separator rows if missing.
    """
    lines = content.split('\n')
    result = []
    i = 0
    in_table = False
    added_separators = 0

    while i < len(lines):
        line = lines[i]

        if is_table_row(line):
            if not in_table:
                # This is the start of a new table (header row)
                in_table = True
                result.append(line)

                # Check if next line is already a separator
                if i + 1 < len(lines) and is_separator_row(lines[i + 1]):
                    # Already has separator, continue
                    pass
                else:
                    # Need to add separator row
                    num_cols = count_columns(line)
                    if num_cols > 0:
                        result.append(create_separator_row(num_cols))
                        added_separators += 1
            else:
                # Continuation of existing table
                result.append(line)
        else:
            # Non-table content
            in_table = False
            result.append(line)

        i += 1

    return '\n'.join(result)


def count_tables_missing_separators(content: str) -> int:
    """Count tables that are missing separator rows."""
    lines = content.split('\n')
    count = 0
    in_table = False

    for i, line in enumerate(lines):
        if is_table_row(line):
            if not in_table:
                # Start of a new table
                in_table = True
                # Check if next line is a separator
                if i + 1 < len(lines) and not is_separator_row(lines[i + 1]):
                    count += 1
        else:
            in_table = False

    return count


def fix_file(filepath: Path, dry_run: bool = False) -> tuple[bool, int]:
    """Fix malformed tables in a single file.

    Returns:
        (changed, count): Whether file was changed and number of fixes applied
    """
    content = filepath.read_text(encoding='utf-8')
    original = content

    # Count issues before fixing
    issues = 0
    issues += len(re.findall(r'^#### \|', content, re.MULTILINE))
    issues += len(re.findall(r'^\.\. table::', content, re.MULTILINE))
    issues += len(re.findall(r'^\s+:(class|widths):', content, re.MULTILINE))
    issues += len(re.findall(r'^#### \s*$', content, re.MULTILINE))
    issues += len(SIMPLE_TABLE_SEP_RE.findall(content))

    # Apply fixes in order
    content = remove_rst_table_directives(content)
    # Convert leaked simple-table bodies (must run after directive removal so
    # the body is no longer hidden behind `.. table::`).
    content, simple_converted = convert_simple_table_body(content)
    issues += simple_converted
    # Dedent raw <table> HTML blocks so MkDocs renders them as HTML.
    content, html_dedented = dedent_raw_html_tables(content)
    issues += html_dedented

    content = remove_standalone_header_markers(content)
    content = fix_table_row_prefixes(content)
    content = remove_empty_lines_in_tables(content)

    # Count missing separators after cleanup
    missing_separators = count_tables_missing_separators(content)
    issues += missing_separators

    # Add separator rows
    content = add_separator_rows(content)

    changed = content != original

    if changed and not dry_run:
        filepath.write_text(content, encoding='utf-8')

    return changed, issues


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Fix malformed Markdown tables')
    parser.add_argument('path', nargs='?', default='.',
                       help='Path to docs directory or specific file')
    parser.add_argument('--dry-run', '-n', action='store_true',
                       help='Show what would be changed without modifying files')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show detailed output')
    parser.add_argument('--report-tables', action='store_true',
                       help='Report simple-table conversion + HTML dedent counts per file')

    args = parser.parse_args()

    path = Path(args.path)

    if path.is_file():
        files = [path]
    else:
        files = list(path.rglob('*.md'))

    total_changed = 0
    total_issues = 0

    if args.report_tables:
        report_total_tables = 0
        report_total_html = 0
        for filepath in sorted(files):
            text = filepath.read_text(encoding='utf-8')
            text2 = remove_rst_table_directives(text)
            _, n_tables = convert_simple_table_body(text2)
            _, n_html = dedent_raw_html_tables(text2)
            if n_tables or n_html:
                print(f"{filepath}: {n_tables} simple tables, {n_html} HTML blocks")
                report_total_tables += n_tables
                report_total_html += n_html
        print(f"\nTotal: {report_total_tables} simple tables, {report_total_html} HTML blocks "
              f"would be normalised")
        return 0

    for filepath in sorted(files):
        changed, issues = fix_file(filepath, dry_run=args.dry_run)

        if changed or (args.verbose and issues > 0):
            status = '[DRY RUN] ' if args.dry_run else ''
            action = 'Would fix' if args.dry_run else 'Fixed'
            if changed:
                print(f"{status}{action} {issues} issues in {filepath}")
                total_changed += 1
                total_issues += issues
            elif args.verbose:
                print(f"No changes needed: {filepath}")

    print(f"\n{'Would modify' if args.dry_run else 'Modified'} {total_changed} files, "
          f"fixed {total_issues} issues")

    return 0 if total_changed > 0 or not args.dry_run else 1


if __name__ == '__main__':
    sys.exit(main())
