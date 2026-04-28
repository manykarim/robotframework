#!/usr/bin/env python3
"""
Fix incorrectly converted RST anonymous references in Markdown files.

RST anonymous references use `text`__ paired with __ URL targets. During
conversion, many of these were turned into (#slug) self-links instead of
their actual external URL or cross-reference targets.

This script:
1. Parses each RST source file to extract anonymous reference pairs
2. Maps them to the converted MD files
3. Rewrites (#slug) links back to the correct target URLs

This is IDEMPOTENT - already-correct links are not modified.

Usage:
    python fix_anonymous_refs.py              # Fix all files
    python fix_anonymous_refs.py --dry-run    # Preview changes
    python fix_anonymous_refs.py --report     # Show extraction stats
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


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
    """Load RST→MD file mapping."""
    with open(REFERENCE_MAP, encoding="utf-8") as f:
        ref_map = json.load(f)
    return {k: v for k, v in ref_map.get("rst_to_md_files", {}).items()
            if not k.startswith("_")}


def extract_anonymous_pairs(rst_file: Path) -> List[Tuple[str, str]]:
    """Extract anonymous reference text and target pairs from RST file.

    RST anonymous references are matched in document order:
    - `text`__ is the reference (double underscore)
    - __ URL or __ `Section`_ is the target

    Returns [(reference_text, target_url_or_section), ...]
    """
    content = rst_file.read_text(encoding="utf-8")

    # Extract all anonymous references in order
    refs = []
    for m in re.finditer(r'`([^`]+)`__', content):
        refs.append((m.start(), m.group(1).strip()))

    # Extract all anonymous targets in order
    targets = []
    for m in re.finditer(r'^[ \t]*__\s+(.+)$', content, re.MULTILINE):
        target = m.group(1).strip()
        targets.append((m.start(), target))

    # Pair them in document order
    pairs = []
    for i, (ref_pos, ref_text) in enumerate(refs):
        if i < len(targets):
            _, target = targets[i]
            pairs.append((ref_text, target))

    return pairs


def resolve_target(target: str, rst_file: Path, file_map: Dict[str, str]) -> Optional[str]:
    """Resolve an anonymous target to a URL or MD path.

    Target can be:
    - External URL: http://... or https://...
    - RST cross-ref: `Section Name`_ or SectionName_
    - RST label ref: `label name`_
    """
    # External URL
    if target.startswith('http://') or target.startswith('https://'):
        return target

    # RST cross-reference: `Section Name`_ or Name_
    m = re.match(r'`([^`]+)`_$', target)
    if m:
        section_name = m.group(1)
        return resolve_section_ref(section_name, rst_file, file_map)

    m = re.match(r'(\w[\w\s-]*)_$', target)
    if m:
        section_name = m.group(1)
        return resolve_section_ref(section_name, rst_file, file_map)

    return None


def resolve_section_ref(section_name: str, rst_file: Path, file_map: Dict[str, str]) -> Optional[str]:
    """Resolve a section name reference to an MD file path + anchor."""
    section_slug = slugify(section_name)

    # Search all MD files for this heading
    for md_rel in file_map.values():
        md_path = DOCS_DIR / md_rel
        if not md_path.exists():
            continue

        content = md_path.read_text(encoding="utf-8")
        for line in content.split('\n'):
            m = re.match(r'^(#{1,6})\s+(.+)$', line)
            if m and slugify(m.group(2)) == section_slug:
                return md_rel + '#' + section_slug

            # Also check <a id="..."> tags
            for am in re.finditer(r'<a\s+id="([^"]+)"', line):
                if slugify(am.group(1)) == section_slug:
                    return md_rel + '#' + section_slug

    return None


def fix_anonymous_refs_in_file(
    rst_file: str,
    md_file: str,
    file_map: Dict[str, str],
    dry_run: bool = False
) -> Tuple[int, int, List[str]]:
    """Fix anonymous references in a single MD file using RST source data."""
    rst_path = RST_SOURCE_DIR / rst_file
    md_path = DOCS_DIR / md_file

    if not rst_path.exists() or not md_path.exists():
        return 0, 0, []

    pairs = extract_anonymous_pairs(rst_path)
    if not pairs:
        return 0, 0, []

    md_content = md_path.read_text(encoding="utf-8")
    md_dir = str(Path(md_file).parent)
    fixed = 0
    skipped = 0
    details = []

    for ref_text, target in pairs:
        ref_slug = slugify(ref_text)

        # Check if this reference exists as a broken (#slug) link in the MD
        broken_pattern = f'[{ref_text}](#{ref_slug})'
        if broken_pattern not in md_content:
            # Also try with different text casing
            found = False
            for m in re.finditer(re.escape(f'](#{ref_slug})'), md_content):
                # Found a link to this slug
                found = True
                break
            if not found:
                skipped += 1
                continue

        # Resolve the target
        resolved = resolve_target(target, rst_path, file_map)
        if not resolved:
            skipped += 1
            details.append(f"  SKIP: [{ref_text}](#{ref_slug}) → target '{target}' unresolvable")
            continue

        # Build the replacement link
        if resolved.startswith('http'):
            new_link = f'[{ref_text}]({resolved})'
        else:
            resolved_file = resolved.split('#')[0]
            anchor = '#' + resolved.split('#')[1] if '#' in resolved else ''
            # If target is in the same file, use just the anchor
            if resolved_file == md_file:
                new_link = f'[{ref_text}]({anchor})'
            else:
                rel_path = os.path.relpath(resolved_file, md_dir)
                rel_path = rel_path.replace(os.sep, '/')
                new_link = f'[{ref_text}]({rel_path}{anchor})'

        # Replace in content
        if broken_pattern in md_content:
            md_content = md_content.replace(broken_pattern, new_link, 1)
            fixed += 1
            details.append(f"  FIX: #{ref_slug} → {resolved[:60]}")
        else:
            # Try regex for case variations
            pattern = re.compile(
                re.escape(f'](#{ref_slug})'),
                re.IGNORECASE
            )
            # Use the same resolved link as above
            resolved_file = resolved.split('#')[0]
            anchor_part = '#' + resolved.split('#')[1] if '#' in resolved else ''
            if resolved.startswith('http'):
                repl_target = resolved
            elif resolved_file == md_file:
                repl_target = anchor_part
            else:
                rp = os.path.relpath(resolved_file, md_dir).replace(os.sep, '/')
                repl_target = rp + anchor_part
            new_md, count = pattern.subn(f']({repl_target})', md_content, count=1)
            if count > 0:
                md_content = new_md
                fixed += 1
                details.append(f"  FIX: #{ref_slug} → {resolved[:60]} (regex)")
            else:
                skipped += 1

    if fixed > 0 and not dry_run:
        md_path.write_text(md_content, encoding="utf-8")

    return fixed, skipped, details


def main():
    parser = argparse.ArgumentParser(
        description="Fix incorrectly converted RST anonymous references"
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview changes")
    parser.add_argument("--report", action="store_true", help="Show details")
    args = parser.parse_args()

    file_map = load_file_map()
    total_fixed = 0
    total_skipped = 0

    print("Extracting RST anonymous reference pairs...")
    total_pairs = 0
    for rst_file in file_map:
        rst_path = RST_SOURCE_DIR / rst_file
        if rst_path.exists():
            pairs = extract_anonymous_pairs(rst_path)
            total_pairs += len(pairs)
            if args.report and pairs:
                print(f"  {rst_file}: {len(pairs)} anonymous refs")

    # Also check master file
    master = RST_SOURCE_DIR / "RobotFrameworkUserGuide.rst"
    if master.exists():
        master_pairs = extract_anonymous_pairs(master)
        total_pairs += len(master_pairs)
        if args.report:
            print(f"  RobotFrameworkUserGuide.rst: {len(master_pairs)} anonymous refs")

    print(f"Total anonymous reference pairs: {total_pairs}")
    print(f"\nFixing broken anonymous references in MD files...")

    for rst_file, md_file in file_map.items():
        fixed, skipped, details = fix_anonymous_refs_in_file(
            rst_file, md_file, file_map, args.dry_run
        )
        total_fixed += fixed
        total_skipped += skipped

        if (fixed > 0 or (args.report and details)):
            rel = md_file
            print(f"  {rel}: {fixed} fixed, {skipped} skipped")
            if args.report:
                for d in details:
                    print(f"    {d}")

    print(f"\nFixed {total_fixed} anonymous references")
    print(f"Skipped {total_skipped}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
