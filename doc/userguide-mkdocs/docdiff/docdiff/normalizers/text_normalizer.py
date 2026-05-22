"""Text normalization utilities for consistent document comparison.

This module provides functions for normalizing text, code, table cells,
headings, and links to enable accurate comparison between documentation
formats.
"""

from __future__ import annotations

import difflib
import html
import re
import unicodedata
from pathlib import PurePosixPath
from typing import List, Optional


# Zero-width characters to remove during normalization
ZERO_WIDTH_CHARS = (
    '\u200b',  # Zero-width space
    '\u200c',  # Zero-width non-joiner
    '\u200d',  # Zero-width joiner
    '\ufeff',  # Byte order mark / zero-width no-break space
    '\u2060',  # Word joiner
    '\u180e',  # Mongolian vowel separator
)

# HTML tags to strip (keeping content)
HTML_TAG_PATTERN = re.compile(r'<[^>]+>')

# Pattern for section number prefixes (e.g., "2.1.3", "1.", "2.1.3.")
SECTION_NUMBER_PATTERN = re.compile(r'^(\d+(?:\.\d+)*\.?)\s*')

# Pattern for punctuation except hyphens
PUNCTUATION_EXCEPT_HYPHEN = re.compile(r'[^\w\s-]')

# Pattern for multiple whitespace
MULTI_WHITESPACE = re.compile(r'\s+')

# Pattern for multiple hyphens
MULTI_HYPHEN = re.compile(r'-+')


def normalize_text(text: str) -> str:
    """Normalize text for consistent comparison.

    Performs the following normalizations:
    - Strips leading/trailing whitespace
    - Collapses multiple whitespace to single space
    - Decodes HTML entities (&amp;, &lt;, &gt;, &nbsp;, etc.)
    - Converts to lowercase for comparison
    - Removes zero-width characters
    - Normalizes Unicode (NFC normalization)

    Args:
        text: The input text to normalize.

    Returns:
        The normalized text string.

    Examples:
        >>> normalize_text("  Hello   World  ")
        'hello world'
        >>> normalize_text("&amp; &lt;test&gt;")
        '& <test>'
    """
    if not text:
        return ""

    # Remove zero-width characters first
    for char in ZERO_WIDTH_CHARS:
        text = text.replace(char, '')

    # Decode HTML entities (do this twice to handle double-encoded entities)
    text = html.unescape(text)
    text = html.unescape(text)

    # Normalize Unicode to NFC form
    text = unicodedata.normalize('NFC', text)

    # Convert to lowercase
    text = text.lower()

    # Collapse multiple whitespace to single space
    text = MULTI_WHITESPACE.sub(' ', text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


def normalize_code(code: str) -> str:
    """Normalize code while preserving indentation structure.

    Important for Robot Framework code comparison where indentation matters.

    Performs the following normalizations:
    - Preserves indentation structure
    - Strips trailing whitespace from each line
    - Normalizes line endings to \\n
    - Removes empty lines at start/end
    - Does NOT change case

    Args:
        code: The code string to normalize.

    Returns:
        The normalized code string.

    Examples:
        >>> normalize_code("  line1  \\n  line2  \\n")
        '  line1\\n  line2'
        >>> normalize_code("\\r\\ncode\\r\\n")
        'code'
    """
    if not code:
        return ""

    # Normalize line endings to \n
    code = code.replace('\r\n', '\n').replace('\r', '\n')

    # Split into lines, strip trailing whitespace from each
    lines = [line.rstrip() for line in code.split('\n')]

    # Remove empty lines at start
    while lines and not lines[0]:
        lines.pop(0)

    # Remove empty lines at end
    while lines and not lines[-1]:
        lines.pop()

    return '\n'.join(lines)


def normalize_table_cell(cell: str) -> str:
    """Normalize a table cell for comparison.

    Performs the following normalizations:
    - Strips whitespace
    - Removes HTML formatting tags (but keeps content)
    - Decodes HTML entities

    Args:
        cell: The table cell content to normalize.

    Returns:
        The normalized cell content.

    Examples:
        >>> normalize_table_cell("  <strong>text</strong>  ")
        'text'
        >>> normalize_table_cell("&nbsp;value&nbsp;")
        'value'
    """
    if not cell:
        return ""

    # Decode HTML entities
    cell = html.unescape(cell)

    # Remove HTML tags but keep content
    cell = HTML_TAG_PATTERN.sub('', cell)

    # Strip whitespace
    cell = cell.strip()

    return cell


def normalize_heading(heading: str) -> str:
    """Normalize a heading for comparison and anchor generation.

    Performs the following normalizations:
    - Removes leading numbers and dots (e.g., "2.1.3 Foo" -> "Foo")
    - Strips whitespace
    - Converts to lowercase
    - Removes punctuation except hyphens
    - Replaces spaces with hyphens

    Args:
        heading: The heading text to normalize.

    Returns:
        The normalized heading suitable for comparison or as an anchor.

    Examples:
        >>> normalize_heading("2.1.3 Test Setup")
        'test-setup'
        >>> normalize_heading("Hello, World!")
        'hello-world'
    """
    if not heading:
        return ""

    # Remove section number prefix
    heading = SECTION_NUMBER_PATTERN.sub('', heading)

    # Strip whitespace
    heading = heading.strip()

    # Convert to lowercase
    heading = heading.lower()

    # Remove punctuation except hyphens
    heading = PUNCTUATION_EXCEPT_HYPHEN.sub('', heading)

    # Replace whitespace with hyphens
    heading = MULTI_WHITESPACE.sub('-', heading)

    # Collapse multiple hyphens
    heading = MULTI_HYPHEN.sub('-', heading)

    # Remove leading/trailing hyphens
    heading = heading.strip('-')

    return heading


def extract_number_prefix(heading: str) -> Optional[str]:
    """Extract section number prefix from a heading.

    Extracts section numbers like "2.1.3" from headings.

    Args:
        heading: The heading text to extract from.

    Returns:
        The section number string if found, None otherwise.

    Examples:
        >>> extract_number_prefix("2.1.3 Test Setup")
        '2.1.3'
        >>> extract_number_prefix("1. Introduction")
        '1'
        >>> extract_number_prefix("No Number Here") is None
        True
    """
    if not heading:
        return None

    match = SECTION_NUMBER_PATTERN.match(heading.strip())
    if match:
        # Remove trailing dot if present
        number = match.group(1).rstrip('.')
        return number if number else None

    return None


def normalize_link(href: str, base_path: str = "") -> str:
    """Normalize a link/href for comparison.

    Performs the following normalizations:
    - Resolves relative paths (../path/ patterns)
    - Removes trailing slashes (except for root)
    - Normalizes fragment identifiers (#section-name)
    - Handles query strings

    Args:
        href: The href/link to normalize.
        base_path: Optional base path for resolving relative links.

    Returns:
        The normalized link string.

    Examples:
        >>> normalize_link("../section/page.html#anchor")
        '../section/page.html#anchor'
        >>> normalize_link("/path/to/page/", "/docs")
        '/path/to/page'
        >>> normalize_link("page.html#Section-Name")
        'page.html#section-name'
    """
    if not href:
        return ""

    # Split fragment identifier
    fragment = ""
    if '#' in href:
        href, fragment = href.split('#', 1)
        # Normalize fragment to lowercase
        fragment = fragment.lower()

    # Split query string (preserve but normalize)
    query = ""
    if '?' in href:
        href, query = href.split('?', 1)

    # Handle absolute URLs (don't modify scheme/host)
    if href.startswith(('http://', 'https://', '//')):
        # Just normalize the path portion
        pass
    elif base_path and not href.startswith('/'):
        # Resolve relative path against base
        try:
            base = PurePosixPath(base_path)
            if not base_path.endswith('/'):
                base = base.parent
            resolved = base / href
            # Normalize the path (handles ..)
            parts: List[str] = []
            for part in resolved.parts:
                if part == '..':
                    if parts and parts[-1] != '..' and parts[-1] != '/':
                        parts.pop()
                    elif not parts:
                        # Can't go above root, just skip
                        pass
                    else:
                        parts.append(part)
                elif part != '.':
                    parts.append(part)
            # Build path, ensuring we don't create double slashes
            if parts and parts[0] == '/':
                href = '/' + '/'.join(parts[1:]) if len(parts) > 1 else '/'
            else:
                href = '/'.join(parts) if parts else '/'
        except Exception:
            pass  # Keep original on error

    # Remove trailing slash (except for root '/')
    if href != '/' and href.endswith('/'):
        href = href.rstrip('/')

    # Reconstruct the URL
    result = href
    if query:
        result += '?' + query
    if fragment:
        result += '#' + fragment

    return result


def similarity_ratio(text1: str, text2: str) -> float:
    """Calculate similarity ratio between two texts.

    Uses difflib.SequenceMatcher to calculate similarity.
    Both texts are normalized before comparison.

    Args:
        text1: First text to compare.
        text2: Second text to compare.

    Returns:
        A float between 0.0 (completely different) and 1.0 (identical).

    Examples:
        >>> similarity_ratio("hello world", "hello world")
        1.0
        >>> similarity_ratio("hello", "hallo")
        0.8
        >>> similarity_ratio("abc", "xyz")
        0.0
    """
    # Normalize both texts
    norm1 = normalize_text(text1)
    norm2 = normalize_text(text2)

    # Handle empty strings
    if not norm1 and not norm2:
        return 1.0
    if not norm1 or not norm2:
        return 0.0

    # Use SequenceMatcher for similarity
    matcher = difflib.SequenceMatcher(None, norm1, norm2)
    return matcher.ratio()


def fuzzy_match(
    query: str,
    candidates: List[str],
    threshold: float = 0.85
) -> Optional[str]:
    """Find the best matching candidate above a similarity threshold.

    Args:
        query: The string to match.
        candidates: List of candidate strings to match against.
        threshold: Minimum similarity ratio required (default 0.85).

    Returns:
        The best matching candidate if above threshold, None otherwise.

    Examples:
        >>> fuzzy_match("test setup", ["Test Setup", "Test Teardown"])
        'Test Setup'
        >>> fuzzy_match("xyz", ["abc", "def"], threshold=0.9) is None
        True
    """
    if not query or not candidates:
        return None

    best_match: Optional[str] = None
    best_ratio: float = 0.0

    for candidate in candidates:
        ratio = similarity_ratio(query, candidate)
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = candidate

    if best_ratio >= threshold:
        return best_match

    return None


# ============================================================================
# Legacy functions (preserved for backward compatibility)
# ============================================================================

def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in text.

    Collapses multiple whitespace characters into single spaces
    and strips leading/trailing whitespace.

    Args:
        text: The text to normalize.

    Returns:
        Text with normalized whitespace.
    """
    if not text:
        return ""
    # Replace multiple whitespace (including newlines) with single space
    return MULTI_WHITESPACE.sub(' ', text).strip()


def strip_formatting(text: str) -> str:
    """Remove common formatting markers from text.

    Removes markdown formatting like **, *, `, etc.

    Args:
        text: The text to strip formatting from.

    Returns:
        Text with formatting removed.
    """
    if not text:
        return ""
    # Remove markdown bold/italic
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)
    # Remove inline code
    text = re.sub(r'`([^`]+)`', r'\1', text)
    # Remove links but keep text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    return text


def normalize_title(title: str) -> str:
    """Normalize a section title for display.

    Args:
        title: The title to normalize.

    Returns:
        Normalized title.
    """
    if not title:
        return ""
    # Strip formatting first
    title = strip_formatting(title)
    # Normalize whitespace
    title = normalize_whitespace(title)
    return title


def normalize_key(title: str) -> str:
    """Normalize a title into a comparison key.

    Creates a lowercase, stripped version suitable for matching.
    Removes section numbers if present.

    Args:
        title: The title to normalize.

    Returns:
        Normalized key for comparison.
    """
    if not title:
        return ""
    # First normalize the title
    key = normalize_title(title)
    # Convert to lowercase
    key = key.lower()
    # Remove leading section numbers (e.g., "2.1.3 Title" -> "title")
    key = re.sub(r'^[\d.]+\s*', '', key)
    # Normalize unicode characters
    key = unicodedata.normalize('NFKC', key)
    # Remove special characters except alphanumeric and spaces
    key = re.sub(r'[^\w\s-]', '', key)
    # Replace spaces with hyphens for URL-friendly keys
    key = MULTI_WHITESPACE.sub('-', key)
    # Remove duplicate hyphens
    key = MULTI_HYPHEN.sub('-', key)
    # Strip leading/trailing hyphens
    key = key.strip('-')
    return key


def extract_section_number(title: str) -> Optional[str]:
    """Extract section number prefix from a title.

    Args:
        title: The title that may contain a section number.

    Returns:
        The section number if found, None otherwise.
    """
    if not title:
        return None
    # Match patterns like "2.1.3", "2.1", "2" at the start
    match = re.match(r'^([\d]+(?:\.[\d]+)*)\s', title)
    if match:
        return match.group(1)
    return None


# ============================================================================
# Additional utility functions
# ============================================================================

def strip_html_tags(text: str) -> str:
    """Remove all HTML tags from text, keeping the content.

    Args:
        text: Text containing HTML tags.

    Returns:
        Text with HTML tags removed.
    """
    return HTML_TAG_PATTERN.sub('', text) if text else ""


def collapse_whitespace(text: str) -> str:
    """Collapse multiple whitespace characters to single space.

    Args:
        text: Text with potentially multiple whitespace.

    Returns:
        Text with collapsed whitespace.
    """
    return MULTI_WHITESPACE.sub(' ', text).strip() if text else ""


def normalize_line_endings(text: str) -> str:
    """Normalize all line endings to Unix-style (\\n).

    Args:
        text: Text with potentially mixed line endings.

    Returns:
        Text with normalized line endings.
    """
    return text.replace('\r\n', '\n').replace('\r', '\n') if text else ""
