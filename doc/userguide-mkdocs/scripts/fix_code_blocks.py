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
    - A new fenced block (``` opener/closer)
    - Dedented prose (a non-indented line that doesn't look like code) after
      one or more blank lines

    Relaxations vs. the original implementation:
    - Indent threshold for "this is still code" lowered from 3 to 2 spaces
      (RF user guide uses 2-space indent throughout).
    - Blank lines no longer terminate the block on their own; we only stop
      when a *dedented prose-looking line* follows.
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

    # The first non-blank line establishes the base indent for this block.
    base_indent = -1
    for line in lines:
        if line.strip():
            base_indent = len(line) - len(line.lstrip())
            break
    if base_indent < 0:
        return -1, -1, ""

    # Code-continuation indent threshold: RF guide uses 2-space indents.
    cont_indent = max(2, base_indent)

    # Prose markers: lines that look like Markdown prose, headings, lists, or
    # admonitions and clearly belong outside the code block.
    def _looks_like_prose(line: str) -> bool:
        s = line.lstrip()
        if not s:
            return False
        # Headings, lists, admonitions, blockquotes, def-list markers, tables.
        if s.startswith(('#', '- ', '* ', '> ', '!!! ', '??? ', ': ', '|')):
            return True
        # Ordered list "1. " etc.
        if re.match(r'^\d+\.\s', s):
            return True
        return False

    code_lines: list[str] = []
    j = 0
    while j < len(lines):
        line = lines[j]
        stripped = line.strip()

        # New fence — orphaned code terminates here.
        if stripped.startswith('```'):
            break

        # Walk over blank lines: only terminate on dedented prose.
        if not stripped:
            # Look ahead past consecutive blank lines.
            k = j + 1
            while k < len(lines) and not lines[k].strip():
                k += 1
            if k >= len(lines):
                # File ends in blanks — drop the trailing blanks from code.
                break
            next_line = lines[k]
            next_indent = len(next_line) - len(next_line.lstrip())
            if next_line.strip().startswith('```'):
                break
            # Indented continuation (>= cont_indent) → stay in code.
            if next_indent >= cont_indent:
                # Keep the blank line(s) — they're part of the code block.
                code_lines.extend(lines[j:k])
                j = k
                continue
            # Dedented but doesn't look like prose? Common case is a continuation
            # at base column 0 of code (shouldn't happen for RF), or a comment
            # like "# something". Keep walking only if it clearly looks like code.
            if _looks_like_prose(next_line):
                break
            # Conservatively stop on any dedent below cont_indent.
            break

        # Non-blank line.
        line_indent = len(line) - len(line.lstrip())
        if line_indent < cont_indent:
            # Dedented inline. If it's a fence or prose, terminate.
            if stripped.startswith('```') or _looks_like_prose(line):
                break
            # Otherwise terminate too — we've left the literal-block region.
            break

        code_lines.append(line)
        j += 1

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


def fix_headings_inside_code_blocks(content: str, verbose: bool = False) -> Tuple[str, int]:
    """Fix markdown headings that appear inside fenced code blocks.

    The converter sometimes includes a heading inside a code block:
        ```python
        def example():
            pass

        ## Next Section
        ```

    This should be:
        ```python
        def example():
            pass
        ```

        ## Next Section

    Uses CommonMark-aware fence tracking (info string = opener, bare = closer).
    """
    lines = content.split('\n')
    fixes = 0
    result = []
    in_code = False
    open_backticks = 0

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.rstrip()

        # Track code fence state (CommonMark rules)
        m = re.match(r'^(`{3,})(.*)', stripped)
        if m:
            backticks = len(m.group(1))
            info = m.group(2).strip()
            if not in_code:
                in_code = True
                open_backticks = backticks
                result.append(line)
                i += 1
                continue
            else:
                if backticks >= open_backticks and not info:
                    in_code = False
                    result.append(line)
                    i += 1
                    continue

        # If inside a code block and we see a markdown heading (## or higher).
        # Single # is skipped because it's ambiguous with code comments.
        if in_code and re.match(r'^#{2,6}\s+\S', stripped):
            # Close the code block before the heading
            # Remove trailing blank lines from the code block
            while result and not result[-1].strip():
                result.pop()
            result.append('```')
            result.append('')
            result.append(line)  # The heading
            in_code = False
            fixes += 1
            if verbose:
                print(f"  Split code block at heading: {stripped[:60]}")

            # Check if the next line is a stray closing fence
            if i + 1 < len(lines) and re.match(r'^`{3,}\s*$', lines[i + 1].rstrip()):
                # Skip the orphaned closing fence
                i += 2
                continue
            i += 1
            continue

        result.append(line)
        i += 1

    return '\n'.join(result), fixes


_FENCE_RE = re.compile(r'^[ \t]*`{3,}.*$')


def _scan_fence_ranges(lines: List[str]) -> List[Tuple[int, int]]:
    """Return list of (start, end_inclusive) line indices that lie inside
    fenced code blocks. CommonMark-aware (info string opens, bare closes)."""
    ranges: List[Tuple[int, int]] = []
    in_fence = False
    open_ticks = 0
    start = -1
    for i, line in enumerate(lines):
        m = re.match(r'^[ \t]*(`{3,})(.*)$', line)
        if not m:
            continue
        ticks = len(m.group(1))
        info = m.group(2).strip()
        if not in_fence:
            in_fence = True
            open_ticks = ticks
            start = i
        else:
            if ticks >= open_ticks and not info:
                ranges.append((start, i))
                in_fence = False
                open_ticks = 0
                start = -1
    if in_fence and start >= 0:
        ranges.append((start, len(lines) - 1))
    return ranges


def _line_in_ranges(idx: int, ranges: List[Tuple[int, int]]) -> bool:
    for a, b in ranges:
        if a <= idx <= b:
            return True
    return False


def fix_lone_colon_lines(content: str, verbose: bool = False) -> Tuple[str, int]:
    """Convert RST literal-block markers that survived as lone `:` / `::` lines.

    Two cases handled (both outside fenced code blocks):

    1. Standalone bare `:` or `::` on its own line, followed (after one or
       more blank lines) by an indented block. The marker line is dropped
       and the indented block is wrapped in a fence.

    2. A paragraph ending with `::` followed by a blank line and an
       indented block. The trailing `::` is reduced to a single `:` (RST
       convention) and the indented block is fenced.

    Idempotent: existing fenced blocks are skipped via mask.
    """
    lines = content.split('\n')
    fence_ranges = _scan_fence_ranges(lines)
    out: List[str] = []
    fixes = 0
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        if _line_in_ranges(i, fence_ranges):
            out.append(line)
            i += 1
            continue

        stripped = line.strip()
        is_bare_colon = stripped in (':', '::')
        is_paragraph_colon = (
            stripped.endswith('::')
            and not stripped.startswith('::')
            and len(stripped) > 2
            and not stripped.endswith(':::')
        )

        if not (is_bare_colon or is_paragraph_colon):
            out.append(line)
            i += 1
            continue

        # Look ahead: blank line(s), then indented content.
        k = i + 1
        while k < n and not lines[k].strip():
            k += 1
        if k >= n or _line_in_ranges(k, fence_ranges):
            out.append(line)
            i += 1
            continue
        first = lines[k]
        first_indent = len(first) - len(first.lstrip())
        if first_indent < 2:
            out.append(line)
            i += 1
            continue

        # Capture the indented block (>= 2 spaces; allow internal blanks).
        block: List[str] = []
        j = k
        while j < n:
            l = lines[j]
            if not l.strip():
                # Peek past blanks.
                m = j + 1
                while m < n and not lines[m].strip():
                    m += 1
                if m >= n:
                    break
                if _line_in_ranges(m, fence_ranges):
                    break
                m_indent = len(lines[m]) - len(lines[m].lstrip())
                if m_indent < 2:
                    break
                block.extend(lines[j:m])
                j = m
                continue
            l_indent = len(l) - len(l.lstrip())
            if l_indent < 2:
                break
            block.append(l)
            j += 1

        # Strip trailing blanks from block.
        while block and not block[-1].strip():
            block.pop()
        if not block:
            out.append(line)
            i += 1
            continue

        # Compute minimum indent of the block to dedent.
        min_indent = min(
            (len(b) - len(b.lstrip()) for b in block if b.strip()),
            default=0,
        )
        dedented = [b[min_indent:] if len(b) >= min_indent else b for b in block]

        # Emit: optional adjusted paragraph + blank + fenced block.
        if is_paragraph_colon:
            # Reduce trailing "::" to ":" per RST convention.
            adjusted = stripped[:-1]
            # Preserve original leading indent.
            lead = line[:len(line) - len(line.lstrip())]
            out.append(f"{lead}{adjusted}")
        # Drop the bare-colon marker entirely.

        out.append('')
        out.append('```')
        out.extend(dedented)
        out.append('```')
        # Preserve a blank separator after.
        if j < n and lines[j].strip():
            out.append('')

        # Re-scan fence ranges since we just inserted fences.
        fixes += 1
        if verbose:
            preview = (dedented[0] if dedented else '')[:50]
            print(f"  Fenced lone-colon block at line {i + 1}: {preview!r}")
        i = j
        # Update fence ranges for subsequent iterations.
        # Cheapest correct approach: rescan from the current `out` length.
        # We handle this by simply not stepping back into already-emitted
        # output; the new fenced lines we just added are in `out`, not
        # `lines`, so they won't re-trigger.

    return '\n'.join(out), fixes


def fix_empty_fence_orphans(content: str, verbose: bool = False) -> Tuple[str, int]:
    """Detect empty fence pairs followed by indented content and merge them.

    Pattern (outside of nested fenced blocks):

        ```lang
        ```

            code line
            code line

    Becomes:

        ```lang
        code line
        code line
        ```

    The original `fix_empty_blocks` handles the single-blank-line case, but
    longer separators or specially-structured continuations slip past. This
    pass complements it.

    Idempotent: the merge only happens when an empty fence pair is found.
    """
    lines = content.split('\n')
    out: List[str] = []
    fixes = 0
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        # Detect empty fence pair: ```lang\n``` (with optional blank between).
        m = re.match(r'^[ \t]*(`{3,})(\w*)\s*$', line)
        if not m:
            out.append(line)
            i += 1
            continue
        ticks = m.group(1)
        lang = m.group(2)
        # Walk forward over blanks.
        j = i + 1
        while j < n and not lines[j].strip():
            j += 1
        if j >= n:
            out.append(line)
            i += 1
            continue
        # Closing fence?
        cm = re.match(r'^[ \t]*(`{3,})\s*$', lines[j])
        if not cm or len(cm.group(1)) < len(ticks):
            out.append(line)
            i += 1
            continue
        # Now look past the empty fence pair for indented content.
        k = j + 1
        while k < n and not lines[k].strip():
            k += 1
        if k >= n:
            out.append(line)
            i += 1
            continue
        first = lines[k]
        first_indent = len(first) - len(first.lstrip())
        if first_indent < 2:
            # No indented continuation — leave the empty fence untouched.
            out.append(line)
            i += 1
            continue

        # Capture indented block (allow internal blanks; min 2-space indent).
        block: List[str] = []
        p = k
        while p < n:
            l = lines[p]
            if not l.strip():
                q = p + 1
                while q < n and not lines[q].strip():
                    q += 1
                if q >= n:
                    break
                q_indent = len(lines[q]) - len(lines[q].lstrip())
                if q_indent < 2 or lines[q].lstrip().startswith('```'):
                    break
                block.extend(lines[p:q])
                p = q
                continue
            if l.lstrip().startswith('```'):
                break
            l_indent = len(l) - len(l.lstrip())
            if l_indent < 2:
                break
            block.append(l)
            p += 1

        while block and not block[-1].strip():
            block.pop()

        if not block:
            out.append(line)
            i += 1
            continue

        min_indent = min(
            (len(b) - len(b.lstrip()) for b in block if b.strip()),
            default=0,
        )
        dedented = [b[min_indent:] if len(b) >= min_indent else b for b in block]

        out.append(f"```{lang}" if lang else "```")
        out.extend(dedented)
        out.append('```')
        if p < n and lines[p].strip():
            out.append('')

        fixes += 1
        if verbose:
            preview = dedented[0][:50] if dedented else ''
            print(f"  Merged empty fence + orphan at line {i + 1}: {preview!r}")
        i = p

    return '\n'.join(out), fixes


def process_file(filepath: Path, dry_run: bool = False, verbose: bool = False) -> int:
    """Process a single file and fix code blocks.

    Returns number of fixes applied.
    """
    content = filepath.read_text(encoding='utf-8')

    # Fix 1: Convert lone `:` / `::` literal markers into fenced blocks.
    fixed_content, fixes0 = fix_lone_colon_lines(content, verbose)

    # Fix 2: Empty blocks with orphaned code (existing pass, with relaxed
    # continuation heuristic).
    fixed_content, fixes1 = fix_empty_blocks(fixed_content, verbose)

    # Fix 3: Empty fence pair followed by indented orphan content.
    fixed_content, fixes3 = fix_empty_fence_orphans(fixed_content, verbose)

    # Fix 4: Headings inside code blocks
    fixed_content, fixes2 = fix_headings_inside_code_blocks(fixed_content, verbose)

    fixes = fixes0 + fixes1 + fixes2 + fixes3
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
    parser.add_argument('--report-orphans', action='store_true',
                        help='Report lone-colon and empty-fence orphan counts per file')

    args = parser.parse_args()

    path = Path(args.path)

    if args.file:
        files = [Path(args.file)]
    elif path.is_file():
        files = [path]
    else:
        files = sorted(path.rglob('*.md'))

    if args.report_orphans:
        total_lone = 0
        total_empty = 0
        for filepath in files:
            try:
                text = filepath.read_text(encoding='utf-8')
            except (OSError, UnicodeDecodeError):
                continue
            _, n_lone = fix_lone_colon_lines(text)
            _, n_empty = fix_empty_fence_orphans(text)
            if n_lone or n_empty:
                print(f"{filepath}: {n_lone} lone-colon, {n_empty} empty-fence orphans")
                total_lone += n_lone
                total_empty += n_empty
        print(f"\nTotal: {total_lone} lone-colon literals, {total_empty} empty-fence orphans")
        return 0

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
