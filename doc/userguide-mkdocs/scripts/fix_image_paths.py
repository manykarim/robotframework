#!/usr/bin/env python3
"""
Fix image paths from CamelCase RST structure to MkDocs section-local paths.

The converter generates image references using the RST source layout:
    ![alt](../assets/images/ExecutingTestCases/log_passed.png)
    ![alt](src/ExecutingTestCases/log_passed.png)

But images are copied to section-local directories:
    docs/executing-tests/log_passed.png

This script rewrites image paths to use section-local references:
    ![alt](log_passed.png)

Also handles cross-section image references by computing relative paths.

This script is IDEMPOTENT.

Usage:
    python fix_image_paths.py              # Fix all files
    python fix_image_paths.py --dry-run    # Preview changes
    python fix_image_paths.py --report     # Show details
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


SCRIPT_DIR = Path(__file__).parent.resolve()
DOCS_DIR = SCRIPT_DIR.parent / "docs"
REFERENCE_MAP = SCRIPT_DIR / "reference_map.json"


def load_section_map() -> Dict[str, str]:
    """Load CamelCase→lowercase section directory mapping."""
    with open(REFERENCE_MAP, encoding="utf-8") as f:
        ref_map = json.load(f)
    return {k: v for k, v in ref_map.get("section_dirs", {}).items()
            if not k.startswith("_")}


def build_image_inventory() -> Dict[str, str]:
    """Build map of image filename → relative path within docs/.

    Returns {filename: section_dir/filename} for all images.
    """
    inventory = {}
    img_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico'}

    for img in DOCS_DIR.rglob("*"):
        if img.suffix.lower() in img_extensions and not any(
            p[0].isupper() for p in img.relative_to(DOCS_DIR).parts[:-1]
        ):
            rel = str(img.relative_to(DOCS_DIR))
            inventory[img.name] = rel

    return inventory


def fix_image_paths_in_content(
    content: str,
    file_path: Path,
    section_map: Dict[str, str],
    image_inventory: Dict[str, str],
) -> Tuple[str, int, List[str]]:
    """Fix image paths in a single file's content.

    Returns (fixed_content, fix_count, details).
    """
    file_dir = str(file_path.parent.relative_to(DOCS_DIR))
    fixes = 0
    details = []

    # Pattern: image references in Markdown
    # Matches: ![alt](path) and [text](path.png) for image-like paths
    img_pattern = re.compile(
        r'(!?\[[^\]]*\]\()' +           # ![alt]( or [text](
        r'([^)]*?' +                     # path prefix
        r'(?:' +
        r'[A-Z][a-zA-Z]*/' +            # CamelCase directory component
        r'|assets/images/' +             # or assets/images/ path
        r'|src/' +                       # or src/ path
        r')' +
        r'[^)]*\.(?:png|jpg|jpeg|gif|svg)' +  # ending with image extension
        r')(\))',                         # closing )
    )

    def fix_path(match):
        nonlocal fixes
        prefix = match.group(1)
        path = match.group(2)
        suffix = match.group(3)

        # Extract just the filename
        filename = Path(path).name

        # Look up in image inventory
        if filename in image_inventory:
            img_rel = image_inventory[filename]
            # Compute relative path from current file to image
            new_path = os.path.relpath(img_rel, file_dir).replace(os.sep, '/')
            if new_path != path:
                fixes += 1
                details.append(f"  {path} → {new_path}")
                return prefix + new_path + suffix

        return match.group(0)

    content = img_pattern.sub(fix_path, content)
    return content, fixes, details


def process_file(
    filepath: Path,
    section_map: Dict[str, str],
    image_inventory: Dict[str, str],
    dry_run: bool = False,
    report: bool = False,
) -> int:
    """Process a single file. Returns fix count."""
    content = filepath.read_text(encoding="utf-8")
    fixed, count, details = fix_image_paths_in_content(
        content, filepath, section_map, image_inventory
    )

    if count > 0:
        if report or dry_run:
            rel = filepath.relative_to(DOCS_DIR)
            print(f"\n  {rel}: {count} image path fixes")
            for d in details:
                print(f"    {d}")
        if not dry_run:
            filepath.write_text(fixed, encoding="utf-8")

    return count


def main():
    parser = argparse.ArgumentParser(
        description="Fix CamelCase image paths to section-local paths"
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview changes")
    parser.add_argument("--report", action="store_true", help="Show details")
    args = parser.parse_args()

    section_map = load_section_map()
    image_inventory = build_image_inventory()

    print(f"Image inventory: {len(image_inventory)} images found")
    if args.report:
        for name, path in sorted(image_inventory.items()):
            print(f"  {name} → {path}")

    files = sorted(DOCS_DIR.rglob("*.md"))
    files = [f for f in files
             if not any(p[0].isupper() for p in f.relative_to(DOCS_DIR).parts[:-1])]

    total = 0
    for filepath in files:
        total += process_file(filepath, section_map, image_inventory,
                              args.dry_run, args.report)

    print(f"\nFixed {total} image paths across {len(files)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
