"""Image validation for documentation comparison.

This module provides functions to extract, validate, and compare images
between documentation versions.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from docdiff.models import Finding


@dataclass
class ImageInfo:
    """Information about an extracted image."""
    src: str
    alt_text: str
    source_section: str
    source_file: str
    title: str = ""
    line_number: int | None = None

    @property
    def filename(self) -> str:
        """Extract just the filename from the src path."""
        return os.path.basename(self.src)

    @property
    def is_external(self) -> bool:
        """Check if image is hosted externally."""
        return self.src.startswith(("http://", "https://", "//"))

    def resolve_path(self, base_path: str) -> str:
        """Resolve the image path relative to a base path."""
        if self.is_external:
            return self.src

        # Handle absolute paths
        if self.src.startswith("/"):
            return os.path.normpath(os.path.join(base_path, self.src.lstrip("/")))

        # Handle relative paths
        source_dir = os.path.dirname(self.source_file)
        if source_dir:
            return os.path.normpath(os.path.join(base_path, source_dir, self.src))
        return os.path.normpath(os.path.join(base_path, self.src))


def _extract_images_from_content(
    content: str,
    source_section: str,
    source_file: str,
) -> list[ImageInfo]:
    """Extract images from markdown/rst content.

    Supports:
    - Markdown images: ![alt](src "title")
    - HTML img tags: <img src="..." alt="..." />
    - RST images: .. image:: path
    - RST figures: .. figure:: path
    """
    images: list[ImageInfo] = []

    # Markdown images: ![alt](src) or ![alt](src "title")
    md_image_pattern = re.compile(
        r'!\[([^\]]*)\]\(([^)"\s]+)(?:\s+"([^"]*)")?\)'
    )
    for match in md_image_pattern.finditer(content):
        alt, src, title = match.groups()
        images.append(ImageInfo(
            src=src.strip(),
            alt_text=alt,
            source_section=source_section,
            source_file=source_file,
            title=title or "",
        ))

    # HTML img tags: <img src="..." alt="..." />
    html_img_pattern = re.compile(
        r'<img\s+[^>]*src=["\']([^"\']+)["\'][^>]*>',
        re.IGNORECASE
    )
    html_alt_pattern = re.compile(r'alt=["\']([^"\']*)["\']', re.IGNORECASE)
    html_title_pattern = re.compile(r'title=["\']([^"\']*)["\']', re.IGNORECASE)

    for match in html_img_pattern.finditer(content):
        full_tag = match.group(0)
        src = match.group(1)

        alt_match = html_alt_pattern.search(full_tag)
        alt = alt_match.group(1) if alt_match else ""

        title_match = html_title_pattern.search(full_tag)
        title = title_match.group(1) if title_match else ""

        images.append(ImageInfo(
            src=src.strip(),
            alt_text=alt,
            source_section=source_section,
            source_file=source_file,
            title=title,
        ))

    # RST images: .. image:: path
    rst_image_pattern = re.compile(r'\.\.\s+image::\s*(\S+)')
    for match in rst_image_pattern.finditer(content):
        src = match.group(1)
        # Look for :alt: option after the directive
        alt = ""
        alt_match = re.search(
            rf'\.\.\s+image::\s*{re.escape(src)}\s+.*?:alt:\s*(.+?)(?:\n\s*:|$)',
            content,
            re.DOTALL
        )
        if alt_match:
            alt = alt_match.group(1).strip()

        images.append(ImageInfo(
            src=src.strip(),
            alt_text=alt,
            source_section=source_section,
            source_file=source_file,
        ))

    # RST figures: .. figure:: path
    rst_figure_pattern = re.compile(r'\.\.\s+figure::\s*(\S+)')
    for match in rst_figure_pattern.finditer(content):
        src = match.group(1)
        # Look for :alt: option
        alt = ""
        alt_match = re.search(
            rf'\.\.\s+figure::\s*{re.escape(src)}\s+.*?:alt:\s*(.+?)(?:\n\s*:|$)',
            content,
            re.DOTALL
        )
        if alt_match:
            alt = alt_match.group(1).strip()

        images.append(ImageInfo(
            src=src.strip(),
            alt_text=alt,
            source_section=source_section,
            source_file=source_file,
        ))

    return images


def _extract_images_recursive(
    sections: list,
    source_file: str,
) -> list[ImageInfo]:
    """Recursively extract images from sections and their children."""
    images: list[ImageInfo] = []

    for section in sections:
        # Extract from section content
        content = getattr(section, "content", "") or ""
        section_id = getattr(section, "id", "") or getattr(section, "title", "") or ""

        images.extend(_extract_images_from_content(
            content=content,
            source_section=section_id,
            source_file=source_file,
        ))

        # Recurse into children
        children = getattr(section, "children", []) or []
        if children:
            images.extend(_extract_images_recursive(children, source_file))

    return images


def extract_all_images(sections: list, source_file: str = "") -> list[ImageInfo]:
    """Extract all images from a list of sections.

    Recursively traverses sections and their children to find all images
    in the content.

    Args:
        sections: List of Section objects to extract images from.
        source_file: The source file path for context.

    Returns:
        List of ImageInfo objects representing all found images.
    """
    return _extract_images_recursive(sections, source_file)


def validate_images(
    images: list[ImageInfo],
    base_path: str,
    check_exists: bool = True,
) -> list:
    """Validate image files and accessibility.

    Checks:
    - Image file exists on disk (if check_exists=True)
    - Image has alt text for accessibility

    Args:
        images: List of ImageInfo objects to validate.
        base_path: Base path for resolving relative image paths.
        check_exists: Whether to check if image files exist on disk.

    Returns:
        List of Finding objects for validation issues.
    """
    from docdiff.models import Finding, FindingCategory, Severity

    findings: list[Finding] = []
    seen_paths: set[str] = set()

    for image in images:
        # Skip external images for existence check
        if image.is_external:
            # Still check alt text for external images
            if not image.alt_text:
                findings.append(Finding(
                    category=FindingCategory.IMAGE_MISSING.value,
                    severity=Severity.WARNING,
                    message=f"Missing alt text: image '{image.src}' lacks accessibility text",
                    source_location=image.source_file,
                    section_key=image.source_section,
                    source_content=image.src,
                    suggestion="Add descriptive alt text for accessibility",
                ))
            continue

        # Check file exists (only once per unique path)
        if check_exists:
            resolved_path = image.resolve_path(base_path)

            if resolved_path not in seen_paths:
                seen_paths.add(resolved_path)

                if not os.path.isfile(resolved_path):
                    findings.append(Finding(
                        category=FindingCategory.IMAGE_MISSING.value,
                        severity=Severity.ERROR,
                        message=f"Missing image file: '{image.src}' does not exist",
                        source_location=image.source_file,
                        section_key=image.source_section,
                        source_content=image.src,
                        suggestion=f"Add the missing image file or update the reference",
                    ))

        # Check alt text
        if not image.alt_text:
            findings.append(Finding(
                category=FindingCategory.IMAGE_MISSING.value,
                severity=Severity.WARNING,
                message=f"Missing alt text: image '{image.src}' lacks accessibility text",
                source_location=image.source_file,
                section_key=image.source_section,
                source_content=image.src,
                suggestion="Add descriptive alt text for accessibility",
            ))

    return findings


def compare_image_sets(
    old_images: list[ImageInfo],
    new_images: list[ImageInfo],
) -> list:
    """Compare image usage between old and new documentation.

    Detects:
    - Images present in old but missing in new
    - Changed alt text between versions

    Args:
        old_images: List of ImageInfo from old documentation.
        new_images: List of ImageInfo from new documentation.

    Returns:
        List of Finding objects for differences.
    """
    from docdiff.models import Finding, FindingCategory, Severity

    findings: list[Finding] = []

    # Build lookup maps by normalized source path
    def normalize_src(src: str) -> str:
        """Normalize image source for comparison."""
        # Remove leading ./ or /
        normalized = src.lstrip("./")
        # Normalize path separators
        normalized = normalized.replace("\\", "/")
        return normalized.lower()

    old_by_src: dict[str, ImageInfo] = {
        normalize_src(img.src): img for img in old_images
    }
    new_by_src: dict[str, ImageInfo] = {
        normalize_src(img.src): img for img in new_images
    }

    # Find missing images (in old but not in new)
    missing_srcs = set(old_by_src.keys()) - set(new_by_src.keys())
    for src in missing_srcs:
        old_img = old_by_src[src]
        findings.append(Finding(
            category=FindingCategory.IMAGE_MISSING.value,
            severity=Severity.ERROR,
            message=f"Image removed: '{old_img.src}' not present in new documentation",
            source_location=old_img.source_file,
            section_key=old_img.source_section,
            source_content=old_img.src,
            suggestion="Restore the image or update references",
        ))

    # Find changed alt text (same image, different alt)
    common_srcs = set(old_by_src.keys()) & set(new_by_src.keys())
    for src in common_srcs:
        old_img = old_by_src[src]
        new_img = new_by_src[src]

        # Compare alt text
        old_alt = old_img.alt_text.strip()
        new_alt = new_img.alt_text.strip()

        if old_alt != new_alt:
            # Determine if this is an improvement or regression
            if old_alt and not new_alt:
                # Alt text was removed - definitely a regression
                findings.append(Finding(
                    category=FindingCategory.CONTENT_CHANGED.value,
                    severity=Severity.WARNING,
                    message=f"Alt text removed: image '{old_img.src}' lost accessibility text",
                    source_location=new_img.source_file,
                    section_key=new_img.source_section,
                    source_content=old_alt,
                    target_content=new_alt,
                    suggestion="Restore alt text for accessibility compliance",
                ))
            elif old_alt and new_alt:
                # Alt text was changed - informational
                findings.append(Finding(
                    category=FindingCategory.CONTENT_CHANGED.value,
                    severity=Severity.INFO,
                    message=f"Alt text changed for image '{old_img.src}'",
                    source_location=new_img.source_file,
                    section_key=new_img.source_section,
                    source_content=old_alt,
                    target_content=new_alt,
                    suggestion="Verify the new alt text is appropriate",
                ))
            # If old had no alt and new has alt, that's an improvement - no finding

    return findings
