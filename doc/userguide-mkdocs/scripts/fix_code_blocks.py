#!/usr/bin/env python3
"""Fix code blocks that were broken during documentation conversion.

The main issue is empty code blocks followed by orphaned code:
```python
```

  from example import Connection
  ...

```python
...
```

This script finds these patterns and fixes them by merging the orphaned code
into the empty block.
"""
import re
from pathlib import Path
from typing import List, Tuple
import sys


def find_empty_blocks(content: str) -> List[Tuple[int, int, str]]:
    """Find empty code blocks (opening fence immediately followed by closing fence).

    Returns list of (start_pos, end_pos, language) tuples.
    """
    # Pattern: ```lang\n``` (with optional whitespace)
    pattern = r'(```(\w+)\n)(```)'
    matches = []
    for m in re.finditer(pattern, content):
        matches.append((m.start(), m.end(), m.group(2)))
    return matches


def find_orphaned_code_after(content: str, pos: int) -> Tuple[int, int, str]:
    """Find orphaned code block after an empty block.

    Starting from pos, skip blank lines only, then capture code until we hit:
    - A matching ```lang block
    - Two or more blank lines followed by text (paragraph break)
    - A header (# or ##)
    """
    # Skip blank lines only (keep indentation of first code line)
    i = pos
    while i < len(content) and content[i] == '\n':
        i += 1

    if i >= len(content):
        return -1, -1, ""

    # Find the start of the first line (including any leading spaces)
    code_start = i

    # Look for end of orphaned code - split from code_start
    remaining = content[code_start:]
    lines = remaining.split('\n')
    code_lines = []

    for j, line in enumerate(lines):
        # Check if this is a closing fence for another block or a new block opening
        if line.strip().startswith('```'):
            # This is either the start of another code block or a closing fence
            # Either way, this is where orphaned code ends
            break

        # Check for paragraph break (blank line followed by non-indented text)
        if j > 0 and not line.strip() and j + 1 < len(lines):
            next_line = lines[j + 1]
            # If next line starts at column 0 (not indented), this might be end of code
            if next_line and not next_line[0].isspace() and not next_line.startswith('```'):
                # Check if it looks like prose vs code
                if not any(next_line.startswith(kw) for kw in ['def ', 'class ', 'import ', 'from ', '#', '***']):
                    break

        code_lines.append(line)

    # Strip trailing empty lines from code
    while code_lines and not code_lines[-1].strip():
        code_lines.pop()

    if not code_lines:
        return -1, -1, ""

    # Calculate end position
    code_end = code_start + sum(len(l) + 1 for l in code_lines) - 1  # -1 for last newline

    return code_start, code_end, '\n'.join(code_lines)


def fix_empty_blocks(content: str, verbose: bool = False) -> Tuple[str, int]:
    """Fix empty code blocks by merging orphaned code into them.

    Returns (fixed_content, count_of_fixes).
    """
    fixes = 0
    result = content

    # Process from end to start to preserve positions
    empty_blocks = find_empty_blocks(result)
    empty_blocks.reverse()  # Process from end to preserve positions

    for block_start, block_end, lang in empty_blocks:
        # Find orphaned code after this empty block
        code_start, code_end, orphaned_code = find_orphaned_code_after(result, block_end)

        if code_start > 0 and orphaned_code.strip():
            # We found orphaned code - merge it into the empty block

            # Remove leading indentation (normalize to no indent)
            lines = orphaned_code.split('\n')
            if lines:
                # Find minimum indentation
                min_indent = float('inf')
                for line in lines:
                    if line.strip():
                        indent = len(line) - len(line.lstrip())
                        min_indent = min(min_indent, indent)

                if min_indent != float('inf') and min_indent > 0:
                    lines = [line[min_indent:] if len(line) >= min_indent else line for line in lines]
                    orphaned_code = '\n'.join(lines)

            # Build the new block
            new_block = f"```{lang}\n{orphaned_code}\n```"

            # Replace: empty block + whitespace + orphaned code
            # Need to include whitespace between empty block and orphaned code
            to_replace = result[block_start:code_end + 1] if code_end + 1 <= len(result) else result[block_start:]

            if verbose:
                print(f"  Fixing empty {lang} block at position {block_start}")
                print(f"    Orphaned code: {orphaned_code[:50]}...")

            result = result[:block_start] + new_block + result[code_end + 1:]
            fixes += 1

    return result, fixes


def process_file(filepath: Path, dry_run: bool = False, verbose: bool = False) -> int:
    """Process a single file and fix code blocks.

    Returns number of fixes applied.
    """
    content = filepath.read_text(encoding='utf-8')
    fixed_content, fixes = fix_empty_blocks(content, verbose)

    if fixes > 0:
        if not dry_run:
            filepath.write_text(fixed_content, encoding='utf-8')
        if verbose:
            print(f"  Applied {fixes} fixes to {filepath.name}")

    return fixes


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Fix broken code blocks in Markdown files')
    parser.add_argument('path', nargs='?', default='/home/many/workspace/robotframework/doc/userguide-mkdocs/docs',
                        help='Path to docs directory or single file')
    parser.add_argument('--dry-run', '-n', action='store_true',
                        help='Show what would be fixed without making changes')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show detailed information about fixes')
    parser.add_argument('--file', '-f', type=str,
                        help='Process only the specified file')

    args = parser.parse_args()

    path = Path(args.path)

    if args.file:
        files = [Path(args.file)]
    elif path.is_file():
        files = [path]
    else:
        files = sorted(path.rglob('*.md'))

    total_fixes = 0
    files_fixed = 0

    print(f"Processing {len(files)} Markdown files...")
    if args.dry_run:
        print("(Dry run - no changes will be made)")
    print()

    for filepath in files:
        if args.verbose:
            print(f"Processing: {filepath.name}")

        fixes = process_file(filepath, dry_run=args.dry_run, verbose=args.verbose)

        if fixes > 0:
            total_fixes += fixes
            files_fixed += 1
            if not args.verbose:
                print(f"  {filepath.name}: {fixes} fixes")

    print()
    print(f"Total: {total_fixes} fixes in {files_fixed} files")

    return 0 if total_fixes == 0 or not args.dry_run else 1


if __name__ == '__main__':
    sys.exit(main())
