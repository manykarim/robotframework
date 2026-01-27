#!/usr/bin/env python3
"""Fix malformed Markdown tables converted from RST.

This script fixes tables that have:
- `#### |` prefixes corrupting table rows
- `   |` indented rows
- `.. table::` RST directives
- `:class:` and `:widths:` RST options
- Standalone `####` lines
- Missing separator rows after headers
"""
import re
import sys
from pathlib import Path


def remove_rst_table_directives(content: str) -> str:
    """Convert RST table directives to markdown headers or remove them."""
    # Convert `.. table:: Title` to nothing (title not needed, context clear)
    content = re.sub(r'^\.\. table::.*$\n', '', content, flags=re.MULTILINE)
    # Remove :class: and :widths: lines
    content = re.sub(r'^\s+:(class|widths):.*$\n', '', content, flags=re.MULTILINE)
    return content


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

    # Apply fixes in order
    content = remove_rst_table_directives(content)
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

    args = parser.parse_args()

    path = Path(args.path)

    if path.is_file():
        files = [path]
    else:
        files = list(path.rglob('*.md'))

    total_changed = 0
    total_issues = 0

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
