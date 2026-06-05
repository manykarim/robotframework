#!/usr/bin/env python3
"""
Reorganize converter output from CamelCase RST structure to MkDocs lowercase structure.

convert.py outputs files mirroring the RST source layout:
    docs/CreatingTestData/Variables.md
    docs/ExecutingTestCases/BasicUsage.md

This script moves them to the MkDocs target layout:
    docs/creating-test-data/variables.md
    docs/executing-tests/basic-usage.md

Uses reference_map.json for known files. Unknown files (new in upstream) are
auto-mapped using CamelCase-to-kebab-case conversion.

This script is IDEMPOTENT - already-reorganized files are left untouched.

Usage:
    python reorganize.py              # Move files
    python reorganize.py --dry-run    # Preview moves
    python reorganize.py --report     # Show mapping details
"""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import yaml as _yaml

    class _NavLoader(_yaml.SafeLoader):
        pass

    # mkdocs.yml uses !!python/name: tags that SafeLoader rejects — ignore them
    _NavLoader.add_multi_constructor(
        'tag:yaml.org,2002:python/',
        lambda loader, tag_suffix, node: None,
    )

    def _yaml_load(stream):
        return _yaml.load(stream, Loader=_NavLoader)

    HAS_YAML = True
except ImportError:
    HAS_YAML = False


SCRIPT_DIR = Path(__file__).parent.resolve()
DOCS_DIR = SCRIPT_DIR.parent / "docs"
REFERENCE_MAP = SCRIPT_DIR / "reference_map.json"
MKDOCS_YML = SCRIPT_DIR.parent / "mkdocs.yml"


def load_mappings() -> Tuple[Dict[str, str], Dict[str, str]]:
    """Load file and section mappings from reference_map.json."""
    with open(REFERENCE_MAP, encoding="utf-8") as f:
        ref_map = json.load(f)
    file_map = {k: v for k, v in ref_map.get("rst_to_md_files", {}).items()
                if not k.startswith("_")}
    section_map = {k: v for k, v in ref_map.get("section_dirs", {}).items()
                   if not k.startswith("_")}
    return file_map, section_map


def load_section_intros() -> Dict[str, str]:
    """Load section intro paragraphs from reference_map.json."""
    with open(REFERENCE_MAP, encoding="utf-8") as f:
        ref_map = json.load(f)
    return ref_map.get("section_intros", {})


def load_nav_section_title(section_dir: str) -> str:
    """Return the nav section title for section_dir (e.g. 'Extending Robot Framework').

    Falls back to title-cased dir name if PyYAML unavailable or section not found.
    """
    fallback = section_dir.replace("-", " ").title()
    if not HAS_YAML or not MKDOCS_YML.exists():
        return fallback

    with open(MKDOCS_YML, encoding="utf-8") as f:
        config = _yaml_load(f)

    nav = config.get("nav", [])
    for section in nav:
        if not isinstance(section, dict):
            continue
        for title, entries in section.items():
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if isinstance(entry, str) and entry.startswith(f"{section_dir}/"):
                    return title
                if isinstance(entry, dict):
                    for _, path in entry.items():
                        if isinstance(path, str) and path.startswith(f"{section_dir}/"):
                            return title
    return fallback


def load_nav_children(section_dir: str) -> List[Tuple[str, str]]:
    """Return [(title, relative_path), ...] for non-index nav entries under section_dir.

    Reads mkdocs.yml nav to get titles and ordering.  Falls back to an empty
    list if PyYAML is not available or the section is not found in the nav.
    """
    if not HAS_YAML or not MKDOCS_YML.exists():
        return []

    with open(MKDOCS_YML, encoding="utf-8") as f:
        config = _yaml_load(f)

    nav = config.get("nav", [])
    children = []

    for section in nav:
        if not isinstance(section, dict):
            continue
        for _title, entries in section.items():
            if not isinstance(entries, list):
                continue
            # Check whether this section matches section_dir by inspecting
            # the first entry path prefix
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                for title, path in entry.items():
                    if not isinstance(path, str):
                        continue
                    if path.startswith(f"{section_dir}/") and not path.endswith("index.md"):
                        children.append((title, path.split("/", 1)[1]))
                    elif path.startswith(f"{section_dir}/") and path.endswith("index.md"):
                        # This section matches — collect all non-index children
                        children = []
                        for child in entries:
                            if not isinstance(child, dict):
                                continue
                            for ctitle, cpath in child.items():
                                if isinstance(cpath, str) and not cpath.endswith("index.md"):
                                    children.append((ctitle, cpath.split("/", 1)[1]))
                        return children
    return children


def build_index_content(section_dir: str, title: str,
                        intros: Dict[str, str]) -> str:
    """Build the full content for a section index.md."""
    lines = [f"# {title}", ""]

    intro = intros.get(section_dir)
    if intro:
        lines.append(intro)
        lines.append("")

    children = load_nav_children(section_dir)
    if children:
        lines.append("## In this section")
        lines.append("")
        for ctitle, cpath in children:
            lines.append(f"- [{ctitle}]({cpath})")
        lines.append("")

    return "\n".join(lines)


def camel_to_kebab(name: str) -> str:
    """Convert CamelCase to kebab-case: DynamicLibraryAPI → dynamic-library-api."""
    # Insert hyphen before uppercase letters that follow lowercase
    s = re.sub(r'([a-z])([A-Z])', r'\1-\2', name)
    # Insert hyphen before uppercase letters that are followed by lowercase (for acronyms)
    s = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1-\2', s)
    return s.lower()


def reorganize(dry_run: bool = False, report: bool = False) -> Tuple[int, int, List[str]]:
    """Move CamelCase files to MkDocs lowercase structure.

    Returns (moved_count, created_index_count, unmapped_files)
    """
    file_map, section_map = load_mappings()
    intros = load_section_intros()
    moved = 0
    created_indexes = 0
    unmapped = []

    # Step 1: Move known files using reference_map
    for rst_rel, md_rel in file_map.items():
        camel_md = rst_rel.replace(".rst", ".md")
        src = DOCS_DIR / camel_md
        dst = DOCS_DIR / md_rel

        if not src.exists():
            continue
        if dst.exists():
            if report:
                print(f"  SKIP (exists): {md_rel}")
            continue

        dst.parent.mkdir(parents=True, exist_ok=True)
        if dry_run:
            print(f"  MOVE: {camel_md} → {md_rel}")
        else:
            shutil.move(str(src), str(dst))
        moved += 1

    # Step 2: Handle unmapped CamelCase files (new in upstream)
    for camel_dir in sorted(DOCS_DIR.iterdir()):
        if not camel_dir.is_dir() or not camel_dir.name[0].isupper():
            continue

        md_dir = section_map.get(camel_dir.name)
        if not md_dir:
            # Unknown section - report but don't crash
            for f in camel_dir.glob("*.md"):
                unmapped.append(f"{camel_dir.name}/{f.name}")
            continue

        target_dir = DOCS_DIR / md_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        for md_file in sorted(camel_dir.glob("*.md")):
            kebab_name = camel_to_kebab(md_file.stem) + ".md"
            dst = target_dir / kebab_name

            if dst.exists():
                if report:
                    print(f"  SKIP (exists): {md_dir}/{kebab_name}")
                continue

            if dry_run:
                print(f"  MOVE (auto): {camel_dir.name}/{md_file.name} → {md_dir}/{kebab_name}")
            else:
                shutil.move(str(md_file), str(dst))
            moved += 1

    # Step 3: Create section index pages with intro paragraph and child TOC
    for section_md in section_map.values():
        idx = DOCS_DIR / section_md / "index.md"
        if not idx.exists():
            title = load_nav_section_title(section_md)
            if not dry_run:
                idx.parent.mkdir(parents=True, exist_ok=True)
                idx.write_text(build_index_content(section_md, title, intros),
                               encoding="utf-8")
            created_indexes += 1
            if dry_run or report:
                print(f"  CREATE: {section_md}/index.md")

    # Step 4: Clean up empty CamelCase directories
    for d in sorted(DOCS_DIR.iterdir()):
        if d.is_dir() and d.name[0].isupper():
            remaining = list(d.glob("*"))
            if not remaining:
                if not dry_run:
                    d.rmdir()
                if report:
                    print(f"  RMDIR: {d.name}/")
            else:
                for f in remaining:
                    unmapped.append(f"{d.name}/{f.name}")

    # Step 5: Clean up CamelCase master file
    master = DOCS_DIR / "RobotFrameworkUserGuide.md"
    if master.exists():
        if not dry_run:
            master.unlink()
        if report:
            print(f"  DELETE: RobotFrameworkUserGuide.md")

    return moved, created_indexes, unmapped


def main():
    parser = argparse.ArgumentParser(
        description="Reorganize CamelCase converter output to MkDocs lowercase structure"
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview moves")
    parser.add_argument("--report", action="store_true", help="Show details")
    args = parser.parse_args()

    print("Reorganizing converter output to MkDocs structure...")
    moved, indexes, unmapped = reorganize(args.dry_run, args.report)

    print(f"\nMoved: {moved} files")
    print(f"Created: {indexes} index pages")
    if unmapped:
        print(f"Unmapped: {len(unmapped)} files (add to reference_map.json):")
        for f in unmapped:
            print(f"  {f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
