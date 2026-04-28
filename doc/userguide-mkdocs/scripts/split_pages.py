#!/usr/bin/env python3
"""
Split a single converted Markdown file into multiple files at H2 boundaries.

Driven by the ``split_pages`` block in ``reference_map.json``. Each split entry
slices the source MD from a specified ``## <heading>`` to the next configured
H2 (or EOF), promotes that H2 to an ``# <h1_title>`` and writes it to
``target`` under ``docs/``.

A side-file ``scripts/split_redirects.json`` records the anchor redirect
mapping so downstream scripts (``fix_cross_page_anchors.py``,
``fix_anchor_corrections.py``) can rewrite stale cross-page anchors. Each H3
inside a split section becomes its own redirect entry.

This script is IDEMPOTENT and DATA-DRIVEN. To split additional pages, add
entries to ``reference_map.json``'s ``split_pages`` block instead of editing
this script.

Usage:
    python split_pages.py              # Apply splits
    python split_pages.py --dry-run    # Preview without writing files
    python split_pages.py --report     # Verbose summary
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


SCRIPT_DIR = Path(__file__).parent.resolve()
DOCS_DIR = SCRIPT_DIR.parent / "docs"
REFERENCE_MAP = SCRIPT_DIR / "reference_map.json"
REDIRECTS_FILE = SCRIPT_DIR / "split_redirects.json"


# ---------------------------------------------------------------------------
# Loading config
# ---------------------------------------------------------------------------

def load_split_config() -> Dict[str, dict]:
    """Return the ``split_pages`` block from reference_map.json (or {})."""
    with open(REFERENCE_MAP, encoding="utf-8") as f:
        data = json.load(f)
    block = data.get("split_pages", {}) or {}
    # Drop comment keys
    return {k: v for k, v in block.items() if not k.startswith("_")}


# ---------------------------------------------------------------------------
# Heading helpers
# ---------------------------------------------------------------------------

H2_RE = re.compile(r"^##[ \t]+(?P<title>\S.*?)\s*$")
H3_RE = re.compile(r"^###[ \t]+(?P<title>\S.*?)\s*$")
FENCE_RE = re.compile(r"^(```|~~~)")


def _normalise(text: str) -> str:
    """Lowercase + collapse whitespace for fuzzy heading match."""
    return re.sub(r"\s+", " ", text.strip().lower())


def slugify(text: str) -> str:
    """Slugify a heading the same way pymdownx/toc does (good-enough fallback).

    Matches the GitHub/pymdownx style used elsewhere in the pipeline:
    lowercase, drop non-word/space/dash chars, replace spaces with dashes.
    """
    s = text.strip().lower()
    # Drop anything that is not a word char, dash, space, or unicode letter.
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


HEADING_RE = re.compile(r"^(?P<hashes>#{2,6})[ \t]+(?P<title>\S.*?)\s*$")


def _iter_headings(lines: List[str]):
    """Yield (line_index, level, raw_title) for ##..###### headings.

    Skips lines inside fenced code blocks.
    """
    in_fence = False
    fence_marker: Optional[str] = None
    for idx, line in enumerate(lines):
        m = FENCE_RE.match(line)
        if m:
            marker = m.group(1)
            if not in_fence:
                in_fence = True
                fence_marker = marker
            elif fence_marker and line.startswith(fence_marker):
                in_fence = False
                fence_marker = None
            continue
        if in_fence:
            continue
        h = HEADING_RE.match(line)
        if h:
            yield idx, len(h.group("hashes")), h.group("title")


# ---------------------------------------------------------------------------
# Splitting
# ---------------------------------------------------------------------------

def find_h2_index(lines: List[str], heading: str) -> Optional[int]:
    """Return the 0-based line index of ``## <heading>`` (fuzzy), or None."""
    target = _normalise(heading)
    for idx, level, title in _iter_headings(lines):
        if level == 2 and _normalise(title) == target:
            return idx
    return None


def compute_split_ranges(
    lines: List[str], splits: List[dict]
) -> List[Tuple[dict, int, int]]:
    """Return [(split_entry, start_idx, end_idx_exclusive), ...] sorted by start.

    Raises KeyError if any heading cannot be located.
    """
    located: List[Tuple[dict, int]] = []
    for entry in splits:
        idx = find_h2_index(lines, entry["from_heading"])
        if idx is None:
            raise KeyError(
                f"Heading not found: ## {entry['from_heading']!r}"
            )
        located.append((entry, idx))

    # Order by start index in the source so the slice between two splits is
    # bounded by the next configured split (or EOF).
    located.sort(key=lambda pair: pair[1])

    ranges: List[Tuple[dict, int, int]] = []
    for i, (entry, start) in enumerate(located):
        end = located[i + 1][1] if i + 1 < len(located) else len(lines)
        ranges.append((entry, start, end))
    return ranges


def build_split_content(lines: List[str], start: int, end: int, h1_title: str) -> str:
    """Return the new file body: H2 promoted to H1, contents up to ``end``."""
    section = lines[start:end]
    # Replace the leading ## ... line with # <h1_title>.
    if section:
        section = section.copy()
        section[0] = f"# {h1_title}"
    body = "\n".join(section).rstrip() + "\n"
    # A single leading blank line, mirroring the existing converter output.
    return "\n" + body


# ---------------------------------------------------------------------------
# Redirects
# ---------------------------------------------------------------------------

def collect_redirects(
    source_rel: str,
    lines: List[str],
    ranges: List[Tuple[dict, int, int]],
) -> Dict[str, str]:
    """Build the anchor-redirect mapping for one source file.

    Keys are ``<source_rel>#<slug>``; values are ``<target_rel>`` or
    ``<target_rel>#<slug>``.
    """
    redirects: Dict[str, str] = {}
    for entry, start, end in ranges:
        target_rel = entry["target"]
        section_h2_title = (
            lines[start][3:].strip()
            if lines[start].startswith("## ")
            else entry["from_heading"]
        )
        section_h2_slug = slugify(section_h2_title)
        # The slice's leading H2 anchor → bare target file (it becomes the H1).
        redirects[f"{source_rel}#{section_h2_slug}"] = target_rel

        # Every other heading inside the slice keeps its slug but moves files.
        sub_lines = lines[start:end]
        first = True
        for _offset, _level, title in _iter_headings(sub_lines):
            if first:
                # Skip the leading ## that we just promoted to H1.
                first = False
                continue
            slug = slugify(title)
            if not slug:
                continue
            redirects[f"{source_rel}#{slug}"] = f"{target_rel}#{slug}"
    return redirects


def merge_redirects(new: Dict[str, str]) -> Dict[str, str]:
    """Merge ``new`` into the persisted redirects file (preserving comments)."""
    if REDIRECTS_FILE.exists():
        with open(REDIRECTS_FILE, encoding="utf-8") as f:
            existing = json.load(f)
    else:
        existing = {
            "_comment": (
                "Auto-generated by split_pages.py. Maps "
                "<source_md>#<anchor> → <target_md>[#<anchor>] for pages "
                "that were split during conversion. Consumed by "
                "fix_cross_page_anchors.py / fix_anchor_corrections.py."
            )
        }
    for key, value in new.items():
        existing[key] = value
    return existing


# ---------------------------------------------------------------------------
# Main per-source processing
# ---------------------------------------------------------------------------

def process_source(
    source_rel: str,
    config: dict,
    dry_run: bool,
    report: bool,
) -> Tuple[int, int, int, Dict[str, str], List[str]]:
    """Split one source MD per its config block.

    Returns (created, skipped_unchanged, deleted, redirects, log_lines).
    """
    log: List[str] = []
    source_path = DOCS_DIR / source_rel
    splits = config.get("splits", [])
    delete_source = bool(config.get("delete_source", False))

    if not source_path.exists():
        # If all targets already exist and source is gone, treat as a no-op.
        targets = [DOCS_DIR / s["target"] for s in splits]
        if delete_source and all(t.exists() for t in targets):
            log.append(f"  {source_rel}: already split (source removed); skipping")
            return 0, len(targets), 0, {}, log
        log.append(f"  {source_rel}: source not found and not yet split")
        return 0, 0, 0, {}, log

    text = source_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    try:
        ranges = compute_split_ranges(lines, splits)
    except KeyError as err:
        log.append(f"  {source_rel}: {err}")
        return 0, 0, 0, {}, log

    created = 0
    skipped = 0
    for entry, start, end in ranges:
        target_rel = entry["target"]
        target_path = DOCS_DIR / target_rel
        new_content = build_split_content(lines, start, end, entry["h1_title"])

        if target_path.exists():
            current = target_path.read_text(encoding="utf-8")
            if current == new_content:
                skipped += 1
                if report:
                    log.append(f"    = {target_rel} (unchanged)")
                continue

        if not dry_run:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(new_content, encoding="utf-8")
        created += 1
        log.append(f"    + {target_rel} ({end - start} lines)")

    redirects = collect_redirects(source_rel, lines, ranges)

    deleted = 0
    if delete_source:
        if not dry_run:
            source_path.unlink()
        deleted = 1
        log.append(f"    - {source_rel} (deleted)")

    return created, skipped, deleted, redirects, log


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Split combined Markdown pages into per-section files based on "
            "reference_map.json's split_pages block."
        )
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview only")
    parser.add_argument("--report", action="store_true", help="Show details")
    args = parser.parse_args()

    config_block = load_split_config()
    if not config_block:
        print("No split_pages entries configured. Nothing to do.")
        return 0

    print(f"Loaded {len(config_block)} split_pages entr"
          f"{'y' if len(config_block) == 1 else 'ies'}")

    total_created = 0
    total_skipped = 0
    total_deleted = 0
    all_redirects: Dict[str, str] = {}

    for source_rel, config in sorted(config_block.items()):
        created, skipped, deleted, redirects, log = process_source(
            source_rel, config, args.dry_run, args.report
        )
        total_created += created
        total_skipped += skipped
        total_deleted += deleted
        all_redirects.update(redirects)

        if args.report or args.dry_run or created or deleted:
            print(f"\n  {source_rel}:")
            for line in log:
                print(line)

    if all_redirects and not args.dry_run:
        merged = merge_redirects(all_redirects)
        REDIRECTS_FILE.write_text(
            json.dumps(merged, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    summary = (
        f"\nSplit summary: {total_created} created, "
        f"{total_skipped} unchanged, {total_deleted} source(s) removed, "
        f"{len(all_redirects)} redirect(s)"
    )
    if args.dry_run:
        summary += " [dry-run, no files written]"
    print(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
