#!/usr/bin/env python3
"""
Fix incorrect filename references in converted Markdown files.

During RST→Markdown conversion, some cross-file links use incorrect filenames
(e.g., 'test-case.md' instead of 'creating-test-cases.md'). This script
corrects them using the filename_corrections map in reference_map.json.

This script is IDEMPOTENT - running it multiple times produces the same result.

Usage:
    python fix_file_references.py              # Fix all files
    python fix_file_references.py --dry-run    # Preview changes
    python fix_file_references.py --report     # Show what would change
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


SCRIPT_DIR = Path(__file__).parent.resolve()
DOCS_DIR = SCRIPT_DIR.parent / "docs"
REFERENCE_MAP = SCRIPT_DIR / "reference_map.json"


def load_corrections() -> Dict[str, str]:
    """Load filename corrections from reference map."""
    with open(REFERENCE_MAP, encoding="utf-8") as f:
        ref_map = json.load(f)
    corrections = ref_map.get("filename_corrections", {})
    # Remove comment entries
    return {k: v for k, v in corrections.items() if not k.startswith("_")}


def fix_file_references_in_content(
    content: str, corrections: Dict[str, str],
    file_path: Path = None, docs_dir: Path = None
) -> Tuple[str, int, List[str]]:
    """
    Fix incorrect filenames and relative path depth in Markdown link targets.

    Handles patterns like:
    - [text](../section/wrong-name.md#anchor) - wrong filename
    - [text](wrong-name.md#anchor) - wrong filename
    - [text](../../section/file.md) - wrong path depth

    Returns: (fixed_content, fix_count, details)
    """
    fix_count = 0
    details = []

    # Step 1: Fix wrong filenames
    for wrong_name, correct_name in corrections.items():
        pattern = re.compile(
            r'(\[[^\]]*\]\([^)]*?)' +      # [text](prefix...
            re.escape(wrong_name) +          # wrong-name.md
            r'([#)][^)]*\)|[\)])',           # #anchor) or )
            re.DOTALL
        )

        def replace_ref(match, wn=wrong_name, cn=correct_name):
            nonlocal fix_count
            fix_count += 1
            details.append(f"  filename: {wn} → {cn}")
            return match.group(1) + cn + match.group(2)

        content = pattern.sub(replace_ref, content)

    # Step 2: Fix relative path depth issues (../../ section/ → ../section/)
    # When a file is at depth 1 (e.g., extending/file.md), links to other
    # depth-1 sections should use ../ not ../../
    if file_path and docs_dir:
        file_rel = file_path.relative_to(docs_dir)
        file_depth = len(file_rel.parts) - 1  # directory depth (exclude filename)

        # Fix over-deep relative paths
        # e.g., from extending/file.md, ../../creating-test-data/x.md is wrong
        # because extending/ is only 1 level deep, so ../ goes to docs root
        def fix_path_depth(match):
            nonlocal fix_count
            prefix = match.group(1)
            path = match.group(2)

            # Count ../ segments in the path
            up_count = 0
            remaining = path
            while remaining.startswith("../"):
                up_count += 1
                remaining = remaining[3:]

            # If going up more levels than the file's directory depth, fix it
            if up_count > file_depth and file_depth > 0:
                correct_ups = "../" * file_depth
                fix_count += 1
                fixed = correct_ups + remaining
                details.append(f"  depth: {'../' * up_count}{remaining} → {fixed}")
                return prefix + fixed

            return match.group(0)

        # Match links with ../ paths: [text](../../path)
        depth_pattern = re.compile(
            r'(\[[^\]]*\]\()' +           # [text](
            r'((?:\.\./){2,}[^)]+)' +     # ../../path (2+ levels up)
            r'\)',
            re.DOTALL
        )
        content = depth_pattern.sub(fix_path_depth, content)

    return content, fix_count, details


def process_file(
    file_path: Path, corrections: Dict[str, str],
    dry_run: bool = False, report: bool = False,
    docs_dir: Path = None
) -> int:
    """Process a single file. Returns number of fixes."""
    content = file_path.read_text(encoding="utf-8")
    fixed_content, fix_count, details = fix_file_references_in_content(
        content, corrections, file_path, docs_dir
    )

    if fix_count > 0:
        rel_path = file_path.relative_to(DOCS_DIR)
        if report or dry_run:
            print(f"  {rel_path}: {fix_count} fixes")
            for d in details:
                print(f"    {d}")
        if not dry_run:
            file_path.write_text(fixed_content, encoding="utf-8")

    return fix_count


def main():
    parser = argparse.ArgumentParser(
        description="Fix incorrect filename references in Markdown links"
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview changes")
    parser.add_argument("--report", action="store_true", help="Show details")
    parser.add_argument("--file", type=Path, help="Process single file")
    args = parser.parse_args()

    corrections = load_corrections()
    if not corrections:
        print("No filename corrections defined in reference_map.json")
        return 0

    print(f"Filename corrections loaded: {len(corrections)} mappings")
    for wrong, correct in corrections.items():
        print(f"  {wrong} → {correct}")

    if args.file:
        files = [args.file]
    else:
        files = sorted(DOCS_DIR.rglob("*.md"))
        files = [f for f in files
                 if not any(p[0].isupper() for p in f.relative_to(DOCS_DIR).parts[:-1])]

    total_fixes = 0
    for file_path in files:
        total_fixes += process_file(
            file_path, corrections, args.dry_run, args.report, DOCS_DIR
        )

    print(f"\nFixed {total_fixes} incorrect filename references across {len(files)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
