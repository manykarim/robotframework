#!/usr/bin/env python3
"""
Inject missing RST label anchors into converted Markdown files.

RST uses `.. _label:` to define anchor targets. During conversion, many of these
are lost. This script extracts ALL labels from the RST source, maps them to the
corresponding MD files, and injects `<a id="slug"></a>` tags.

Three types of RST labels are handled:
  1. Simple labels: `.. _name:` → anchor before next heading
  2. Reference labels: ``.. _name: `Target`_`` → anchor at target heading
  3. External labels: ``.. _name: http://...`` → already handled as links (skip)

This script is IDEMPOTENT - running it multiple times produces the same result.
It skips anchors that already exist (from headings or previous `<a id>` tags).

Usage:
    python fix_missing_anchors.py              # Fix all files
    python fix_missing_anchors.py --dry-run    # Preview changes
    python fix_missing_anchors.py --report     # Show extraction stats
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


SCRIPT_DIR = Path(__file__).parent.resolve()
DOCS_DIR = SCRIPT_DIR.parent / "docs"
RST_SOURCE_DIR = SCRIPT_DIR.parent.parent / "userguide" / "src"
REFERENCE_MAP = SCRIPT_DIR / "reference_map.json"


def slugify(text: str) -> str:
    """Convert text to MkDocs anchor slug."""
    slug = text.lower().strip()
    slug = re.sub(r'`([^`]*)`', r'\1', slug)
    slug = re.sub(r'\*+([^*]*)\*+', r'\1', slug)
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')


def load_file_map() -> Dict[str, str]:
    """Load RST→MD file mapping from reference_map.json."""
    with open(REFERENCE_MAP, encoding="utf-8") as f:
        ref_map = json.load(f)
    return {k: v for k, v in ref_map.get("rst_to_md_files", {}).items()
            if not k.startswith("_")}


def extract_rst_labels(rst_file: Path) -> List[dict]:
    """Extract all label definitions from an RST file.

    Returns list of {name, slug, type, line, target, next_heading}
    """
    content = rst_file.read_text(encoding="utf-8")
    lines = content.split('\n')
    labels = []
    section_chars = set('=-~^"\'')

    for i, line in enumerate(lines):
        # Match: .. _label-name:
        m = re.match(r'^\.\.\s+_([^:]+):\s*(.*)$', line)
        if not m:
            continue

        label_name = m.group(1).strip().strip('`')
        label_value = m.group(2).strip()
        label_slug = slugify(label_name)

        # Classify label type
        if label_value and (label_value.startswith('http://') or label_value.startswith('https://')):
            label_type = 'external'
            target = label_value
        elif label_value and label_value.endswith('_'):
            label_type = 'reference'
            # Extract target section name: `Target Name`_ or Target_
            target_match = re.match(r'`([^`]+)`_|(\w+)_', label_value)
            target = target_match.group(1) or target_match.group(2) if target_match else label_value
        else:
            label_type = 'simple'
            target = None

        # Find the next heading after this label
        next_heading = None
        for j in range(i + 1, min(i + 20, len(lines))):
            if j + 1 < len(lines):
                next_line = lines[j + 1] if j + 1 < len(lines) else ''
                if (lines[j].strip() and next_line.strip()
                        and set(next_line.strip()) <= section_chars
                        and len(next_line.strip()) >= 3):
                    next_heading = lines[j].strip()
                    break

        labels.append({
            'name': label_name,
            'slug': label_slug,
            'type': label_type,
            'line': i + 1,
            'target': target,
            'next_heading': next_heading,
        })

    return labels


def get_existing_anchors(md_file: Path) -> Set[str]:
    """Get all existing anchors in an MD file (heading slugs + explicit <a id>)."""
    content = md_file.read_text(encoding="utf-8")
    anchors = set()

    in_code = False
    for line in content.split('\n'):
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

        # Heading anchors
        m = re.match(r'^(#{1,6})\s+(.+)$', stripped)
        if m:
            anchors.add(slugify(m.group(2)))

        # Explicit <a id="..."> anchors
        for m in re.finditer(r'<a\s+id="([^"]+)"', stripped):
            anchors.add(m.group(1))
            anchors.add(slugify(m.group(1)))

    return anchors


def find_heading_line(md_file: Path, heading_text: str) -> Optional[int]:
    """Find the line number of a heading in an MD file (1-indexed)."""
    content = md_file.read_text(encoding="utf-8")
    heading_slug = slugify(heading_text)

    for i, line in enumerate(content.split('\n'), 1):
        m = re.match(r'^(#{1,6})\s+(.+)$', line)
        if m and slugify(m.group(2)) == heading_slug:
            return i

    # Fuzzy match - try substring
    for i, line in enumerate(content.split('\n'), 1):
        m = re.match(r'^(#{1,6})\s+(.+)$', line)
        if m:
            md_slug = slugify(m.group(2))
            if heading_slug in md_slug or md_slug in heading_slug:
                return i

    return None


def inject_anchor(content: str, anchor_id: str, before_line: int) -> str:
    """Inject <a id="anchor_id"></a> before a specific line."""
    lines = content.split('\n')
    if before_line < 1 or before_line > len(lines):
        return content

    # Check if anchor already exists nearby
    check_start = max(0, before_line - 3)
    check_end = min(len(lines), before_line + 1)
    for j in range(check_start, check_end):
        if f'id="{anchor_id}"' in lines[j]:
            return content  # Already exists

    # Insert anchor tag before the heading line
    idx = before_line - 1
    anchor_tag = f'<a id="{anchor_id}"></a>'

    # Don't insert duplicate blank lines
    if idx > 0 and lines[idx - 1].strip() == '':
        lines.insert(idx, anchor_tag)
    else:
        lines.insert(idx, '')
        lines.insert(idx + 1, anchor_tag)

    return '\n'.join(lines)


def process_file(
    rst_file: str,
    md_file: str,
    file_map: Dict[str, str],
    all_labels: Dict[str, List[dict]],
    dry_run: bool = False
) -> Tuple[int, int]:
    """Process labels for a single RST→MD file pair."""
    rst_path = RST_SOURCE_DIR / rst_file
    md_path = DOCS_DIR / md_file

    if not rst_path.exists() or not md_path.exists():
        return 0, 0

    labels = extract_rst_labels(rst_path)
    if not labels:
        return 0, 0

    existing = get_existing_anchors(md_path)
    content = md_path.read_text(encoding="utf-8")
    injected = 0
    skipped = 0

    for label in labels:
        slug = label['slug']

        # Skip if anchor already exists
        if slug in existing:
            skipped += 1
            continue

        # Skip external link labels (handled elsewhere)
        if label['type'] == 'external':
            skipped += 1
            continue

        # Find where to inject
        target_line = None

        if label['type'] == 'simple' and label['next_heading']:
            target_line = find_heading_line(md_path, label['next_heading'])
        elif label['type'] == 'reference' and label['target']:
            # Reference label points to another section heading
            target_slug = slugify(label['target'])
            # First check this file
            target_line = find_heading_line(md_path, label['target'])
            if not target_line:
                # Search ALL MD files for the target heading
                for other_md in DOCS_DIR.rglob("*.md"):
                    parts = other_md.relative_to(DOCS_DIR).parts
                    if any(p[0].isupper() for p in parts[:-1]):
                        continue
                    if other_md == md_path:
                        continue
                    other_line = find_heading_line(other_md, label['target'])
                    if other_line:
                        other_existing = get_existing_anchors(other_md)
                        if slug not in other_existing:
                            other_content = other_md.read_text(encoding="utf-8")
                            new_other = inject_anchor(other_content, slug, other_line)
                            if new_other != other_content and not dry_run:
                                other_md.write_text(new_other, encoding="utf-8")
                            if new_other != other_content:
                                injected += 1
                        else:
                            skipped += 1
                        target_line = None  # Don't inject in current file
                        break
                else:
                    skipped += 1
                continue

        if target_line:
            new_content = inject_anchor(content, slug, target_line)
            if new_content != content:
                content = new_content
                existing.add(slug)
                injected += 1
        else:
            skipped += 1

    if injected > 0 and not dry_run:
        md_path.write_text(content, encoding="utf-8")

    return injected, skipped


def process_master_labels(file_map: Dict[str, str], dry_run: bool = False) -> Tuple[int, int]:
    """Process labels from the master RobotFrameworkUserGuide.rst.

    The master file has labels that map to section entry points in sub-files.
    """
    master_rst = RST_SOURCE_DIR / "RobotFrameworkUserGuide.rst"
    if not master_rst.exists():
        return 0, 0

    labels = extract_rst_labels(master_rst)
    injected = 0
    skipped = 0

    # Build heading→file map from all MD files
    heading_to_file: Dict[str, str] = {}
    for md_rel in file_map.values():
        md_path = DOCS_DIR / md_rel
        if not md_path.exists():
            continue
        content = md_path.read_text(encoding="utf-8")
        for m in re.finditer(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE):
            heading_to_file[slugify(m.group(2))] = md_rel

    for label in labels:
        if label['type'] == 'external':
            skipped += 1
            continue

        slug = label['slug']

        # Try to find the target file
        target_file = None
        target_heading = label.get('next_heading') or label.get('target')

        if target_heading:
            target_slug = slugify(target_heading)
            if target_slug in heading_to_file:
                target_file = heading_to_file[target_slug]

        if label['type'] == 'reference' and label['target']:
            target_slug = slugify(label['target'])
            if target_slug in heading_to_file:
                target_file = heading_to_file[target_slug]

        if not target_file:
            skipped += 1
            continue

        md_path = DOCS_DIR / target_file
        existing = get_existing_anchors(md_path)

        if slug in existing:
            skipped += 1
            continue

        heading_text = target_heading or label['target']
        target_line = find_heading_line(md_path, heading_text)

        if target_line:
            content = md_path.read_text(encoding="utf-8")
            new_content = inject_anchor(content, slug, target_line)
            if new_content != content:
                if not dry_run:
                    md_path.write_text(new_content, encoding="utf-8")
                injected += 1
            else:
                skipped += 1
        else:
            skipped += 1

    return injected, skipped


def main():
    parser = argparse.ArgumentParser(
        description="Inject missing RST label anchors into Markdown files"
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview changes")
    parser.add_argument("--report", action="store_true", help="Show extraction stats")
    args = parser.parse_args()

    file_map = load_file_map()
    total_injected = 0
    total_skipped = 0

    print("Extracting RST labels from source files...")
    total_labels = 0
    for rst_file in file_map:
        rst_path = RST_SOURCE_DIR / rst_file
        if rst_path.exists():
            labels = extract_rst_labels(rst_path)
            total_labels += len(labels)
            if args.report and labels:
                print(f"  {rst_file}: {len(labels)} labels")
                for l in labels:
                    status = f"→ {l['next_heading']}" if l['next_heading'] else f"({l['type']})"
                    print(f"    {l['slug']:40s} {status}")

    # Process master file labels
    master_labels = extract_rst_labels(RST_SOURCE_DIR / "RobotFrameworkUserGuide.rst")
    total_labels += len(master_labels)
    print(f"  RobotFrameworkUserGuide.rst: {len(master_labels)} labels")

    print(f"\nTotal RST labels found: {total_labels}")
    print(f"\nInjecting anchors into MD files...")

    # Process per-file labels
    for rst_file, md_file in file_map.items():
        inj, skip = process_file(rst_file, md_file, file_map, {}, args.dry_run)
        total_injected += inj
        total_skipped += skip

    # Process master file labels
    inj, skip = process_master_labels(file_map, args.dry_run)
    total_injected += inj
    total_skipped += skip

    print(f"\nInjected {total_injected} anchor tags")
    print(f"Skipped {total_skipped} (already exist, external, or unresolvable)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
