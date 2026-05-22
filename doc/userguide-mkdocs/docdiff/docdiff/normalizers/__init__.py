"""Text normalization utilities for comparison."""

import html
import re
from difflib import SequenceMatcher


def normalize_text(text: str) -> str:
    """Normalize text for comparison.

    - Converts HTML entities to characters
    - Normalizes whitespace
    - Strips leading/trailing whitespace
    - Converts to lowercase for comparison
    """
    # Decode HTML entities
    text = html.unescape(text)

    # Normalize various quote types (curly/smart quotes to straight quotes)
    text = text.replace('\u201c', '"').replace('\u201d', '"')  # left/right double quotes
    text = text.replace('\u2018', "'").replace('\u2019', "'")  # left/right single quotes

    # Normalize dashes
    text = text.replace('–', '-').replace('—', '-')

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)

    # Strip
    text = text.strip()

    return text


def normalize_text_for_comparison(text: str) -> str:
    """Normalize text specifically for comparison (more aggressive)."""
    text = normalize_text(text)

    # Convert to lowercase
    text = text.lower()

    # Remove punctuation for fuzzy matching
    text = re.sub(r'[^\w\s]', '', text)

    return text


def normalize_code(code: str) -> str:
    """Normalize code while preserving structure.

    - Preserves indentation (important for Python, etc.)
    - Normalizes line endings
    - Strips trailing whitespace on each line
    - Removes leading/trailing blank lines
    """
    # Normalize line endings
    code = code.replace('\r\n', '\n').replace('\r', '\n')

    # Strip trailing whitespace on each line while preserving indentation
    lines = code.split('\n')
    lines = [line.rstrip() for line in lines]

    # Remove leading blank lines
    while lines and not lines[0]:
        lines.pop(0)

    # Remove trailing blank lines
    while lines and not lines[-1]:
        lines.pop()

    return '\n'.join(lines)


def normalize_heading(heading: str) -> str:
    """Normalize heading text for matching."""
    # Remove numbering prefix (e.g., "2.1.3 " or "2.1.3. ")
    heading = re.sub(r'^[\d.]+\s*', '', heading)

    # Normalize text
    heading = normalize_text(heading)

    return heading


def generate_heading_key(heading: str) -> str:
    """Generate a normalized key for heading matching."""
    # Start with normalized heading
    key = normalize_heading(heading)

    # Convert to lowercase
    key = key.lower()

    # Remove non-alphanumeric characters except spaces and hyphens
    key = re.sub(r'[^\w\s-]', '', key)

    # Replace spaces with hyphens
    key = re.sub(r'\s+', '-', key)

    # Remove consecutive hyphens
    key = re.sub(r'-+', '-', key)

    # Strip leading/trailing hyphens
    key = key.strip('-')

    return key


def similarity_ratio(text1: str, text2: str) -> float:
    """Calculate similarity ratio between two texts.

    Returns a value between 0.0 (completely different) and 1.0 (identical).
    """
    if not text1 and not text2:
        return 1.0
    if not text1 or not text2:
        return 0.0

    # Normalize for comparison
    norm1 = normalize_text_for_comparison(text1)
    norm2 = normalize_text_for_comparison(text2)

    matcher = SequenceMatcher(None, norm1, norm2)
    return matcher.ratio()


def fuzzy_match(text1: str, text2: str, threshold: float = 0.8) -> bool:
    """Check if two texts are a fuzzy match.

    Args:
        text1: First text to compare
        text2: Second text to compare
        threshold: Minimum similarity ratio (0.0 to 1.0)

    Returns:
        True if similarity is at or above threshold
    """
    return similarity_ratio(text1, text2) >= threshold


def extract_words(text: str) -> list[str]:
    """Extract words from text for comparison."""
    text = normalize_text(text)
    words = re.findall(r'\b\w+\b', text.lower())
    return words


def word_overlap_ratio(text1: str, text2: str) -> float:
    """Calculate the word overlap ratio between two texts.

    Returns the Jaccard similarity coefficient.
    """
    words1 = set(extract_words(text1))
    words2 = set(extract_words(text2))

    if not words1 and not words2:
        return 1.0
    if not words1 or not words2:
        return 0.0

    intersection = words1 & words2
    union = words1 | words2

    return len(intersection) / len(union)


def normalize_table_cell(cell: str) -> str:
    """Normalize a table cell value."""
    cell = normalize_text(cell)
    # Remove markdown formatting
    cell = re.sub(r'\*\*([^*]+)\*\*', r'\1', cell)  # Bold
    cell = re.sub(r'\*([^*]+)\*', r'\1', cell)  # Italic
    cell = re.sub(r'`([^`]+)`', r'\1', cell)  # Code
    return cell


def normalize_list_item(item: str) -> str:
    """Normalize a list item."""
    # Remove list markers
    item = re.sub(r'^[\s]*[-*+]\s*', '', item)
    item = re.sub(r'^[\s]*\d+\.\s*', '', item)
    return normalize_text(item)


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
    return re.sub(r'\s+', ' ', text).strip()


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
    # First normalize the text
    key = normalize_text(title)
    # Convert to lowercase
    key = key.lower()
    # Remove leading section numbers (e.g., "2.1.3 Title" -> "title")
    key = re.sub(r'^[\d.]+\s*', '', key)
    # Remove special characters except alphanumeric and spaces
    key = re.sub(r'[^\w\s-]', '', key)
    # Replace spaces with hyphens for URL-friendly keys
    key = re.sub(r'\s+', '-', key)
    # Remove duplicate hyphens
    key = re.sub(r'-+', '-', key)
    # Strip leading/trailing hyphens
    key = key.strip('-')
    return key
