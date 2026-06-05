#!/usr/bin/env python3
"""Copy generated MkDocs content into a local checkout of pekkaklarck/manual.

Usage:
    python publish_to_manual.py --manual-dir /path/to/manual

The script reads manual_file_map.json (alongside this file), copies each
mapped source file from doc/userguide-mkdocs/docs/ to the corresponding
target path under <manual-dir>/doc/manual/docs/, and prints a summary.
"""

import argparse
import json
import shutil
import sys
from pathlib import Path


def load_map(scripts_dir: Path) -> dict:
    map_path = scripts_dir / "manual_file_map.json"
    with map_path.open() as f:
        data = json.load(f)
    return data["files"]


def publish(docs_dir: Path, manual_docs_dir: Path, file_map: dict) -> int:
    copied = []
    skipped = []

    for src_rel, dst_rel in file_map.items():
        src = docs_dir / src_rel
        dst = manual_docs_dir / dst_rel

        if not src.exists():
            print(f"  WARNING: source not found, skipping: {src_rel}", file=sys.stderr)
            skipped.append(src_rel)
            continue

        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied.append(f"  {src_rel} -> {dst_rel}")

    print(f"\n{'='*60}")
    print(f"Copied : {len(copied)} file(s)")
    if copied:
        for line in copied:
            print(line)
    print(f"\nSkipped: {len(skipped)} file(s)")
    if skipped:
        for path in skipped:
            print(f"  {path}")
    print('='*60)

    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--manual-dir",
        required=True,
        type=Path,
        help="Path to a local checkout of pekkaklarck/manual",
    )
    args = parser.parse_args()

    scripts_dir = Path(__file__).parent
    docs_dir = scripts_dir.parent / "docs"
    manual_docs_dir = args.manual_dir / "doc" / "manual" / "docs"

    if not docs_dir.is_dir():
        print(f"ERROR: docs directory not found: {docs_dir}", file=sys.stderr)
        return 1

    if not manual_docs_dir.is_dir():
        print(f"ERROR: manual docs directory not found: {manual_docs_dir}", file=sys.stderr)
        print("       Is --manual-dir pointing to the root of a pekkaklarck/manual checkout?", file=sys.stderr)
        return 1

    file_map = load_map(scripts_dir)
    print(f"Source : {docs_dir}")
    print(f"Target : {manual_docs_dir}")
    print(f"Entries: {len(file_map)}")

    return publish(docs_dir, manual_docs_dir, file_map)


if __name__ == "__main__":
    sys.exit(main())
