#!/usr/bin/env python3
"""
Convert remaining RST syntax to proper Markdown.

This script fixes RST syntax remnants in the Robot Framework User Guide
Markdown files, including:
- RST labels (.. _label:) -> HTML anchors
- RST link definitions (.. _name: url) -> Markdown reference links
- Anonymous link targets (__ url) -> inline links
- .. raw:: html directives -> plain HTML
- .. table:: directives -> remove directive, keep content
- .. list-table: directives -> convert to proper Markdown tables
- Double-colon code markers (::) -> already handled or remove
"""

import re
import sys
from pathlib import Path
from typing import Tuple


DOCS_DIR = Path(__file__).parent.parent / "docs"


# Known RST role names handled by this pipeline. Restricted set so that URL
# schemes (http:, mailto:) are never mistaken for roles.
ROLE_NAMES = ('setting', 'name', 'option', 'file', 'codesc', 'opt')

# Prefix form: :role:`text` (text may span lines). DOTALL so newlines match.
PREFIX_ROLE_PATTERN = re.compile(
    r':(' + '|'.join(ROLE_NAMES) + r'):`([^`\n]+(?:\n[^`\n]+)?)`',
    re.DOTALL,
)

# Postfix form: `text`:role: (text may span lines). DOTALL.
POSTFIX_ROLE_PATTERN = re.compile(
    r'`([^`\n]+(?:\n[^`\n]+)?)`:(' + '|'.join(ROLE_NAMES) + r'):',
    re.DOTALL,
)


def _mask_fenced_blocks_for_roles(text: str) -> str:
    """Mask fenced-block content with spaces of the same length, preserving
    byte offsets so regex match indices on the masked string remain valid
    against the original content. Honours CommonMark closer rules.
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
        if (in_fence and not opening_now) or closing_now:
            out.append(' ' * len(line))
        else:
            out.append(line)
    return '\n'.join(out)


def strip_postfix_roles(content: str) -> str:
    """Convert `text`:role: -> `text` outside fenced blocks.

    Operates by splice: scan masked text for matches, substitute on the
    matching slice in the original content. Idempotent (no role left after).
    """
    masked = _mask_fenced_blocks_for_roles(content)
    result = []
    last = 0
    for m in POSTFIX_ROLE_PATTERN.finditer(masked):
        start, end = m.start(), m.end()
        result.append(content[last:start])
        text = m.group(1)
        # Collapse internal newlines/whitespace in the captured backtick text.
        normalized = ' '.join(text.split())
        result.append(f'`{normalized}`')
        last = end
    result.append(content[last:])
    return ''.join(result)


def convert_rst_labels(content: str) -> str:
    """
    Convert RST label definitions to HTML anchors.

    .. _varargs-library:  ->  <a id="varargs-library"></a>
    .. _`Getting dynamic keyword names`:  ->  <a id="Getting dynamic keyword names"></a>
    """
    # Handle backtick-quoted labels: .. _`label name`:
    content = re.sub(
        r'^\.\.[ \t]+_`([^`]+)`:\s*$',
        r'<a id="\1"></a>',
        content,
        flags=re.MULTILINE
    )
    # Handle simple labels: .. _label-name:
    content = re.sub(
        r'^\.\.[ \t]+_([^:\s][^:]*?):\s*$',
        r'<a id="\1"></a>',
        content,
        flags=re.MULTILINE
    )
    return content


def convert_link_definitions(content: str) -> str:
    """
    Convert RST link definitions to Markdown reference links.

    .. _Union: https://docs.python.org/...  ->  [Union]: https://docs.python.org/...
    .. _ISO 8601: https://...  ->  [ISO 8601]: https://...
    """
    # Handle: .. _name: url
    content = re.sub(
        r'^\.\.[ \t]+_([^:]+):\s+(https?://\S+)\s*$',
        r'[\1]: \2',
        content,
        flags=re.MULTILINE
    )
    return content


def convert_anonymous_links(content: str, filename: str) -> Tuple[str, list]:
    """
    Convert anonymous link targets and references to proper Markdown.

    RST anonymous references use:
    - `text`__ as the reference
    - __ url or __ anchor_ as the target

    Returns: (converted_content, list_of_warnings)
    """
    warnings = []
    lines = content.split('\n')

    # First pass: collect anonymous targets and their line numbers
    anon_targets = []
    target_lines = set()
    for i, line in enumerate(lines):
        # Match: __ http://... or __ anchor_ or __ [text](#anchor)
        match = re.match(r'^__\s+(.+?)\s*$', line)
        if match:
            target = match.group(1)
            anon_targets.append((i, target))
            target_lines.add(i)

    # Build URL queue from anonymous targets
    url_queue = []
    for _, target in anon_targets:
        # Convert RST anchor reference (anchor_) to Markdown (#anchor)
        if target.endswith('_') and not target.startswith('http'):
            anchor = target[:-1].lower().replace(' ', '-')
            url_queue.append(f'#{anchor}')
        # Already a markdown link
        elif target.startswith('[') and '](#' in target:
            # Extract just the URL part
            url_match = re.search(r'\(([^)]+)\)', target)
            if url_match:
                url_queue.append(url_match.group(1))
            else:
                url_queue.append(target)
        # Plain URL
        elif target.startswith('http'):
            url_queue.append(target)
        else:
            # Other internal reference, convert to anchor
            anchor = target.lower().replace(' ', '-')
            url_queue.append(f'#{anchor}')

    url_index = 0
    result = []

    for i, line in enumerate(lines):
        # Skip target lines
        if i in target_lines:
            continue

        # Find anonymous references: `text`__
        def replace_anon_ref(match):
            nonlocal url_index
            text = match.group(1)
            if url_index < len(url_queue):
                url = url_queue[url_index]
                url_index += 1
                return f'[{text}]({url})'
            else:
                # No URL available - convert to an anchor reference based on text
                anchor = text.lower().replace(' ', '-')
                return f'[{text}](#{anchor})'

        # Replace `text`__ patterns
        line = re.sub(r'`([^`]+)`__', replace_anon_ref, line)
        result.append(line)

    return '\n'.join(result), warnings


def remove_raw_html_directive(content: str) -> str:
    """
    Remove .. raw:: html directive, keeping the HTML content.

    .. raw:: html

       <table>...</table>

    becomes just:

    <table>...</table>
    """
    # Pattern: .. raw:: html followed by blank line and indented content
    pattern = r'^\.\.\s+raw::\s*html\s*\n\s*\n'
    content = re.sub(pattern, '\n', content, flags=re.MULTILINE)
    return content


def remove_table_directive(content: str) -> str:
    """
    Remove .. table:: directive line and its options, keeping table content.

    .. table:: Title
       :class: tabular
       :widths: 5 5 5

    becomes nothing (the actual table content follows)
    """
    # Remove the directive line
    content = re.sub(
        r'^\.\.\s+table::[^\n]*\n',
        '',
        content,
        flags=re.MULTILINE
    )
    # Remove directive options (lines starting with :option:)
    content = re.sub(
        r'^[ \t]+:[a-zA-Z_-]+:[^\n]*\n',
        '',
        content,
        flags=re.MULTILINE
    )
    return content


def convert_list_table(content: str) -> str:
    """
    Convert RST list-table format to proper Markdown tables.

    This handles the specific format found in translations.md where
    list-tables are partially converted but still have RST artifacts.
    """
    lines = content.split('\n')
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check for list-table directive
        if re.match(r'^\.\.\s+list-table:', line):
            # Skip the directive line
            i += 1
            # Skip blank line if present
            if i < len(lines) and lines[i].strip() == '':
                i += 1
            # Skip code fence if present (malformed conversion)
            if i < len(lines) and lines[i].strip() == '```':
                i += 1
            # Skip directive options (:class:, :width:, :widths:, :header-rows:)
            while i < len(lines) and re.match(r'^:[a-zA-Z_-]+:', lines[i].strip()):
                i += 1
            # Skip blank line after options
            if i < len(lines) and lines[i].strip() == '':
                i += 1

            # Now collect the table data
            table_rows = []
            current_row = []

            while i < len(lines):
                line = lines[i]
                stripped = line.strip()

                # End of table: closing code fence or blank line followed by non-list content
                if stripped == '```':
                    i += 1
                    break
                if stripped == '' and i + 1 < len(lines) and not lines[i+1].strip().startswith(('*', '-', ' ')):
                    break

                # New row starts with * -
                if re.match(r'^\* - ', stripped):
                    if current_row:
                        table_rows.append(current_row)
                    current_row = [stripped[4:]]  # Remove "* - "
                # Continuation of row with  -
                elif re.match(r'^  - ', stripped):
                    current_row.append(stripped[4:])  # Remove "  - "
                # Empty line within table
                elif stripped == '':
                    pass

                i += 1

            # Add last row
            if current_row:
                table_rows.append(current_row)

            # Convert to Markdown table
            if table_rows:
                # Determine number of columns
                num_cols = max(len(row) for row in table_rows)

                # Build markdown table
                for row_idx, row in enumerate(table_rows):
                    # Pad row to have correct number of columns
                    while len(row) < num_cols:
                        row.append('')
                    result.append('| ' + ' | '.join(row) + ' |')
                    # Add header separator after first row
                    if row_idx == 0:
                        result.append('|' + '|'.join(['---'] * num_cols) + '|')

                result.append('')
            continue

        result.append(line)
        i += 1

    return '\n'.join(result)


def remove_generated_comments(content: str) -> str:
    """Remove/convert RST-style generated content comments."""
    content = re.sub(
        r'^\.\.\s+START GENERATED CONTENT\s*$',
        '<!-- START GENERATED CONTENT -->',
        content,
        flags=re.MULTILINE
    )
    content = re.sub(
        r'^\.\.\s+END GENERATED CONTENT\s*$',
        '<!-- END GENERATED CONTENT -->',
        content,
        flags=re.MULTILINE
    )
    content = re.sub(
        r'^\.\.\s+Generated by[^\n]*$',
        '',
        content,
        flags=re.MULTILINE
    )
    return content


def convert_rst_note_directive(content: str) -> str:
    """
    Convert RST Note:: directive to Markdown admonition.

    .. Note:: text  ->  !!! note
                           text
    """
    # Handle inline note: .. Note:: text
    def replace_note(match):
        text = match.group(1).strip()
        return f'!!! note\n    {text}'

    content = re.sub(
        r'^\.\.\s+[Nn]ote::\s*(.+)$',
        replace_note,
        content,
        flags=re.MULTILINE
    )
    return content


def fix_malformed_table_headers(content: str) -> str:
    """
    Fix malformed table headers that appear as #### patterns.

    These are artifacts from poor RST-to-MD conversion of complex tables.
    """
    # Remove standalone #### lines that aren't real headers
    content = re.sub(r'^####\s*$', '', content, flags=re.MULTILINE)
    # Remove #### | patterns (malformed table row markers)
    content = re.sub(r'^####\s+\|', '|', content, flags=re.MULTILINE)
    return content


def cleanup_empty_lines(content: str) -> str:
    """Remove excessive blank lines (more than 2 consecutive)."""
    return re.sub(r'\n{4,}', '\n\n\n', content)


def process_file(filepath: Path, dry_run: bool = False) -> Tuple[int, list]:
    """
    Process a single Markdown file to fix RST syntax.

    Returns: (number_of_changes, list_of_warnings)
    """
    original_content = filepath.read_text(encoding='utf-8')
    content = original_content
    warnings = []

    # Fix multi-line RST roles first (these span line breaks)
    # :name:`Copy\nFile` → *Copy File*
    # :setting:`Test\nTeardown` → `Test Teardown`
    for role, (prefix, suffix) in [('name', ('*', '*')), ('setting', ('`', '`')),
                                     ('option', ('`', '`')), ('file', ('*', '*')),
                                     ('codesc', ('`', '`')), ('opt', ('`', '`'))]:
        content = re.sub(
            rf':{role}:`([^`]+(?:\n[^`]+)?)`',
            lambda m, p=prefix, s=suffix: f'{p}{" ".join(m.group(1).split())}{s}',
            content,
            flags=re.DOTALL
        )

    # Postfix-form roles: `text`:role: → `text` (outside fenced blocks).
    content = strip_postfix_roles(content)

    # Apply conversions in order
    content = convert_rst_labels(content)
    content = convert_link_definitions(content)
    content, anon_warnings = convert_anonymous_links(content, filepath.name)
    warnings.extend(anon_warnings)
    content = remove_raw_html_directive(content)
    content = remove_table_directive(content)
    content = convert_list_table(content)
    content = remove_generated_comments(content)
    content = convert_rst_note_directive(content)
    content = fix_malformed_table_headers(content)
    content = cleanup_empty_lines(content)

    # Count changes (rough estimate based on diff)
    changes = sum(1 for a, b in zip(original_content.split('\n'), content.split('\n')) if a != b)
    changes += abs(len(original_content.split('\n')) - len(content.split('\n')))

    if not dry_run and content != original_content:
        filepath.write_text(content, encoding='utf-8')

    return changes, warnings


def count_rst_artifacts(content: str) -> dict:
    """Count remaining RST artifacts in content."""
    counts = {
        'labels': len(re.findall(r'^\.\.[ \t]+_', content, re.MULTILINE)),
        'link_defs': len(re.findall(r'^\.\.[ \t]+_[^:]+:\s+https?://', content, re.MULTILINE)),
        'raw_html': len(re.findall(r'^\.\.\s+raw::', content, re.MULTILINE)),
        'tables': len(re.findall(r'^\.\.\s+table::', content, re.MULTILINE)),
        'list_tables': len(re.findall(r'^\.\.\s+list-table:', content, re.MULTILINE)),
        'anon_links': len(re.findall(r'^__\s+\S', content, re.MULTILINE)),
        'other': len(re.findall(r'^\.\.[ \t]+[^_]', content, re.MULTILINE)),
    }
    counts['total'] = sum(counts.values())
    return counts


def main():
    """Main function to process all Markdown files."""
    import argparse

    parser = argparse.ArgumentParser(description='Fix RST syntax in Markdown files')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without applying them')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed output')
    parser.add_argument('--file', type=str, help='Process only this file')
    parser.add_argument('--count-only', action='store_true', help='Only count RST artifacts')
    args = parser.parse_args()

    if args.file:
        filepath = Path(args.file)
        if not filepath.is_absolute():
            filepath = Path.cwd() / filepath
        files = [filepath]
    else:
        files = list(DOCS_DIR.rglob('*.md'))

    if args.count_only:
        total_counts = {
            'labels': 0, 'link_defs': 0, 'raw_html': 0,
            'tables': 0, 'list_tables': 0, 'anon_links': 0, 'other': 0, 'total': 0
        }
        for filepath in files:
            content = filepath.read_text(encoding='utf-8')
            counts = count_rst_artifacts(content)
            if counts['total'] > 0:
                print(f"{filepath.relative_to(DOCS_DIR)}: {counts['total']} artifacts")
                if args.verbose:
                    for key, val in counts.items():
                        if val > 0 and key != 'total':
                            print(f"  - {key}: {val}")
            for key in total_counts:
                total_counts[key] += counts[key]

        print(f"\nTotal RST artifacts: {total_counts['total']}")
        for key, val in total_counts.items():
            if val > 0 and key != 'total':
                print(f"  - {key}: {val}")
        return

    total_changes = 0
    all_warnings = []

    print(f"Processing {len(files)} Markdown files...")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'APPLYING CHANGES'}")
    print()

    for filepath in sorted(files):
        changes, warnings = process_file(filepath, dry_run=args.dry_run)
        if changes > 0 or warnings:
            rel_path = filepath.relative_to(DOCS_DIR)
            print(f"{rel_path}: {changes} changes")
            if args.verbose:
                for warn in warnings:
                    print(f"  WARNING: {warn}")
            total_changes += changes
            all_warnings.extend([(filepath.name, w) for w in warnings])

    print()
    print(f"Total changes: {total_changes}")
    if all_warnings:
        print(f"Total warnings: {len(all_warnings)}")

    if args.dry_run:
        print("\nNo changes applied (dry run mode)")


if __name__ == '__main__':
    main()
