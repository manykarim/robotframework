#!/usr/bin/env python3
"""
Detect RST source changes relative to the conversion reference map.

Compares the actual RST source file inventory against reference_map.json to find:
  - NEW files: RST files that exist but aren't in the map
  - REMOVED files: Map entries whose RST source no longer exists
  - CHANGED sections: New directories not in section_dirs

Can auto-update reference_map.json with new entries.

Usage:
    python detect_changes.py                  # Report changes
    python detect_changes.py --update         # Auto-update reference_map.json
    python detect_changes.py --update-nav     # Also suggest mkdocs.yml nav updates
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_DIR = SCRIPT_DIR.parent
RST_SOURCE_DIR = PROJECT_DIR.parent / "userguide" / "src"
REFERENCE_MAP = SCRIPT_DIR / "reference_map.json"


def camel_to_kebab(name: str) -> str:
    """Convert CamelCase to kebab-case."""
    s = re.sub(r'([a-z])([A-Z])', r'\1-\2', name)
    s = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1-\2', s)
    return s.lower()


def detect() -> Tuple[List[dict], List[str], List[str]]:
    """Detect changes between RST source and reference map.

    Returns (new_files, removed_files, new_sections).
    Each new_file is {rst: path, suggested_md: path, section: name}.
    """
    with open(REFERENCE_MAP, encoding="utf-8") as f:
        ref_map = json.load(f)

    file_map = {k: v for k, v in ref_map.get("rst_to_md_files", {}).items()
                if not k.startswith("_")}
    section_map = {k: v for k, v in ref_map.get("section_dirs", {}).items()
                   if not k.startswith("_")}

    # Discover all RST files in source
    rst_files = set()
    rst_sections = set()
    for rst_file in RST_SOURCE_DIR.rglob("*.rst"):
        rel = str(rst_file.relative_to(RST_SOURCE_DIR))
        if "/" in rel:
            section = rel.split("/")[0]
            rst_sections.add(section)
        # Skip the master file and utility files
        if rst_file.name in ("RobotFrameworkUserGuide.rst", "roles.rst", "version.rst"):
            continue
        # Skip INSTALL.rst (dynamically copied)
        if rst_file.name == "INSTALL.rst":
            continue
        rst_files.add(rel)

    known_rst = set(file_map.keys())

    # Find new files
    new_files = []
    for rst_rel in sorted(rst_files - known_rst):
        parts = rst_rel.split("/")
        if len(parts) == 2:
            section_rst = parts[0]
            filename_rst = parts[1]
            section_md = section_map.get(section_rst, camel_to_kebab(section_rst))
            filename_md = camel_to_kebab(filename_rst.replace(".rst", "")) + ".md"
            md_rel = f"{section_md}/{filename_md}"
        else:
            md_rel = camel_to_kebab(rst_rel.replace(".rst", "")) + ".md"

        new_files.append({
            "rst": rst_rel,
            "suggested_md": md_rel,
            "section": parts[0] if len(parts) == 2 else "",
        })

    # Find removed files
    removed = []
    for rst_rel in sorted(known_rst):
        rst_path = RST_SOURCE_DIR / rst_rel
        if not rst_path.exists():
            removed.append(rst_rel)

    # Find new sections
    known_sections = set(section_map.keys())
    new_sections = sorted(rst_sections - known_sections)

    return new_files, removed, new_sections


def update_reference_map(new_files: List[dict], removed: List[str]):
    """Auto-update reference_map.json with detected changes."""
    with open(REFERENCE_MAP, encoding="utf-8") as f:
        ref_map = json.load(f)

    changes = 0

    # Add new files
    for nf in new_files:
        ref_map["rst_to_md_files"][nf["rst"]] = nf["suggested_md"]
        changes += 1

    # Mark removed files (don't delete - add a comment)
    for rm in removed:
        if rm in ref_map["rst_to_md_files"]:
            md_path = ref_map["rst_to_md_files"][rm]
            del ref_map["rst_to_md_files"][rm]
            # Store in a removed section for reference
            if "_removed_files" not in ref_map:
                ref_map["_removed_files"] = {}
            ref_map["_removed_files"][rm] = md_path
            changes += 1

    if changes > 0:
        with open(REFERENCE_MAP, "w", encoding="utf-8") as f:
            json.dump(ref_map, f, indent=2)

    # Also patch mkdocs.yml to remove nav entries for deleted files
    mkdocs_yml = PROJECT_DIR / "mkdocs.yml"
    if mkdocs_yml.exists() and removed:
        content = mkdocs_yml.read_text(encoding="utf-8")
        original = content
        for rm in removed:
            if rm in ref_map.get("_removed_files", {}):
                md_path = ref_map["_removed_files"][rm]
            else:
                md_path = rm.replace(".rst", ".md")
            # Remove nav lines referencing this file
            lines = content.split("\n")
            content = "\n".join(
                l for l in lines if md_path not in l
            )
        if content != original:
            mkdocs_yml.write_text(content, encoding="utf-8")
            changes += 1

    return changes


def main():
    parser = argparse.ArgumentParser(
        description="Detect RST source changes relative to reference map"
    )
    parser.add_argument("--update", action="store_true",
                        help="Auto-update reference_map.json")
    parser.add_argument("--update-nav", action="store_true",
                        help="Also suggest mkdocs.yml nav updates")
    args = parser.parse_args()

    if not RST_SOURCE_DIR.exists():
        print(f"ERROR: RST source not found: {RST_SOURCE_DIR}")
        return 1

    new_files, removed, new_sections = detect()

    print(f"RST source: {RST_SOURCE_DIR}")
    print(f"Reference:  {REFERENCE_MAP}")
    print()

    if not new_files and not removed and not new_sections:
        print("No changes detected. Reference map is up to date.")
        return 0

    if new_files:
        print(f"NEW files ({len(new_files)}):")
        for nf in new_files:
            print(f"  + {nf['rst']}")
            print(f"    → {nf['suggested_md']}")

    if removed:
        print(f"\nREMOVED files ({len(removed)}):")
        for rm in removed:
            print(f"  - {rm}")

    if new_sections:
        print(f"\nNEW sections ({len(new_sections)}):")
        for ns in new_sections:
            print(f"  + {ns} → {camel_to_kebab(ns)}/")

    if args.update:
        changes = update_reference_map(new_files, removed)
        print(f"\nUpdated reference_map.json: {changes} changes")

    if args.update_nav and new_files:
        print("\nSuggested mkdocs.yml nav additions:")
        for nf in new_files:
            parts = nf["suggested_md"].split("/")
            title = parts[-1].replace(".md", "").replace("-", " ").title()
            section = parts[0].replace("-", " ").title()
            print(f"  Under '{section}':")
            print(f"    - {title}: {nf['suggested_md']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
