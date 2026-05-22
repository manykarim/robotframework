"""Link and resource validators."""

import re
from pathlib import Path
from urllib.parse import urlparse

from docdiff.models import Block, BlockType, Finding, Section, Severity

# Import from submodules
from .link_validator import (
    LinkType,
    LinkInfo,
    extract_all_links,
    validate_internal_links as validate_link_targets,  # renamed to avoid shadowing
    check_anchor_drift,
    build_anchor_map,
)
from .image_validator import (
    ImageInfo,
    extract_all_images,
    validate_images,
    compare_image_sets,
)


class LinkValidator:
    """Validate links in documents."""

    # Patterns for link extraction
    MARKDOWN_LINK = re.compile(r'\[([^\]]*)\]\(([^)]+)\)')
    HTML_LINK = re.compile(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>([^<]*)</a>', re.IGNORECASE)
    BARE_URL = re.compile(r'https?://[^\s<>"()]+')

    def __init__(self, base_path: Path | None = None):
        """Initialize the validator.

        Args:
            base_path: Base path for resolving relative links
        """
        self.base_path = base_path or Path.cwd()

    def extract_links(self, content: str) -> list[dict[str, str]]:
        """Extract all links from content.

        Args:
            content: Text content to extract links from

        Returns:
            List of dicts with 'href' and 'text' keys
        """
        links: list[dict[str, str]] = []

        # Markdown links
        for match in self.MARKDOWN_LINK.finditer(content):
            text, href = match.groups()
            links.append({'href': href, 'text': text})

        # HTML links
        for match in self.HTML_LINK.finditer(content):
            href, text = match.groups()
            links.append({'href': href, 'text': text})

        # Bare URLs (not already captured)
        captured_hrefs = {link['href'] for link in links}
        for match in self.BARE_URL.finditer(content):
            href = match.group(0)
            if href not in captured_hrefs:
                links.append({'href': href, 'text': ''})

        return links

    def validate_link(self, href: str) -> tuple[bool, str]:
        """Validate a single link.

        Args:
            href: The link URL to validate

        Returns:
            Tuple of (is_valid, reason)
        """
        if not href:
            return False, "Empty link"

        # Check for anchor links
        if href.startswith('#'):
            return True, "Anchor link"

        # Parse URL
        parsed = urlparse(href)

        # External links
        if parsed.scheme in ('http', 'https'):
            return True, "External link (not verified)"

        # mailto links
        if parsed.scheme == 'mailto':
            return True, "Email link"

        # Relative file links
        if not parsed.scheme:
            return self._validate_relative_link(href)

        return False, f"Unknown scheme: {parsed.scheme}"

    def _validate_relative_link(self, href: str) -> tuple[bool, str]:
        """Validate a relative file link.

        Args:
            href: Relative path to validate

        Returns:
            Tuple of (is_valid, reason)
        """
        # Remove anchor
        path = href.split('#')[0]
        if not path:
            return True, "Anchor-only link"

        # Resolve path
        try:
            full_path = self.base_path / path
            if full_path.exists():
                return True, "File exists"
            return False, f"File not found: {path}"
        except Exception as e:
            return False, f"Invalid path: {e}"

    def validate_internal_links(
        self,
        sections: list[Section],
        all_section_keys: set[str],
    ) -> list[Finding]:
        """Validate internal anchor links against section keys.

        Args:
            sections: Sections to validate links in
            all_section_keys: Set of valid section keys/anchors

        Returns:
            List of findings for invalid links
        """
        findings: list[Finding] = []

        for section in sections:
            for block in section.blocks:
                links = self.extract_links(block.content)

                for link in links:
                    href = link['href']
                    if href.startswith('#'):
                        anchor = href[1:]
                        if anchor and anchor not in all_section_keys:
                            findings.append(Finding(
                                category="broken_internal_link",
                                severity=Severity.ERROR,
                                message=f"Internal link to unknown anchor: {href}",
                                source_location=section.get_full_path(),
                                source_content=link.get('text', ''),
                                suggestion=f"Valid anchors include: {', '.join(sorted(all_section_keys)[:5])}...",
                            ))

        return findings


class ImageValidator:
    """Validate images in documents."""

    # Patterns for image extraction
    MARKDOWN_IMAGE = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
    HTML_IMAGE = re.compile(r'<img\s+[^>]*src=["\']([^"\']+)["\'][^>]*>', re.IGNORECASE)

    def __init__(self, base_path: Path | None = None):
        """Initialize the validator.

        Args:
            base_path: Base path for resolving relative paths
        """
        self.base_path = base_path or Path.cwd()

    def extract_images(self, content: str) -> list[dict[str, str]]:
        """Extract all images from content.

        Args:
            content: Text content to extract images from

        Returns:
            List of dicts with 'src' and 'alt' keys
        """
        images: list[dict[str, str]] = []

        # Markdown images
        for match in self.MARKDOWN_IMAGE.finditer(content):
            alt, src = match.groups()
            images.append({'src': src, 'alt': alt})

        # HTML images
        for match in self.HTML_IMAGE.finditer(content):
            src = match.group(1)
            # Try to extract alt from the full match
            alt_match = re.search(r'alt=["\']([^"\']*)["\']', match.group(0))
            alt = alt_match.group(1) if alt_match else ''
            images.append({'src': src, 'alt': alt})

        return images

    def validate_image(self, src: str) -> tuple[bool, str]:
        """Validate a single image source.

        Args:
            src: The image source URL/path

        Returns:
            Tuple of (is_valid, reason)
        """
        if not src:
            return False, "Empty source"

        parsed = urlparse(src)

        # External images
        if parsed.scheme in ('http', 'https'):
            return True, "External image (not verified)"

        # Data URLs
        if parsed.scheme == 'data':
            return True, "Data URL"

        # Relative paths
        if not parsed.scheme:
            return self._validate_relative_image(src)

        return False, f"Unknown scheme: {parsed.scheme}"

    def _validate_relative_image(self, src: str) -> tuple[bool, str]:
        """Validate a relative image path.

        Args:
            src: Relative path to validate

        Returns:
            Tuple of (is_valid, reason)
        """
        try:
            full_path = self.base_path / src
            if full_path.exists():
                return True, "Image exists"
            return False, f"Image not found: {src}"
        except Exception as e:
            return False, f"Invalid path: {e}"

    def validate_images_in_sections(
        self,
        sections: list[Section],
    ) -> list[Finding]:
        """Validate all images in sections.

        Args:
            sections: Sections to validate images in

        Returns:
            List of findings for invalid images
        """
        findings: list[Finding] = []

        for section in sections:
            for block in section.blocks:
                # Check image blocks
                if block.block_type == BlockType.IMAGE:
                    src = block.metadata.get('src', '')
                    is_valid, reason = self.validate_image(src)

                    if not is_valid:
                        findings.append(Finding(
                            category="broken_image",
                            severity=Severity.ERROR,
                            message=f"Broken image: {reason}",
                            source_location=section.get_full_path(),
                            source_content=src,
                        ))

                # Check images in content
                images = self.extract_images(block.content)
                for img in images:
                    src = img['src']
                    is_valid, reason = self.validate_image(src)

                    if not is_valid:
                        findings.append(Finding(
                            category="broken_image",
                            severity=Severity.ERROR,
                            message=f"Broken image: {reason}",
                            source_location=section.get_full_path(),
                            source_content=f"![{img['alt']}]({src})",
                        ))

                # Check for missing alt text
                for img in images:
                    if not img['alt']:
                        findings.append(Finding(
                            category="missing_alt_text",
                            severity=Severity.WARNING,
                            message="Image missing alt text",
                            source_location=section.get_full_path(),
                            source_content=img['src'],
                            suggestion="Add descriptive alt text for accessibility",
                        ))

        return findings


def extract_links(content: str) -> list[dict[str, str]]:
    """Extract all links from content.

    Convenience function wrapping LinkValidator.

    Args:
        content: Text content to extract links from

    Returns:
        List of dicts with 'href' and 'text' keys
    """
    validator = LinkValidator()
    return validator.extract_links(content)


def extract_images(content: str) -> list[dict[str, str]]:
    """Extract all images from content.

    Convenience function wrapping ImageValidator.

    Args:
        content: Text content to extract images from

    Returns:
        List of dicts with 'src' and 'alt' keys
    """
    validator = ImageValidator()
    return validator.extract_images(content)


def validate_internal_links(
    sections: list[Section],
    all_section_keys: set[str],
) -> list[Finding]:
    """Validate internal links in sections.

    Args:
        sections: Sections to validate
        all_section_keys: Set of valid section keys/anchors

    Returns:
        List of findings for broken links
    """
    validator = LinkValidator()
    return validator.validate_internal_links(sections, all_section_keys)
