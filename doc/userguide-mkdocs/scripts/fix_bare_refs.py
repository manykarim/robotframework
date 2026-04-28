#!/usr/bin/env python3
"""
Fix bare RST-style word references (Word_) in converted Markdown files.

RST uses `Word_` syntax for hyperlink references. After conversion to Markdown,
some of these remain unconverted as bare `Word_` text. This script converts them
to proper Markdown links using the reference_map.json data file.

This script is IDEMPOTENT - running it multiple times produces the same result.
It will not modify already-converted [Word](url) links.

Usage:
    python fix_bare_refs.py                    # Fix all files
    python fix_bare_refs.py --file path.md     # Fix single file
    python fix_bare_refs.py --dry-run          # Preview changes
    python fix_bare_refs.py --report           # Show remaining unconverted refs
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


SCRIPT_DIR = Path(__file__).parent.resolve()
DOCS_DIR = SCRIPT_DIR.parent / "docs"
REFERENCE_MAP = SCRIPT_DIR / "reference_map.json"


def load_reference_map() -> dict:
    """Load the reference mappings."""
    with open(REFERENCE_MAP, encoding="utf-8") as f:
        return json.load(f)


def get_ignore_patterns(ref_map: dict) -> Set[str]:
    """Build set of patterns to ignore (Python constants, etc.).

    Uses EXACT case matching to avoid blocking legitimate refs like Process_
    when PROCESS_ is in the ignore list.
    """
    ignores = set()
    for item in ref_map.get("ignore_bare_refs", []):
        if not item.startswith("_comment"):
            ignores.add(item)  # Exact case, not uppercased
    return ignores


def compute_relative_path(from_file: Path, to_path: str, docs_dir: Path) -> str:
    """Compute relative path from a file to a target path within docs/."""
    if to_path.startswith("http://") or to_path.startswith("https://"):
        return to_path

    from_dir = from_file.parent.relative_to(docs_dir)
    target = Path(to_path)

    # Compute relative path
    rel = os.path.relpath(target, from_dir)
    # Normalize to forward slashes
    return rel.replace(os.sep, "/")


def is_inside_code_block(content: str, pos: int) -> bool:
    """Check if a position is inside a fenced code block."""
    # Count ``` fences before this position
    fence_count = 0
    search_area = content[:pos]
    for match in re.finditer(r'^```', search_area, re.MULTILINE):
        fence_count += 1
    # Odd count means we're inside a code block
    return fence_count % 2 == 1


def is_inside_inline_code(line: str, pos_in_line: int) -> bool:
    """Check if a position in a line is inside inline code backticks.

    Uses regex to find all `...` spans on the line and checks if pos falls inside one.
    This is more robust than counting backticks, as it handles multi-line edge cases.
    """
    for match in re.finditer(r'`[^`]+`', line):
        if match.start() < pos_in_line < match.end():
            return True
    return False


def is_inside_link_target(line: str, pos_in_line: int) -> bool:
    """Check if a position is inside a Markdown link target ](...)."""
    for match in re.finditer(r'\]\([^)]*\)', line):
        if match.start() < pos_in_line < match.end():
            return True
    return False


def fix_bare_refs_in_content(
    content: str,
    file_path: Path,
    ref_map: dict,
    docs_dir: Path,
    dry_run: bool = False
) -> Tuple[str, int, List[str]]:
    """
    Fix bare Word_ references in content.

    Returns: (fixed_content, fix_count, remaining_unresolved)
    """
    bare_refs = ref_map.get("bare_word_refs", {})
    api_refs = ref_map.get("api_references", {})
    api_base = api_refs.get("base_url", "")
    ignore_patterns = get_ignore_patterns(ref_map)

    fix_count = 0
    unresolved = []
    lines = content.split('\n')
    result_lines = []
    in_code_block = False

    for line in lines:
        # Track code block state
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            result_lines.append(line)
            continue

        if in_code_block:
            result_lines.append(line)
            continue

        # Skip HTML comment lines
        if line.strip().startswith('<!--') or line.strip().startswith('<a id='):
            result_lines.append(line)
            continue

        # Fix API-style references: running.TestSuite_ -> [TestSuite](url)
        for api_name, api_path in api_refs.items():
            if api_name.startswith("_") or api_name == "base_url":
                continue
            pattern = re.escape(api_name) + r'_(?![_\w])'
            if re.search(pattern, line):
                display_name = api_name.split('.')[-1]
                url = api_base + api_path
                replacement = f'[{display_name}]({url})'
                line = re.sub(pattern, replacement, line)
                fix_count += 1

        # Fix bare word references: Word_ -> [Word](target)
        # Match Word_ but not ALLCAPS_ (constants) or word inside backticks
        word_pattern = r'(?<![`\[(\w])([A-Z][a-zA-Z]+)_(?![_\w`\]])'

        def replace_bare_ref(match):
            nonlocal fix_count, unresolved
            word = match.group(1)
            word_lower = word.lower()

            # Skip if it's in the ignore list (exact case match)
            full = word + "_"
            if full in ignore_patterns:
                return match.group(0)

            # Skip ALLCAPS (Python constants like ROBOT_LIBRARY_SCOPE)
            if word.isupper():
                return match.group(0)

            # Check if it's in our reference map
            if word_lower in bare_refs:
                ref_info = bare_refs[word_lower]
                display = ref_info.get("text", word)
                target = ref_info["target"]

                # Compute relative path if it's a local file reference
                if not target.startswith("http"):
                    target = compute_relative_path(file_path, target, docs_dir)

                fix_count += 1
                return f'[{display}]({target})'

            # Not in map - report as unresolved
            unresolved.append(word)
            return match.group(0)

        # Check each match position for inline code and link target context
        new_line = ""
        last_end = 0
        for match in re.finditer(word_pattern, line):
            start = match.start()
            # Check if inside inline code or link target URL
            if is_inside_inline_code(line, start) or is_inside_link_target(line, start):
                new_line += line[last_end:match.end()]
                last_end = match.end()
                continue
            # Apply replacement
            new_line += line[last_end:start]
            replacement = replace_bare_ref(match)
            new_line += replacement
            last_end = match.end()
        new_line += line[last_end:]
        result_lines.append(new_line)

    return '\n'.join(result_lines), fix_count, unresolved


def process_file(
    file_path: Path, ref_map: dict, docs_dir: Path,
    dry_run: bool = False, report: bool = False
) -> Tuple[int, List[str]]:
    """Process a single Markdown file."""
    content = file_path.read_text(encoding="utf-8")
    fixed_content, fix_count, unresolved = fix_bare_refs_in_content(
        content, file_path, ref_map, docs_dir, dry_run
    )

    if report and unresolved:
        rel_path = file_path.relative_to(docs_dir)
        for word in sorted(set(unresolved)):
            print(f"  UNRESOLVED: {word}_ in {rel_path}")

    if fix_count > 0 and not dry_run:
        file_path.write_text(fixed_content, encoding="utf-8")

    return fix_count, unresolved


def main():
    parser = argparse.ArgumentParser(description="Fix bare RST word_ references")
    parser.add_argument("--file", type=Path, help="Process single file")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes")
    parser.add_argument("--report", action="store_true",
                        help="Show remaining unresolved references")
    args = parser.parse_args()

    ref_map = load_reference_map()
    total_fixes = 0
    total_unresolved = []

    if args.file:
        files = [args.file]
    else:
        files = sorted(DOCS_DIR.rglob("*.md"))
        # Exclude CamelCase directories
        files = [f for f in files
                 if not any(p[0].isupper() for p in f.relative_to(DOCS_DIR).parts[:-1])]

    for file_path in files:
        fixes, unresolved = process_file(
            file_path, ref_map, DOCS_DIR, args.dry_run, args.report
        )
        total_fixes += fixes
        total_unresolved.extend(unresolved)

    print(f"Fixed {total_fixes} bare references across {len(files)} files")
    if total_unresolved:
        unique = sorted(set(total_unresolved))
        print(f"Unresolved: {len(unique)} unique patterns: {', '.join(unique[:20])}")
        if len(unique) > 20:
            print(f"  ... and {len(unique) - 20} more")
        print("  Add these to reference_map.json 'bare_word_refs' to resolve them.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
