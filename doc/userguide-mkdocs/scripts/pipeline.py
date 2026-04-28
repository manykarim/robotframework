#!/usr/bin/env python3
"""
Reusable RST → MkDocs Markdown conversion pipeline for Robot Framework User Guide.

This is the MASTER ORCHESTRATOR. Run it to regenerate all Markdown documentation
from the RST source files. The output is a complete, clean MkDocs site.

Usage:
    python pipeline.py                     # Full conversion from scratch
    python pipeline.py --skip-convert      # Re-run only post-processing fixes
    python pipeline.py --validate-only     # Only run validation (no conversion)
    python pipeline.py --dry-run           # Show what would be done

The pipeline stages are:
    1. CLEAN   - Remove old generated output
    2. CONVERT - RST → raw Markdown via convert.py
    3. FIX     - Apply all post-processing fix scripts
    4. ASSETS  - Copy images and static files
    5. VALIDATE - Build MkDocs and check for errors
"""

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Tuple


# Resolve directories
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_DIR = SCRIPT_DIR.parent
DOCS_DIR = PROJECT_DIR / "docs"
RST_SOURCE_DIR = PROJECT_DIR.parent / "userguide" / "src"
REFERENCE_MAP = SCRIPT_DIR / "reference_map.json"


def load_reference_map() -> dict:
    """Load the data-driven reference mappings."""
    with open(REFERENCE_MAP, encoding="utf-8") as f:
        return json.load(f)


def run_script(script_name: str, args: list = None, dry_run: bool = False) -> Tuple[int, str]:
    """Run a post-processing script and return (exit_code, output)."""
    script_path = SCRIPT_DIR / script_name
    if not script_path.exists():
        return 1, f"Script not found: {script_path}"

    cmd = [sys.executable, str(script_path)] + (args or [])
    label = f"  → {script_name}"

    if dry_run:
        print(f"{label} [DRY RUN] would run: {' '.join(cmd)}")
        return 0, ""

    print(f"{label} ...", end=" ", flush=True)
    start = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(SCRIPT_DIR))
    elapsed = time.time() - start

    if result.returncode == 0:
        print(f"OK ({elapsed:.1f}s)")
    else:
        print(f"FAILED ({elapsed:.1f}s)")
        if result.stderr:
            print(f"    stderr: {result.stderr[:500]}")

    return result.returncode, result.stdout + result.stderr


def stage_clean(dry_run: bool = False):
    """Stage 1: Clean output directory (preserve structure)."""
    print("\n[1/5] CLEAN - Removing old generated Markdown files")

    if dry_run:
        print("  → [DRY RUN] Would remove all .md files from docs/")
        return

    # Remove generated .md files but keep directory structure and static assets
    # Preserve hand-authored top-level pages (docs/index.md) — the converter has
    # no RST source for these so re-cleaning them would orphan the nav.
    preserved_top_level = {"index.md"}
    count = 0
    for md_file in DOCS_DIR.rglob("*.md"):
        # Skip files in CamelCase directories (legacy, should not exist)
        parts = md_file.relative_to(DOCS_DIR).parts
        if any(p[0].isupper() for p in parts[:-1]):
            continue
        if len(parts) == 1 and parts[0] in preserved_top_level:
            continue
        md_file.unlink()
        count += 1

    print(f"  → Removed {count} generated .md files")


def stage_convert(dry_run: bool = False):
    """Stage 2: Convert RST to raw Markdown."""
    print("\n[2/5] CONVERT - RST → raw Markdown")

    if not RST_SOURCE_DIR.exists():
        print(f"  ERROR: RST source directory not found: {RST_SOURCE_DIR}")
        return False

    ref_map = load_reference_map()

    # Step 2a: Detect upstream changes (new/removed RST files)
    code, output = run_script("detect_changes.py", ["--update"], dry_run)

    # Step 2b: Run the RST-to-MD converter
    code, output = run_script("convert.py", [], dry_run)
    if code != 0:
        print(f"  WARNING: convert.py returned code {code}")
        # Try the alternative converter
        code2, output2 = run_script("convert_rst_to_md.py", [], dry_run)
        if code2 != 0:
            print(f"  ERROR: Both converters failed.")
            return False

    # Step 2c: Reorganize CamelCase output to MkDocs lowercase structure
    code, output = run_script("reorganize.py", [], dry_run)
    if code != 0:
        print(f"  WARNING: reorganize.py had issues (code {code})")

    # Step 2d: Split combined pages per reference_map.json `split_pages` config
    code, output = run_script("split_pages.py", [], dry_run)
    if code != 0:
        print(f"  WARNING: split_pages.py had issues (code {code})")

    return True


def stage_fix(dry_run: bool = False):
    """Stage 3: Apply all post-processing fix scripts in order."""
    print("\n[3/5] FIX - Applying post-processing fixes")

    # Fix scripts in dependency order - each is idempotent
    fix_scripts = [
        ("fix_image_paths.py",      "Fix CamelCase image paths to section-local"),
        ("fix_admonitions.py",      "Fix admonition formatting"),
        ("fix_rst_syntax.py",       "Convert RST labels, link defs, anonymous links"),
        ("fix_definition_lists.py", "Convert RST def-lists to Material def_list syntax"),
        ("fix_tables.py",           "Fix table formatting"),
        ("fix_links.py",            "Fix API refs and internal cross-references"),
        ("fix_cross_file_links.py", "Fix cross-file anchor references"),
        ("fix_anchors.py",          "Fix and validate anchor links"),
        ("fix_anonymous_refs.py",   "Fix anonymous RST references using RST source pairing"),
        ("fix_file_references.py",  "Fix wrong filenames in generated links"),
        ("fix_missing_anchors.py",  "Inject RST label anchors from source"),
        ("fix_cross_page_anchors.py", "Resolve cross-page #anchor references"),
        ("fix_missing_anchors.py",  "Re-inject after cross-page resolution"),
        ("fix_cross_page_anchors.py", "Final cross-page anchor pass"),
        ("fix_anchor_corrections.py", "Apply data-driven anchor corrections"),
        ("fix_bare_refs.py",        "Convert bare Word_ RST references (runs late)"),
        ("fix_code_blocks.py",      "Fix code block syntax (runs late to catch post-fix artifacts)"),
        ("fix_bare_refs.py",        "Final bare ref cleanup pass"),
        ("add_legacy_anchors.py",   "Add legacy anchor compatibility"),
    ]

    failed = []
    for script, description in fix_scripts:
        script_path = SCRIPT_DIR / script
        if not script_path.exists():
            print(f"  → {script} [SKIP - not found] ({description})")
            continue

        code, output = run_script(script, [], dry_run)
        if code != 0:
            failed.append(script)

    if failed:
        print(f"\n  WARNING: {len(failed)} fix scripts had issues: {', '.join(failed)}")
    else:
        print(f"\n  All fix scripts completed successfully")

    return len(failed) == 0


def stage_assets(dry_run: bool = False):
    """Stage 4: Copy images and static assets from RST source."""
    print("\n[4/5] ASSETS - Copying images and static files")

    ref_map = load_reference_map()
    copied = 0

    # Image extensions to copy
    img_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico'}

    for section_rst, section_md in ref_map.get("section_dirs", {}).items():
        if section_rst.startswith("_"):
            continue

        src_dir = RST_SOURCE_DIR / section_rst
        dst_dir = DOCS_DIR / section_md

        if not src_dir.exists():
            continue

        dst_dir.mkdir(parents=True, exist_ok=True)

        for src_file in src_dir.iterdir():
            if src_file.suffix.lower() in img_extensions:
                dst_file = dst_dir / src_file.name
                if dry_run:
                    print(f"  → [DRY RUN] Would copy {src_file.name} to {section_md}/")
                else:
                    shutil.copy2(src_file, dst_file)
                    copied += 1

    if not dry_run:
        print(f"  → Copied {copied} image files")


def stage_validate(dry_run: bool = False) -> Tuple[int, int]:
    """Stage 5: Validate the generated site."""
    print("\n[5/5] VALIDATE - Building and checking MkDocs site")

    if dry_run:
        print("  → [DRY RUN] Would run mkdocs build --strict")
        return 0, 0

    # Non-strict build first
    print("  → Non-strict build ...", end=" ", flush=True)
    start = time.time()
    result = subprocess.run(
        [sys.executable, "-m", "mkdocs", "build"],
        capture_output=True, text=True, cwd=str(PROJECT_DIR)
    )
    elapsed = time.time() - start

    if result.returncode == 0:
        print(f"PASS ({elapsed:.1f}s)")
    else:
        print(f"FAIL ({elapsed:.1f}s)")
        print(f"    {result.stderr[:500]}")
        return -1, -1

    # Count INFO-level warnings (broken anchors)
    info_warnings = sum(1 for line in result.stderr.split('\n')
                        if 'INFO' in line and 'contains a link' in line)

    # Strict build
    print("  → Strict build ...", end=" ", flush=True)
    start = time.time()
    result_strict = subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "--strict"],
        capture_output=True, text=True, cwd=str(PROJECT_DIR)
    )
    elapsed = time.time() - start

    strict_warnings = sum(1 for line in result_strict.stderr.split('\n')
                          if 'WARNING' in line)

    if result_strict.returncode == 0:
        print(f"PASS ({elapsed:.1f}s)")
    else:
        print(f"FAIL - {strict_warnings} warnings ({elapsed:.1f}s)")

    # V1-V12 conversion-quality validators (issues #2, #3, #6, #7, #8, #9)
    print("  → Conversion validators (V1-V12) ...", end=" ", flush=True)
    start = time.time()
    result_v = subprocess.run(
        [sys.executable, "scripts/validate.py", "--strict-conversion"],
        capture_output=True, text=True, cwd=str(PROJECT_DIR)
    )
    elapsed = time.time() - start
    if result_v.returncode == 0:
        print(f"PASS ({elapsed:.1f}s)")
    else:
        print(f"FAIL ({elapsed:.1f}s)")
        for line in result_v.stdout.split('\n'):
            if line.strip().startswith('V') or 'FAIL' in line or 'PASS' in line:
                print(f"    {line}")
        strict_warnings += 1  # surface as overall failure

    return strict_warnings, info_warnings


def print_summary(strict_warnings: int, info_warnings: int, elapsed: float):
    """Print final pipeline summary."""
    print("\n" + "=" * 60)
    print("PIPELINE SUMMARY")
    print("=" * 60)
    print(f"  Total time:        {elapsed:.1f}s")
    print(f"  Strict warnings:   {strict_warnings}")
    print(f"  Broken anchors:    {info_warnings}")

    if strict_warnings == 0 and info_warnings == 0:
        print(f"  Status:            ✓ PERFECT")
    elif strict_warnings == 0:
        print(f"  Status:            ✓ PASS (strict build clean)")
    else:
        print(f"  Status:            ✗ NEEDS WORK")

    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Reusable RST→MkDocs conversion pipeline for Robot Framework User Guide"
    )
    parser.add_argument("--skip-convert", action="store_true",
                        help="Skip conversion, only run post-processing fixes")
    parser.add_argument("--skip-clean", action="store_true",
                        help="Skip cleaning output directory")
    parser.add_argument("--validate-only", action="store_true",
                        help="Only run validation (no conversion or fixes)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be done without making changes")
    parser.add_argument("--fix-only", action="store_true",
                        help="Only run fix scripts (no conversion, no validation)")
    args = parser.parse_args()

    start_time = time.time()
    print("Robot Framework User Guide - RST→MkDocs Conversion Pipeline")
    print(f"  RST source: {RST_SOURCE_DIR}")
    print(f"  MD output:  {DOCS_DIR}")
    print(f"  Ref map:    {REFERENCE_MAP}")

    if args.validate_only:
        strict_w, info_w = stage_validate(args.dry_run)
        print_summary(strict_w, info_w, time.time() - start_time)
        sys.exit(0 if strict_w == 0 else 1)

    if not args.skip_clean and not args.fix_only:
        stage_clean(args.dry_run)

    if not args.skip_convert and not args.fix_only:
        if not stage_convert(args.dry_run):
            print("\nERROR: Conversion failed. Aborting pipeline.")
            sys.exit(2)

    stage_fix(args.dry_run)

    if not args.fix_only:
        stage_assets(args.dry_run)
        strict_w, info_w = stage_validate(args.dry_run)
        print_summary(strict_w, info_w, time.time() - start_time)
        sys.exit(0 if strict_w == 0 else 1)
    else:
        print(f"\n  Fix-only mode complete ({time.time() - start_time:.1f}s)")


if __name__ == "__main__":
    main()
