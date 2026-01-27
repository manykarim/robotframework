#!/usr/bin/env python3
"""Fix cross-file internal links in Robot Framework User Guide.

This script fixes internal links that reference anchors in other files.
For example: [text](#anchor) where the anchor exists in a different file.
"""
import re
from pathlib import Path
from typing import Dict, Set, Optional


def slugify(text: str) -> str:
    """Convert header text to MkDocs anchor slug."""
    # MkDocs uses a simple slugification:
    # - lowercase
    # - replace spaces with hyphens
    # - remove special characters
    slug = text.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)  # Remove special chars
    slug = re.sub(r'\s+', '-', slug)  # Spaces to hyphens
    slug = re.sub(r'-+', '-', slug)  # Collapse multiple hyphens
    slug = slug.strip('-')
    return slug


def extract_headers(filepath: Path) -> Dict[str, str]:
    """Extract all headers from a markdown file and return {slug: original_text}."""
    content = filepath.read_text(encoding='utf-8')
    headers = {}

    # Match markdown headers (## Header, ### Header, etc.)
    header_pattern = re.compile(r'^#+\s+(.+)$', re.MULTILINE)

    for match in header_pattern.finditer(content):
        header_text = match.group(1).strip()
        # Remove any markdown formatting from header
        header_text = re.sub(r'`([^`]+)`', r'\1', header_text)  # Remove backticks
        slug = slugify(header_text)
        if slug:
            headers[slug] = header_text

    return headers


def build_header_map(docs_dir: Path) -> Dict[str, str]:
    """Build a mapping of {slug: relative_file_path#slug} for all headers."""
    header_map = {}

    for md_file in docs_dir.rglob("*.md"):
        relative_path = md_file.relative_to(docs_dir)
        headers = extract_headers(md_file)

        for slug, original_text in headers.items():
            # Store the file path with anchor
            full_ref = f"{relative_path}#{slug}"

            # Also store variations for matching
            # Store by slug
            if slug not in header_map:
                header_map[slug] = str(relative_path)

            # Store by original text (lowercased)
            text_key = original_text.lower()
            if text_key not in header_map:
                header_map[text_key] = str(relative_path)

    return header_map


def get_anchors_in_file(filepath: Path) -> Set[str]:
    """Get all anchor slugs that exist in a file."""
    content = filepath.read_text(encoding='utf-8')
    anchors = set()

    # Match markdown headers
    header_pattern = re.compile(r'^#+\s+(.+)$', re.MULTILINE)
    for match in header_pattern.finditer(content):
        header_text = match.group(1).strip()
        header_text = re.sub(r'`([^`]+)`', r'\1', header_text)
        slug = slugify(header_text)
        if slug:
            anchors.add(slug)

    # Match explicit anchors like {#anchor-id}
    explicit_pattern = re.compile(r'\{#([^}]+)\}')
    for match in explicit_pattern.finditer(content):
        anchors.add(match.group(1))

    return anchors


def fix_internal_links(content: str, current_file: Path, docs_dir: Path,
                       header_map: Dict[str, str]) -> str:
    """Fix internal anchor links that point to other files."""
    local_anchors = get_anchors_in_file(current_file)
    current_dir = current_file.parent

    def replace_link(match):
        full_match = match.group(0)
        link_text = match.group(1)
        anchor = match.group(2)

        # Normalize anchor for lookup
        anchor_slug = slugify(anchor)
        anchor_lower = anchor.lower()

        # Check if anchor exists in current file
        if anchor_slug in local_anchors:
            # Anchor is local, make sure it uses slug format
            return f'[{link_text}](#{anchor_slug})'

        # Try to find the anchor in another file
        target_file = None

        # Try slug lookup
        if anchor_slug in header_map:
            target_file = header_map[anchor_slug]
        # Try text lookup
        elif anchor_lower in header_map:
            target_file = header_map[anchor_lower]

        if target_file:
            # Calculate relative path from current file to target
            target_path = docs_dir / target_file
            try:
                rel_path = Path(target_path).relative_to(current_dir)
            except ValueError:
                # Need to go up directories
                rel_path = Path('..') / Path(target_file)
                # Adjust path based on directory depth
                current_rel = current_file.relative_to(docs_dir)
                depth = len(current_rel.parts) - 1
                if depth > 0:
                    rel_path = Path('/'.join(['..'] * depth)) / target_file
                else:
                    rel_path = Path(target_file)

            return f'[{link_text}]({rel_path}#{anchor_slug})'

        # Couldn't find anchor, return original
        return full_match

    # Match links like [text](#anchor) where anchor might be in another file
    link_pattern = re.compile(r'\[([^\]]+)\]\(#([^)]+)\)')
    content = link_pattern.sub(replace_link, content)

    return content


def process_file(filepath: Path, docs_dir: Path, header_map: Dict[str, str]) -> bool:
    """Process a single markdown file. Returns True if changes were made."""
    content = filepath.read_text(encoding='utf-8')
    original = content

    content = fix_internal_links(content, filepath, docs_dir, header_map)

    if content != original:
        filepath.write_text(content, encoding='utf-8')
        return True
    return False


def main():
    """Process all markdown files in the docs directory."""
    docs_dir = Path(__file__).parent.parent / "docs"

    if not docs_dir.exists():
        print(f"Error: docs directory not found at {docs_dir}")
        return 1

    print("Building header map...")
    header_map = build_header_map(docs_dir)
    print(f"Found {len(header_map)} unique headers/anchors")

    md_files = list(docs_dir.rglob("*.md"))
    modified_count = 0

    print(f"\nProcessing {len(md_files)} markdown files...")

    for filepath in md_files:
        if process_file(filepath, docs_dir, header_map):
            print(f"  Modified: {filepath.relative_to(docs_dir)}")
            modified_count += 1

    print(f"\nDone. Modified {modified_count} files.")
    return 0


if __name__ == "__main__":
    exit(main())
