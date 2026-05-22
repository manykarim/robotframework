"""Link and anchor validation for documentation comparison.

This module provides functions to extract, validate, and compare links
and anchors between documentation versions.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING
from urllib.parse import urlparse

if TYPE_CHECKING:
    from docdiff.models import Section, Finding


class LinkType(Enum):
    """Classification of link types."""
    INTERNAL = "internal"
    EXTERNAL = "external"
    ANCHOR = "anchor"  # Same-page anchor link (#section)


@dataclass
class LinkInfo:
    """Information about an extracted link."""
    url: str
    text: str
    source_section: str
    source_file: str
    link_type: LinkType
    line_number: int | None = None

    @property
    def is_internal(self) -> bool:
        """Check if link is internal (relative or same domain)."""
        return self.link_type in (LinkType.INTERNAL, LinkType.ANCHOR)

    @property
    def target_page(self) -> str | None:
        """Extract target page path from URL."""
        if self.link_type == LinkType.ANCHOR:
            return None  # Same page
        parsed = urlparse(self.url)
        path = parsed.path
        if not path or path == "/":
            return None
        # Normalize path
        return path.lstrip("/").rstrip("/")

    @property
    def target_anchor(self) -> str | None:
        """Extract target anchor from URL."""
        parsed = urlparse(self.url)
        fragment = parsed.fragment
        return fragment if fragment else None


def _is_external_url(url: str) -> bool:
    """Check if a URL is external (absolute with different domain)."""
    parsed = urlparse(url)
    # Has scheme and netloc = absolute external URL
    return bool(parsed.scheme and parsed.netloc)


def _extract_links_from_content(
    content: str,
    source_section: str,
    source_file: str,
) -> list[LinkInfo]:
    """Extract links from markdown/rst content.

    Supports:
    - Markdown links: [text](url)
    - Markdown reference links: [text][ref]
    - RST links: `text <url>`_
    - RST reference links: :ref:`text`
    - Raw URLs: http(s)://...
    """
    links: list[LinkInfo] = []

    # Markdown inline links: [text](url)
    md_link_pattern = re.compile(r'\[([^\]]*)\]\(([^)]+)\)')
    for match in md_link_pattern.finditer(content):
        text, url = match.groups()
        url = url.strip()
        if url.startswith("#"):
            link_type = LinkType.ANCHOR
        elif _is_external_url(url):
            link_type = LinkType.EXTERNAL
        else:
            link_type = LinkType.INTERNAL

        links.append(LinkInfo(
            url=url,
            text=text,
            source_section=source_section,
            source_file=source_file,
            link_type=link_type,
        ))

    # RST inline links: `text <url>`_
    rst_link_pattern = re.compile(r'`([^<]+)\s*<([^>]+)>`_')
    for match in rst_link_pattern.finditer(content):
        text, url = match.groups()
        url = url.strip()
        if url.startswith("#"):
            link_type = LinkType.ANCHOR
        elif _is_external_url(url):
            link_type = LinkType.EXTERNAL
        else:
            link_type = LinkType.INTERNAL

        links.append(LinkInfo(
            url=url,
            text=text.strip(),
            source_section=source_section,
            source_file=source_file,
            link_type=link_type,
        ))

    return links


def _extract_links_recursive(
    sections: list,
    source_file: str,
) -> list[LinkInfo]:
    """Recursively extract links from sections and their children."""
    links: list[LinkInfo] = []

    for section in sections:
        # Extract from section content
        content = getattr(section, "content", "") or ""
        section_id = getattr(section, "id", "") or getattr(section, "title", "") or ""

        links.extend(_extract_links_from_content(
            content=content,
            source_section=section_id,
            source_file=source_file,
        ))

        # Recurse into children
        children = getattr(section, "children", []) or []
        if children:
            links.extend(_extract_links_recursive(children, source_file))

    return links


def extract_all_links(sections: list, source_file: str = "") -> list[LinkInfo]:
    """Extract all links from a list of sections.

    Recursively traverses sections and their children to find all links
    in the content. Links are categorized as internal, external, or anchor.

    Args:
        sections: List of Section objects to extract links from.
        source_file: The source file path for context.

    Returns:
        List of LinkInfo objects representing all found links.
    """
    return _extract_links_recursive(sections, source_file)


def validate_internal_links(
    links: list[LinkInfo],
    available_anchors: dict[str, set[str]],
    available_pages: set[str] | None = None,
) -> list:
    """Validate that internal links point to existing targets.

    Checks each internal link to ensure:
    - The target page exists in available_pages (if provided)
    - For fragment links, the anchor exists on the target page

    Args:
        links: List of LinkInfo objects to validate.
        available_anchors: Dict mapping page paths to sets of valid anchors.
        available_pages: Optional set of valid page paths (without leading slash).
            If None, page existence is not checked, only anchors.

    Returns:
        List of Finding objects for broken links.
    """
    from docdiff.models import Finding, FindingCategory, Severity

    findings: list[Finding] = []

    # Build page set from anchor map keys if not provided
    if available_pages is None:
        available_pages = set(available_anchors.keys())

    for link in links:
        if not link.is_internal:
            continue

        # Same-page anchor links
        if link.link_type == LinkType.ANCHOR:
            anchor = link.target_anchor
            if anchor:
                # Check anchor exists on source file
                source_anchors = available_anchors.get(link.source_file, set())
                if anchor not in source_anchors:
                    findings.append(Finding(
                        category=FindingCategory.LINK_BROKEN.value,
                        severity=Severity.ERROR,
                        message=f"Broken anchor link: '#{anchor}' not found on page '{link.source_file}'",
                        source_location=link.source_file,
                        section_key=link.source_section,
                        source_content=link.url,
                        suggestion=f"Verify anchor '#{anchor}' exists or update the link",
                    ))
            continue

        # Internal page links
        target_page = link.target_page
        if target_page:
            # Normalize for comparison
            normalized_page = target_page.rstrip("/")
            # Try with and without common extensions
            page_variants = [
                normalized_page,
                normalized_page + ".md",
                normalized_page + ".html",
                normalized_page + "/index",
                normalized_page + "/index.md",
            ]

            page_found = any(p in available_pages for p in page_variants)

            if not page_found:
                findings.append(Finding(
                    category=FindingCategory.LINK_BROKEN.value,
                    severity=Severity.ERROR,
                    message=f"Broken internal link: page '{target_page}' not found",
                    source_location=link.source_file,
                    section_key=link.source_section,
                    source_content=link.url,
                    suggestion=f"Update link target or create missing page '{target_page}'",
                ))
            else:
                # Check anchor if present
                anchor = link.target_anchor
                if anchor:
                    # Find which variant matched
                    matched_page = next(
                        (p for p in page_variants if p in available_pages),
                        normalized_page
                    )
                    page_anchors = available_anchors.get(matched_page, set())
                    if anchor not in page_anchors:
                        findings.append(Finding(
                            category=FindingCategory.LINK_BROKEN.value,
                            severity=Severity.ERROR,
                            message=f"Broken fragment link: anchor '#{anchor}' not found on page '{target_page}'",
                            source_location=link.source_file,
                            section_key=link.source_section,
                            source_content=link.url,
                            suggestion=f"Verify anchor '#{anchor}' exists on '{target_page}'",
                        ))

    return findings


def check_anchor_drift(
    old_anchors: dict[str, str],
    new_anchors: dict[str, str],
) -> list:
    """Compare anchor IDs between old and new documentation versions.

    Detects anchors that have been renamed or removed, which could
    break deep links from external sources.

    Args:
        old_anchors: Dict mapping anchor IDs to their headings in old docs.
        new_anchors: Dict mapping anchor IDs to their headings in new docs.

    Returns:
        List of Finding objects for anchor drift issues.
    """
    from docdiff.models import Finding, FindingCategory, Severity

    findings: list[Finding] = []

    # Find missing anchors
    missing_anchors = set(old_anchors.keys()) - set(new_anchors.keys())

    for anchor in missing_anchors:
        old_heading = old_anchors[anchor]

        # Try to find a similar anchor that might be a rename
        possible_renames = []
        for new_anchor, new_heading in new_anchors.items():
            # Check if headings are similar
            if _headings_similar(old_heading, new_heading):
                possible_renames.append((new_anchor, new_heading))

        if possible_renames:
            # Likely a rename
            new_anchor, new_heading = possible_renames[0]
            findings.append(Finding(
                category=FindingCategory.ANCHOR_MISSING.value,
                severity=Severity.ERROR,
                message=(
                    f"Anchor renamed: '#{anchor}' ('{old_heading}') appears to have been "
                    f"renamed to '#{new_anchor}' ('{new_heading}')"
                ),
                source_content=f"#{anchor}",
                target_content=f"#{new_anchor}",
                suggestion=f"Add redirect from #{anchor} to #{new_anchor}",
            ))
        else:
            # Anchor removed
            findings.append(Finding(
                category=FindingCategory.ANCHOR_MISSING.value,
                severity=Severity.ERROR,
                message=f"Anchor removed: '#{anchor}' ('{old_heading}') no longer exists",
                source_content=f"#{anchor}",
                suggestion="Consider adding redirect or keeping anchor for backwards compatibility",
            ))

    return findings


def _headings_similar(heading1: str, heading2: str) -> bool:
    """Check if two headings are similar enough to be considered related.

    Uses simple normalization and substring matching.
    """
    def normalize(s: str) -> str:
        return re.sub(r'[^a-z0-9]+', '', s.lower())

    norm1 = normalize(heading1)
    norm2 = normalize(heading2)

    if not norm1 or not norm2:
        return False

    # Check for substring match or high overlap
    if norm1 in norm2 or norm2 in norm1:
        return True

    # Check word overlap
    words1 = set(heading1.lower().split())
    words2 = set(heading2.lower().split())

    if not words1 or not words2:
        return False

    overlap = len(words1 & words2) / max(len(words1), len(words2))
    return overlap >= 0.5


def _generate_anchor_from_heading(heading: str) -> str:
    """Generate an anchor ID from a heading text.

    Follows common markdown anchor generation rules:
    - Lowercase
    - Replace spaces with hyphens
    - Remove special characters
    """
    anchor = heading.lower()
    anchor = re.sub(r'[^\w\s-]', '', anchor)
    anchor = re.sub(r'[\s_]+', '-', anchor)
    anchor = anchor.strip('-')
    return anchor


def build_anchor_map(sections: list, source_file: str = "") -> dict[str, set[str]]:
    """Build a map of page paths to available anchors.

    Extracts all heading-generated anchors from sections and maps them
    to their source pages.

    Args:
        sections: List of Section objects to extract anchors from.
        source_file: The source file path (used as the page key).

    Returns:
        Dict mapping page paths to sets of available anchor IDs.
    """
    anchors: set[str] = set()

    def extract_anchors_recursive(section_list: list) -> None:
        for section in section_list:
            # Get section ID if explicitly set
            section_id = getattr(section, "id", None)
            if section_id:
                anchors.add(section_id)

            # Generate anchor from title
            title = getattr(section, "title", None)
            if title:
                generated_anchor = _generate_anchor_from_heading(title)
                if generated_anchor:
                    anchors.add(generated_anchor)

            # Check for explicit anchors in content
            content = getattr(section, "content", "") or ""

            # HTML anchor tags: <a name="anchor"> or <a id="anchor">
            html_anchor_pattern = re.compile(r'<a\s+(?:name|id)=["\']([^"\']+)["\']')
            for match in html_anchor_pattern.finditer(content):
                anchors.add(match.group(1))

            # Markdown heading IDs: {#anchor}
            md_anchor_pattern = re.compile(r'\{#([^}]+)\}')
            for match in md_anchor_pattern.finditer(content):
                anchors.add(match.group(1))

            # Recurse into children
            children = getattr(section, "children", []) or []
            if children:
                extract_anchors_recursive(children)

    extract_anchors_recursive(sections)

    return {source_file: anchors} if source_file else {"": anchors}
