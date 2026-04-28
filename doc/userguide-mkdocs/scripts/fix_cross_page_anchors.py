#!/usr/bin/env python3
"""
Fix cross-page anchor references in converted Markdown files.

After RST→MkDocs conversion, many internal links use #anchor format pointing to
sections that were on the same single-page HTML but are now on different MkDocs pages.
This script builds a global heading→page map and rewrites #anchor links to
../page.md#anchor format.

This script is IDEMPOTENT - running it multiple times produces the same result.

Usage:
    python fix_cross_page_anchors.py              # Fix all files
    python fix_cross_page_anchors.py --dry-run    # Preview changes
    python fix_cross_page_anchors.py --report     # Show anchor map and stats
    python fix_cross_page_anchors.py --file X.md  # Fix single file
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


SCRIPT_DIR = Path(__file__).parent.resolve()
DOCS_DIR = SCRIPT_DIR.parent / "docs"


def slugify(text: str) -> str:
    """Convert heading text to MkDocs anchor slug.

    MkDocs uses Python-Markdown's toc extension which generates anchors by:
    - lowercasing
    - removing everything except alphanumerics, hyphens, underscores, spaces
    - converting spaces to hyphens
    - collapsing multiple hyphens
    """
    slug = text.lower()
    # Remove inline code backticks and their content markers
    slug = re.sub(r'`([^`]*)`', r'\1', slug)
    # Remove bold/italic markers
    slug = re.sub(r'\*+([^*]*)\*+', r'\1', slug)
    # Remove special chars except hyphens, underscores, spaces
    slug = re.sub(r'[^\w\s-]', '', slug)
    # Spaces and underscores to hyphens
    slug = re.sub(r'[\s_]+', '-', slug)
    # Collapse multiple hyphens
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')


def extract_anchors_from_file(filepath: Path) -> Dict[str, str]:
    """Extract all anchors available on a page.

    Returns {anchor_slug: heading_text} for both:
    - Auto-generated heading anchors (## Heading → #heading)
    - Explicit HTML anchors (<a id="name"></a>)
    """
    content = filepath.read_text(encoding="utf-8")
    anchors = {}

    # Extract heading anchors
    in_code = False
    for line in content.split('\n'):
        stripped = line.rstrip()
        if re.match(r'^`{3,}', stripped):
            info = stripped.lstrip('`').strip()
            if in_code:
                if not info:  # closing fence has no info string
                    in_code = False
            else:
                in_code = True
            continue

        if in_code:
            continue

        # Markdown headings
        m = re.match(r'^(#{1,6})\s+(.+)$', stripped)
        if m:
            heading_text = m.group(2).strip()
            slug = slugify(heading_text)
            if slug:
                anchors[slug] = heading_text

        # Explicit HTML anchors
        for m in re.finditer(r'<a\s+id="([^"]+)"', stripped):
            anchors[m.group(1)] = m.group(1)

    return anchors


def build_global_anchor_map(docs_dir: Path) -> Dict[str, List[str]]:
    """Build global map: {anchor_slug: [file_paths_containing_this_anchor]}.

    Returns list of files because the same anchor might exist on multiple pages.
    """
    anchor_map: Dict[str, List[str]] = {}

    for md_file in sorted(docs_dir.rglob("*.md")):
        # Skip CamelCase directories
        parts = md_file.relative_to(docs_dir).parts
        if any(p[0].isupper() for p in parts[:-1]):
            continue

        rel_path = str(md_file.relative_to(docs_dir))
        anchors = extract_anchors_from_file(md_file)

        for slug in anchors:
            if slug not in anchor_map:
                anchor_map[slug] = []
            anchor_map[slug].append(rel_path)

    return anchor_map


def find_broken_anchors(filepath: Path, local_anchors: Dict[str, str]) -> List[Tuple[int, str, str]]:
    """Find all #anchor links that don't exist on this page.

    Returns [(line_number, full_link, anchor_slug), ...]
    """
    content = filepath.read_text(encoding="utf-8")
    broken = []

    in_code = False
    for i, line in enumerate(content.split('\n'), 1):
        stripped = line.rstrip()
        if re.match(r'^`{3,}', stripped):
            info = stripped.lstrip('`').strip()
            if in_code:
                if not info:
                    in_code = False
            else:
                in_code = True
            continue

        if in_code:
            continue

        # Find same-page anchor links: [text](#anchor) or (#anchor)
        for m in re.finditer(r'\]\(#([^)]+)\)', line):
            anchor = m.group(1)
            if anchor not in local_anchors:
                broken.append((i, m.group(0), anchor))

    return broken


def fix_anchors_in_file(
    filepath: Path,
    local_anchors: Dict[str, str],
    global_map: Dict[str, List[str]],
    docs_dir: Path,
    dry_run: bool = False
) -> Tuple[int, int, List[str]]:
    """Fix broken cross-page anchors in a single file.

    Returns (fixed_count, unresolved_count, details)
    """
    content = filepath.read_text(encoding="utf-8")
    file_rel = str(filepath.relative_to(docs_dir))
    file_dir = str(filepath.parent.relative_to(docs_dir))
    fixed = 0
    unresolved = 0
    details = []

    broken = find_broken_anchors(filepath, local_anchors)
    if not broken:
        return 0, 0, []

    lines = content.split('\n')

    for line_num, full_link, anchor in broken:
        # Look up anchor in global map
        candidates = global_map.get(anchor, [])

        # Filter out the current file
        candidates = [c for c in candidates if c != file_rel]

        if not candidates:
            # Try fuzzy match: the anchor might be slightly different
            # (e.g., "test-cases" vs "creating-test-cases")
            fuzzy_candidates = []
            for key, files in global_map.items():
                if anchor in key or key in anchor:
                    for f in files:
                        if f != file_rel:
                            fuzzy_candidates.append((key, f))

            if fuzzy_candidates:
                # Pick the best fuzzy match (shortest key that contains the anchor)
                fuzzy_candidates.sort(key=lambda x: len(x[0]))
                best_key, best_file = fuzzy_candidates[0]
                target_path = os.path.relpath(best_file, file_dir)
                target_path = target_path.replace(os.sep, '/')

                old_ref = f"](#{anchor})"
                new_ref = f"]({target_path}#{best_key})"

                idx = line_num - 1
                if old_ref in lines[idx]:
                    lines[idx] = lines[idx].replace(old_ref, new_ref, 1)
                    fixed += 1
                    details.append(f"  L{line_num}: #{anchor} → {target_path}#{best_key} (fuzzy)")
                else:
                    unresolved += 1
                    details.append(f"  L{line_num}: #{anchor} UNRESOLVED (fuzzy candidates exist)")
            else:
                unresolved += 1
                details.append(f"  L{line_num}: #{anchor} UNRESOLVED")
            continue

        # Pick the best candidate (prefer same section, then shortest path)
        target_file = candidates[0]
        if len(candidates) > 1:
            # Prefer file in same section
            current_section = file_dir.split('/')[0] if '/' in file_dir else file_dir
            same_section = [c for c in candidates
                           if c.startswith(current_section + '/')]
            if same_section:
                target_file = same_section[0]

        # Compute relative path
        target_path = os.path.relpath(target_file, file_dir)
        target_path = target_path.replace(os.sep, '/')

        # Replace in the line
        old_ref = f"](#{anchor})"
        new_ref = f"]({target_path}#{anchor})"

        idx = line_num - 1
        if old_ref in lines[idx]:
            lines[idx] = lines[idx].replace(old_ref, new_ref, 1)
            fixed += 1
            details.append(f"  L{line_num}: #{anchor} → {target_path}#{anchor}")
        else:
            unresolved += 1
            details.append(f"  L{line_num}: #{anchor} UNRESOLVED (not found in line)")

    if fixed > 0 and not dry_run:
        filepath.write_text('\n'.join(lines), encoding="utf-8")

    return fixed, unresolved, details


def main():
    parser = argparse.ArgumentParser(
        description="Fix cross-page anchor references in MkDocs Markdown"
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview changes")
    parser.add_argument("--report", action="store_true", help="Show anchor map stats")
    parser.add_argument("--file", type=Path, help="Process single file")
    parser.add_argument("--verbose", action="store_true", help="Show all details")
    args = parser.parse_args()

    print("Building global anchor map...")
    global_map = build_global_anchor_map(DOCS_DIR)
    print(f"  Found {len(global_map)} unique anchors across all pages")

    if args.report:
        # Show anchors that exist on multiple pages
        multi = {k: v for k, v in global_map.items() if len(v) > 1}
        print(f"  Anchors on multiple pages: {len(multi)}")
        for anchor, files in sorted(multi.items())[:20]:
            print(f"    #{anchor}: {', '.join(files)}")

    if args.file:
        files = [args.file]
    else:
        files = sorted(DOCS_DIR.rglob("*.md"))
        files = [f for f in files
                 if not any(p[0].isupper()
                            for p in f.relative_to(DOCS_DIR).parts[:-1])]

    total_fixed = 0
    total_unresolved = 0

    for filepath in files:
        local_anchors = extract_anchors_from_file(filepath)
        fixed, unresolved, details = fix_anchors_in_file(
            filepath, local_anchors, global_map, DOCS_DIR, args.dry_run
        )

        if (fixed > 0 or unresolved > 0) and (args.verbose or args.report or args.dry_run):
            rel = filepath.relative_to(DOCS_DIR)
            print(f"\n  {rel}: {fixed} fixed, {unresolved} unresolved")
            if args.verbose:
                for d in details:
                    print(f"    {d}")

        total_fixed += fixed
        total_unresolved += unresolved

    print(f"\nFixed {total_fixed} cross-page anchor references")
    if total_unresolved > 0:
        print(f"Unresolved: {total_unresolved} anchors (sections may not exist yet)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
