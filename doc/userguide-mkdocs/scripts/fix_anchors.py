#!/usr/bin/env python3
"""Fix broken anchor links in Robot Framework User Guide MkDocs documentation.

This script fixes:
1. Anchors with spaces - converts to lowercase hyphenated format
   e.g., `](#user keywords)` -> `](#user-keywords)`
2. GitHub issue references with double hash
   e.g., `](##5250)` -> `](https://github.com/robotframework/robotframework/issues/5250)`
"""
import re
from pathlib import Path
from collections import defaultdict


GITHUB_ISSUES_BASE = "https://github.com/robotframework/robotframework/issues/"


def convert_anchor_to_slug(anchor: str) -> str:
    """Convert an anchor with spaces to a proper MkDocs slug.

    MkDocs converts headings to anchors by:
    - Converting to lowercase
    - Replacing spaces with hyphens
    - Removing special characters (except hyphens)
    """
    # Convert to lowercase
    slug = anchor.lower()
    # Replace spaces with hyphens
    slug = slug.replace(' ', '-')
    # Remove or replace special characters that aren't valid in anchors
    # Keep alphanumeric, hyphens, and underscores
    slug = re.sub(r'[^\w\-]', '', slug)
    # Collapse multiple hyphens
    slug = re.sub(r'-+', '-', slug)
    # Strip leading/trailing hyphens
    slug = slug.strip('-')
    return slug


def fix_anchors_with_spaces(content: str) -> tuple[str, list[dict]]:
    """Fix anchor links that contain spaces.

    Converts `](#anchor with spaces)` to `](#anchor-with-spaces)`

    Returns tuple of (modified_content, list_of_changes)
    """
    changes = []

    # Pattern to match markdown links with anchors containing spaces
    # Matches: ](#anchor with spaces) where anchor has at least one space
    # Captures: the anchor text including the # prefix
    pattern = r'\]\(#([^)]*\s[^)]*)\)'

    def replace_anchor(match):
        original_anchor = match.group(1)
        new_anchor = convert_anchor_to_slug(original_anchor)
        changes.append({
            'type': 'anchor_space',
            'original': f'](#{original_anchor})',
            'replacement': f'](#{new_anchor})'
        })
        return f'](#{new_anchor})'

    modified = re.sub(pattern, replace_anchor, content)
    return modified, changes


def fix_github_issue_refs(content: str) -> tuple[str, list[dict]]:
    """Fix GitHub issue references with double hash.

    Converts `](##5250)` to `](https://github.com/robotframework/robotframework/issues/5250)`

    Returns tuple of (modified_content, list_of_changes)
    """
    changes = []

    # Pattern to match double-hash issue references
    # Matches: ](##NNNN) where NNNN is one or more digits
    pattern = r'\]\(##(\d+)\)'

    def replace_issue_ref(match):
        issue_num = match.group(1)
        full_url = f'{GITHUB_ISSUES_BASE}{issue_num}'
        changes.append({
            'type': 'github_issue',
            'original': f'](##{issue_num})',
            'replacement': f']({full_url})'
        })
        return f']({full_url})'

    modified = re.sub(pattern, replace_issue_ref, content)
    return modified, changes


def process_file(filepath: Path) -> dict:
    """Process a single markdown file.

    Returns dict with file info and changes made.
    """
    content = filepath.read_text(encoding='utf-8')
    original = content
    all_changes = []

    # Fix anchors with spaces
    content, anchor_changes = fix_anchors_with_spaces(content)
    all_changes.extend(anchor_changes)

    # Fix GitHub issue references
    content, issue_changes = fix_github_issue_refs(content)
    all_changes.extend(issue_changes)

    result = {
        'filepath': filepath,
        'modified': content != original,
        'changes': all_changes
    }

    if content != original:
        filepath.write_text(content, encoding='utf-8')

    return result


def main():
    """Process all markdown files in the docs directory."""
    script_dir = Path(__file__).parent
    docs_dir = script_dir.parent / "docs"

    if not docs_dir.exists():
        print(f"Error: docs directory not found at {docs_dir}")
        return 1

    md_files = sorted(docs_dir.rglob("*.md"))

    print(f"Scanning {len(md_files)} markdown files for broken anchor links...")
    print("=" * 70)

    total_changes = 0
    files_modified = 0
    change_counts = defaultdict(int)

    for filepath in md_files:
        result = process_file(filepath)

        if result['modified']:
            files_modified += 1
            rel_path = filepath.relative_to(docs_dir)
            print(f"\n{rel_path}:")

            for change in result['changes']:
                total_changes += 1
                change_counts[change['type']] += 1
                print(f"  - {change['original']}")
                print(f"    -> {change['replacement']}")

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Files scanned:  {len(md_files)}")
    print(f"Files modified: {files_modified}")
    print(f"Total changes:  {total_changes}")
    print()
    print("Changes by type:")
    print(f"  - Anchors with spaces fixed: {change_counts['anchor_space']}")
    print(f"  - GitHub issue refs fixed:   {change_counts['github_issue']}")

    return 0


if __name__ == "__main__":
    exit(main())
