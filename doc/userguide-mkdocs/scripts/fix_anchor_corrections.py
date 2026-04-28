#!/usr/bin/env python3
"""
Apply data-driven anchor corrections to converted Markdown files.

Reads anchor_corrections.json which maps broken anchor links to their correct
targets. This handles cases that automated scripts can't resolve:
- RST anonymous references that became wrong #slug links
- Heading slug mismatches between old and new format
- Cross-page references with incorrect anchor names

This script is IDEMPOTENT and DATA-DRIVEN. To fix new broken anchors,
add entries to anchor_corrections.json rather than modifying this script.

Usage:
    python fix_anchor_corrections.py              # Apply all corrections
    python fix_anchor_corrections.py --dry-run    # Preview changes
    python fix_anchor_corrections.py --report     # Show stats
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


SCRIPT_DIR = Path(__file__).parent.resolve()
DOCS_DIR = SCRIPT_DIR.parent / "docs"
CORRECTIONS_FILE = SCRIPT_DIR / "anchor_corrections.json"


def load_corrections() -> Dict[str, Dict[str, str]]:
    """Load corrections grouped by MD file.

    Returns {md_file: {broken_link: correct_link}}
    """
    with open(CORRECTIONS_FILE, encoding="utf-8") as f:
        raw = json.load(f)

    by_file: Dict[str, Dict[str, str]] = {}
    for key, value in raw.items():
        if key.startswith("_"):
            continue
        parts = key.split("|", 1)
        if len(parts) != 2:
            continue
        md_file, broken_link = parts
        by_file.setdefault(md_file, {})[broken_link] = value

    return by_file


def apply_corrections(
    md_file: str,
    corrections: Dict[str, str],
    dry_run: bool = False
) -> Tuple[int, List[str]]:
    """Apply corrections to a single MD file."""
    md_path = DOCS_DIR / md_file
    if not md_path.exists():
        return 0, [f"  File not found: {md_file}"]

    content = md_path.read_text(encoding="utf-8")
    original = content
    fixed = 0
    details = []

    for broken_link, correct_link in corrections.items():
        # Build the pattern to find: ](broken_link)
        escaped = re.escape(broken_link)
        pattern = re.compile(r'\](\(' + escaped + r'\))')

        matches = pattern.findall(content)
        if matches:
            # Replace ](broken_link) with ](correct_link)
            old = f']({broken_link})'
            new = f']({correct_link})'
            count = content.count(old)
            if count > 0:
                content = content.replace(old, new)
                fixed += count
                details.append(f"  {broken_link} → {correct_link} ({count}x)")

    if fixed > 0 and not dry_run and content != original:
        md_path.write_text(content, encoding="utf-8")

    return fixed, details


def main():
    parser = argparse.ArgumentParser(
        description="Apply data-driven anchor corrections"
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview changes")
    parser.add_argument("--report", action="store_true", help="Show details")
    args = parser.parse_args()

    corrections_by_file = load_corrections()
    total_corrections = sum(len(v) for v in corrections_by_file.values())
    print(f"Loaded {total_corrections} corrections for {len(corrections_by_file)} files")

    total_fixed = 0
    for md_file, corrections in sorted(corrections_by_file.items()):
        fixed, details = apply_corrections(md_file, corrections, args.dry_run)
        total_fixed += fixed
        if fixed > 0 and (args.report or args.dry_run):
            print(f"\n  {md_file}: {fixed} corrections")
            for d in details:
                print(f"    {d}")

    print(f"\nApplied {total_fixed} anchor corrections")
    return 0


if __name__ == "__main__":
    sys.exit(main())
