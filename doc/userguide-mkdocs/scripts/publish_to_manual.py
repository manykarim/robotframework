#!/usr/bin/env python3
"""Copy generated MkDocs content into a local checkout of the manual repo.

Usage:
    python publish_to_manual.py --manual-dir /path/to/manual [--no-rewrite]

The script reads manual_file_map.json (alongside this file), copies each
mapped source file from doc/userguide-mkdocs/docs/ to the corresponding
target path under <manual-dir>/doc/manual/docs/, and then rewrites internal
cross-file Markdown links in the copied files from our section/file naming
(e.g. creating-test-data/test-data-syntax.md) to the manual's naming
(e.g. syntax/data.md). Anchors (#fragment) are preserved. Targets with no
mapping are left unchanged and reported. Use --no-rewrite to copy only.
"""

import argparse
import json
import posixpath
import re
import shutil
import sys
from pathlib import Path


# Matches Markdown inline link/image targets: the (...) part after ](.
# Group 1 is the raw content inside the parentheses (URL plus optional title).
_LINK_RE = re.compile(r"\]\(([^)]+)\)")
# Matches a fenced code-block delimiter line (``` or ~~~, three or more),
# capturing the marker and any trailing content (info string on open).
_FENCE_RE = re.compile(r"^(`{3,}|~{3,})(.*)$")


def load_map(scripts_dir: Path) -> dict:
    map_path = scripts_dir / "manual_file_map.json"
    with map_path.open() as f:
        return json.load(f)


def _split_url(raw: str):
    """Split a link's inner content into (path, anchor, title_suffix).

    `raw` is everything between ']( ' and ')'. It may contain an optional
    title after whitespace, e.g. `path.md#a "Title"`.
    """
    raw = raw.strip()
    # Separate an optional title (first unescaped whitespace).
    parts = raw.split(None, 1)
    url = parts[0]
    title = (" " + parts[1]) if len(parts) > 1 else ""
    if "#" in url:
        path, frag = url.split("#", 1)
        anchor = "#" + frag
    else:
        path, anchor = url, ""
    return path, anchor, title


def _map_target(resolved_src: str, files: dict, section_dirs: dict):
    """Map a docs-root-relative source path to the manual's path.

    Returns (mapped_path, kind) where kind is 'file', 'section', or None.
    """
    if resolved_src in files:
        return files[resolved_src], "file"
    # Fallback: remap only the leading section directory, keep the filename.
    head, _, tail = resolved_src.partition("/")
    if tail and head in section_dirs:
        return f"{section_dirs[head]}/{tail}", "section"
    return None, None


def rewrite_links(text: str, src_rel: str, dst_rel: str, files: dict,
                  section_dirs: dict, unmapped: set) -> str:
    """Rewrite internal Markdown links in one file's text."""
    src_dir = posixpath.dirname(src_rel)
    dst_dir = posixpath.dirname(dst_rel)

    out_lines = []
    in_fence = False
    fence_char = ""
    fence_len = 0
    for line in text.split("\n"):
        # Robust CommonMark fence tracking: a fence opens on 3+ backticks/tildes
        # and only closes on a line with the same marker char, length >= the
        # opening length, and no trailing info string. This correctly handles
        # nested fences (e.g. a ```markdown block showing ``` examples).
        m = _FENCE_RE.match(line.lstrip())
        if m:
            marker, rest = m.group(1), m.group(2)
            if not in_fence:
                in_fence = True
                fence_char = marker[0]
                fence_len = len(marker)
            elif (marker[0] == fence_char and len(marker) >= fence_len
                  and rest.strip() == ""):
                in_fence = False
            out_lines.append(line)
            continue
        if in_fence:
            out_lines.append(line)
            continue

        def repl(m):
            path, anchor, title = _split_url(m.group(1))
            # Skip external links, mailto, protocol-relative, pure anchors.
            if (not path or path.startswith(("http://", "https://", "mailto:",
                                             "//", "/"))
                    or ":" in path.split("/")[0]):
                return m.group(0)
            # Resolve relative to the SOURCE file's directory.
            resolved = posixpath.normpath(posixpath.join(src_dir, path))
            mapped, kind = _map_target(resolved, files, section_dirs)
            if mapped is None:
                if path.endswith(".md"):
                    unmapped.add(resolved)
                return m.group(0)
            # Recompute relative to the TARGET file's directory.
            new_path = posixpath.relpath(mapped, dst_dir) if dst_dir else mapped
            return f"]({new_path}{anchor}{title})"

        out_lines.append(_LINK_RE.sub(repl, line))
    return "\n".join(out_lines)


def publish(docs_dir: Path, manual_docs_dir: Path, file_map: dict,
            section_dirs: dict, do_rewrite: bool) -> int:
    copied = []
    skipped = []
    copied_md = []  # (src_rel, dst_rel) for Markdown files

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
        if src_rel.endswith(".md"):
            copied_md.append((src_rel, dst_rel))

    unmapped = set()
    rewritten = 0
    if do_rewrite:
        for src_rel, dst_rel in copied_md:
            dst = manual_docs_dir / dst_rel
            text = dst.read_text(encoding="utf-8")
            new_text = rewrite_links(text, src_rel, dst_rel, file_map,
                                     section_dirs, unmapped)
            if new_text != text:
                dst.write_text(new_text, encoding="utf-8")
                rewritten += 1

    print(f"\n{'='*60}")
    print(f"Copied : {len(copied)} file(s)")
    if copied:
        for line in copied:
            print(line)
    print(f"\nSkipped: {len(skipped)} file(s)")
    if skipped:
        for path in skipped:
            print(f"  {path}")
    if do_rewrite:
        print(f"\nRewritten links in: {rewritten} file(s)")
        print(f"Unmapped .md link targets: {len(unmapped)}")
        for path in sorted(unmapped):
            print(f"  {path}")
    print('='*60)

    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--manual-dir",
        required=True,
        type=Path,
        help="Path to a local checkout of the manual repo (manykarim/manual)",
    )
    parser.add_argument(
        "--no-rewrite",
        action="store_true",
        help="Copy files only; do not rewrite internal cross-file links",
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
        print("       Is --manual-dir pointing to the root of a manykarim/manual checkout?", file=sys.stderr)
        return 1

    data = load_map(scripts_dir)
    file_map = data["files"]
    section_dirs = data.get("section_dirs", {})
    print(f"Source : {docs_dir}")
    print(f"Target : {manual_docs_dir}")
    print(f"Entries: {len(file_map)}")
    print(f"Rewrite: {'no' if args.no_rewrite else 'yes'}")

    return publish(docs_dir, manual_docs_dir, file_map, section_dirs,
                   do_rewrite=not args.no_rewrite)


if __name__ == "__main__":
    sys.exit(main())
