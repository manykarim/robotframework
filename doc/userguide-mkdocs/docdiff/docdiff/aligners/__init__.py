"""Section alignment utilities for matching source and target sections.

This module provides multi-stage alignment algorithms to match sections
between HTML (old) and Markdown (new) documentation with different key formats.
"""

import hashlib
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any

from docdiff.models import AlignmentResult, Section


@dataclass
class AlignmentConfig:
    """Configuration for section alignment."""
    fuzzy_threshold: float = 0.8
    number_weight: float = 0.3
    key_weight: float = 0.4
    title_weight: float = 0.3
    allow_reordering: bool = True
    # Stage-specific thresholds
    title_similarity_threshold: float = 0.85
    parent_context_threshold: float = 0.75
    content_similarity_threshold: float = 0.7


def normalize_section_key(heading: str) -> str:
    """Generate consistent section keys for matching.

    This function normalizes heading text to create a key that works
    across HTML and Markdown formats by:
    - Removing section number prefixes (e.g., "2.1.3")
    - Converting to lowercase
    - Removing punctuation except hyphens
    - Replacing spaces with hyphens
    - Removing path components (e.g., "getting-started/introduction" -> "introduction")

    Args:
        heading: The heading text to normalize.

    Returns:
        A normalized key string suitable for matching.

    Examples:
        >>> normalize_section_key("2.1.3 Test Setup")
        'test-setup'
        >>> normalize_section_key("Why Robot Framework?")
        'why-robot-framework'
        >>> normalize_section_key("getting-started/introduction")
        'introduction'
    """
    if not heading:
        return ""

    # Remove number prefixes like "2.1.3" or "2.1.3."
    heading = re.sub(r'^\d+(\.\d+)*\.?\s*', '', heading)

    # If the key contains path separators, extract the last component
    # This handles keys like "getting-started/introduction"
    if '/' in heading:
        heading = heading.split('/')[-1]

    # Lowercase
    key = heading.lower()

    # Replace underscores with hyphens for consistency
    key = key.replace('_', '-')

    # Remove punctuation except hyphens
    key = re.sub(r'[^\w\s-]', '', key)

    # Replace spaces with hyphens
    key = re.sub(r'\s+', '-', key)

    # Collapse multiple hyphens
    key = re.sub(r'-+', '-', key)

    return key.strip('-')


def _compute_title_similarity(title1: str, title2: str) -> float:
    """Compute similarity ratio between two titles.

    Args:
        title1: First title to compare.
        title2: Second title to compare.

    Returns:
        Similarity ratio between 0.0 and 1.0.
    """
    if not title1 or not title2:
        return 0.0

    # Normalize both titles for comparison
    norm1 = normalize_section_key(title1)
    norm2 = normalize_section_key(title2)

    if not norm1 or not norm2:
        return 0.0

    # Exact match after normalization
    if norm1 == norm2:
        return 1.0

    return SequenceMatcher(None, norm1, norm2).ratio()


def _compute_content_hash(section: Section) -> str:
    """Compute a hash of section content for matching.

    Args:
        section: The section to hash.

    Returns:
        A hash string of the section's content.
    """
    content_parts = []

    # Include title
    if section.title:
        content_parts.append(normalize_section_key(section.title))

    # Include content
    if section.content:
        # Normalize content: lowercase, collapse whitespace, first 500 chars
        content = section.content.lower()
        content = re.sub(r'\s+', ' ', content)[:500]
        content_parts.append(content)

    # Include blocks content
    for block in section.blocks:
        if block.content:
            block_content = block.content.lower()
            block_content = re.sub(r'\s+', ' ', block_content)[:200]
            content_parts.append(block_content)

    combined = '|'.join(content_parts)
    return hashlib.md5(combined.encode()).hexdigest()[:16]


def _flatten_sections(sections: list[Section], parent_key: str | None = None) -> list[Section]:
    """Recursively flatten nested section hierarchy.

    Args:
        sections: List of sections that may have nested children.
        parent_key: Key of the parent section (for context).

    Returns:
        Flat list of all sections including nested children.
    """
    result: list[Section] = []

    for section in sections:
        # Set parent_key if not already set
        if parent_key and not section.parent_key:
            section.parent_key = parent_key

        result.append(section)

        # Recursively flatten children (prefer subsections, fallback to children)
        children = section.subsections if section.subsections else section.children
        if children:
            result.extend(_flatten_sections(children, section.key))

    return result


def _stage1_exact_number_match(
    source_sections: list[Section],
    target_sections: list[Section],
    matched_source: set[str],
    matched_target: set[str],
    stats: dict[str, int],
) -> list[tuple[Section, Section]]:
    """Stage 1: Match sections by exact section number (confidence: 1.0).

    This is the highest confidence match as section numbers are explicit.
    """
    matches: list[tuple[Section, Section]] = []

    # Build index of target sections by number
    target_by_number: dict[str, Section] = {}
    for section in target_sections:
        if section.number and section.key not in matched_target:
            target_by_number[section.number] = section

    for source in source_sections:
        if not source.number:
            continue
        if source.key in matched_source:
            continue

        target = target_by_number.get(source.number)
        if target and target.key not in matched_target:
            matches.append((source, target))
            matched_source.add(source.key)
            matched_target.add(target.key)
            stats['exact_number'] = stats.get('exact_number', 0) + 1

    return matches


def _stage2_exact_key_match(
    source_sections: list[Section],
    target_sections: list[Section],
    matched_source: set[str],
    matched_target: set[str],
    stats: dict[str, int],
) -> list[tuple[Section, Section]]:
    """Stage 2: Match sections by normalized key (confidence: 0.95).

    Uses normalize_section_key for consistent key comparison across formats.
    """
    matches: list[tuple[Section, Section]] = []

    # Build index of target sections by normalized key
    target_by_key: dict[str, Section] = {}
    for section in target_sections:
        if section.key not in matched_target:
            norm_key = normalize_section_key(section.key)
            if norm_key:
                # Also try normalizing the title
                norm_title = normalize_section_key(section.title)
                target_by_key[norm_key] = section
                if norm_title and norm_title != norm_key:
                    target_by_key[norm_title] = section

    for source in source_sections:
        if source.key in matched_source:
            continue

        # Try matching by normalized source key
        norm_source_key = normalize_section_key(source.key)
        target = target_by_key.get(norm_source_key)

        # Also try normalizing the source title
        if not target:
            norm_source_title = normalize_section_key(source.title)
            target = target_by_key.get(norm_source_title)

        if target and target.key not in matched_target:
            matches.append((source, target))
            matched_source.add(source.key)
            matched_target.add(target.key)
            stats['exact_key'] = stats.get('exact_key', 0) + 1

    return matches


def _stage3_fuzzy_title_match(
    source_sections: list[Section],
    target_sections: list[Section],
    matched_source: set[str],
    matched_target: set[str],
    stats: dict[str, int],
    threshold: float = 0.85,
) -> list[tuple[Section, Section]]:
    """Stage 3: Match sections by fuzzy title similarity (confidence: 0.9).

    Uses SequenceMatcher with threshold >= 0.85 (configurable).
    """
    matches: list[tuple[Section, Section]] = []

    # Get unmatched sections
    unmatched_source = [s for s in source_sections if s.key not in matched_source]
    unmatched_target = [s for s in target_sections if s.key not in matched_target]

    for source in unmatched_source:
        best_match: Section | None = None
        best_score = 0.0

        for target in unmatched_target:
            if target.key in matched_target:
                continue

            # Compare both keys and titles, use the better score
            key_score = _compute_title_similarity(source.key, target.key)
            title_score = _compute_title_similarity(source.title, target.title)
            score = max(key_score, title_score)

            if score >= threshold and score > best_score:
                best_match = target
                best_score = score

        if best_match:
            matches.append((source, best_match))
            matched_source.add(source.key)
            matched_target.add(best_match.key)
            stats['fuzzy'] = stats.get('fuzzy', 0) + 1

    return matches


def _stage4_parent_context_match(
    source_sections: list[Section],
    target_sections: list[Section],
    matched_source: set[str],
    matched_target: set[str],
    stats: dict[str, int],
    threshold: float = 0.75,
) -> list[tuple[Section, Section]]:
    """Stage 4: Match sections by parent context + title (confidence: 0.8).

    Matches sections that have similar parents and child titles.
    """
    matches: list[tuple[Section, Section]] = []

    # Get unmatched sections
    unmatched_source = [s for s in source_sections if s.key not in matched_source]
    unmatched_target = [s for s in target_sections if s.key not in matched_target]

    # Group by parent key
    source_by_parent: dict[str | None, list[Section]] = {}
    target_by_parent: dict[str | None, list[Section]] = {}

    for section in unmatched_source:
        parent = section.parent_key
        if parent not in source_by_parent:
            source_by_parent[parent] = []
        source_by_parent[parent].append(section)

    for section in unmatched_target:
        parent = section.parent_key
        if parent not in target_by_parent:
            target_by_parent[parent] = []
        target_by_parent[parent].append(section)

    # Match within same parent context
    for parent_key, source_children in source_by_parent.items():
        if parent_key is None:
            continue  # Skip root-level sections (no parent context)

        # Find matching parent keys (exact or fuzzy)
        matching_parents: list[str | None] = []
        for target_parent in target_by_parent:
            if target_parent is None:
                continue
            if parent_key == target_parent:
                matching_parents.append(target_parent)
            elif _compute_title_similarity(parent_key, target_parent) >= 0.8:
                matching_parents.append(target_parent)

        for matching_parent in matching_parents:
            target_children = target_by_parent.get(matching_parent, [])

            for source_child in source_children:
                if source_child.key in matched_source:
                    continue

                for target_child in target_children:
                    if target_child.key in matched_target:
                        continue

                    # Compare titles within parent context
                    score = _compute_title_similarity(source_child.title, target_child.title)

                    if score >= threshold:
                        matches.append((source_child, target_child))
                        matched_source.add(source_child.key)
                        matched_target.add(target_child.key)
                        stats['parent_context'] = stats.get('parent_context', 0) + 1
                        break

    return matches


def _stage5_content_hash_match(
    source_sections: list[Section],
    target_sections: list[Section],
    matched_source: set[str],
    matched_target: set[str],
    stats: dict[str, int],
    threshold: float = 0.7,
) -> list[tuple[Section, Section]]:
    """Stage 5: Match sections by content similarity (confidence: 0.7).

    Uses content hashing and text similarity for sections with similar content.
    """
    matches: list[tuple[Section, Section]] = []

    # Get unmatched sections with content
    unmatched_source = [
        s for s in source_sections
        if s.key not in matched_source and (s.content or s.blocks)
    ]
    unmatched_target = [
        s for s in target_sections
        if s.key not in matched_target and (s.content or s.blocks)
    ]

    # Compute content hashes
    source_hashes: dict[str, Section] = {}
    for section in unmatched_source:
        h = _compute_content_hash(section)
        source_hashes[h] = section

    # Try to match by content hash
    for target in unmatched_target:
        if target.key in matched_target:
            continue

        target_hash = _compute_content_hash(target)
        source = source_hashes.get(target_hash)

        if source and source.key not in matched_source:
            matches.append((source, target))
            matched_source.add(source.key)
            matched_target.add(target.key)
            stats['content_hash'] = stats.get('content_hash', 0) + 1

    # For remaining unmatched, try fuzzy content comparison
    still_unmatched_source = [s for s in unmatched_source if s.key not in matched_source]
    still_unmatched_target = [t for t in unmatched_target if t.key not in matched_target]

    for source in still_unmatched_source:
        best_match: Section | None = None
        best_score = 0.0

        for target in still_unmatched_target:
            if target.key in matched_target:
                continue

            # Compare content similarity
            source_content = source.content or ''
            target_content = target.content or ''

            if source_content and target_content:
                # Normalize content for comparison
                source_norm = re.sub(r'\s+', ' ', source_content.lower())[:1000]
                target_norm = re.sub(r'\s+', ' ', target_content.lower())[:1000]

                score = SequenceMatcher(None, source_norm, target_norm).ratio()

                if score >= threshold and score > best_score:
                    best_match = target
                    best_score = score

        if best_match:
            matches.append((source, best_match))
            matched_source.add(source.key)
            matched_target.add(best_match.key)
            stats['content_similarity'] = stats.get('content_similarity', 0) + 1

    return matches


def align_sections(
    source_sections: list[Section],
    target_sections: list[Section],
    config: AlignmentConfig | None = None,
) -> AlignmentResult:
    """Align source sections with target sections using multi-stage algorithm.

    The alignment proceeds in stages with decreasing confidence:
    1. EXACT NUMBER MATCH: Match by section number prefix (confidence: 1.0)
    2. EXACT KEY MATCH: Match by normalized key (confidence: 0.95)
    3. FUZZY TITLE MATCH: Use SequenceMatcher >= 0.85 (confidence: 0.9)
    4. PARENT CONTEXT MATCH: Match by parent section + title (confidence: 0.8)
    5. CONTENT HASH MATCH: Match by content similarity (confidence: 0.7)

    Args:
        source_sections: Sections from the source (old/HTML) document
        target_sections: Sections from the target (new/Markdown) document
        config: Alignment configuration

    Returns:
        AlignmentResult with matched pairs and unmatched sections
    """
    if config is None:
        config = AlignmentConfig()

    # Flatten nested structures
    flat_source = _flatten_sections(source_sections)
    flat_target = _flatten_sections(target_sections)

    # Track matched sections
    matched_source: set[str] = set()
    matched_target: set[str] = set()

    # Statistics
    stats: dict[str, int] = {
        'exact_number': 0,
        'exact_key': 0,
        'fuzzy': 0,
        'parent_context': 0,
        'content_hash': 0,
        'content_similarity': 0,
        'unmatched_source': 0,
        'unmatched_target': 0,
    }

    # Collect all matches
    all_matches: list[tuple[Section, Section]] = []

    # Stage 1: Exact number match (highest confidence)
    all_matches.extend(_stage1_exact_number_match(
        flat_source, flat_target, matched_source, matched_target, stats
    ))

    # Stage 2: Exact normalized key match
    all_matches.extend(_stage2_exact_key_match(
        flat_source, flat_target, matched_source, matched_target, stats
    ))

    # Stage 3: Fuzzy title match
    all_matches.extend(_stage3_fuzzy_title_match(
        flat_source, flat_target, matched_source, matched_target, stats,
        threshold=config.title_similarity_threshold
    ))

    # Stage 4: Parent context match
    all_matches.extend(_stage4_parent_context_match(
        flat_source, flat_target, matched_source, matched_target, stats,
        threshold=config.parent_context_threshold
    ))

    # Stage 5: Content hash/similarity match
    all_matches.extend(_stage5_content_hash_match(
        flat_source, flat_target, matched_source, matched_target, stats,
        threshold=config.content_similarity_threshold
    ))

    # Collect unmatched sections
    source_only: list[Section] = []
    target_only: list[Section] = []

    for section in flat_source:
        if section.key not in matched_source:
            source_only.append(section)
            stats['unmatched_source'] += 1

    for section in flat_target:
        if section.key not in matched_target:
            target_only.append(section)
            stats['unmatched_target'] += 1

    return AlignmentResult(
        matched=all_matches,
        source_only=source_only,
        target_only=target_only,
        match_stats=stats,
    )


def find_missing_sections(
    source_sections: list[Section],
    target_sections: list[Section],
    config: AlignmentConfig | None = None,
) -> list[Section]:
    """Find sections that exist in source but not in target.

    Args:
        source_sections: Sections from the source document
        target_sections: Sections from the target document
        config: Alignment configuration

    Returns:
        List of sections that couldn't be matched in target
    """
    result = align_sections(source_sections, target_sections, config)
    return result.source_only


def find_extra_sections(
    source_sections: list[Section],
    target_sections: list[Section],
    config: AlignmentConfig | None = None,
) -> list[Section]:
    """Find sections that exist in target but not in source.

    Args:
        source_sections: Sections from the source document
        target_sections: Sections from the target document
        config: Alignment configuration

    Returns:
        List of sections in target that don't have source equivalents
    """
    result = align_sections(source_sections, target_sections, config)
    return result.target_only


def get_alignment_statistics(result: AlignmentResult) -> dict[str, Any]:
    """Get detailed statistics about the alignment.

    Args:
        result: The alignment result to analyze

    Returns:
        Dictionary with alignment statistics
    """
    total_source = len(result.matched) + len(result.source_only)
    total_target = len(result.matched) + len(result.target_only)

    stats = {
        'total_source_sections': total_source,
        'total_target_sections': total_target,
        'matched_sections': len(result.matched),
        'source_only': len(result.source_only),
        'target_only': len(result.target_only),
        'match_rate': result.get_match_rate(),
        'match_breakdown': result.match_stats.copy(),
    }

    return stats


def suggest_matches(
    unmatched_source: list[Section],
    unmatched_target: list[Section],
    config: AlignmentConfig | None = None,
) -> list[tuple[Section, Section, float]]:
    """Suggest potential matches for unmatched sections.

    Returns matches below the normal threshold that might still be related.

    Args:
        unmatched_source: Source sections without matches
        unmatched_target: Target sections without matches
        config: Alignment configuration

    Returns:
        List of (source, target, score) tuples for potential matches
    """
    if config is None:
        config = AlignmentConfig()

    suggestions: list[tuple[Section, Section, float]] = []

    # Lower threshold for suggestions (half of normal)
    suggestion_threshold = config.fuzzy_threshold * 0.5

    for source in unmatched_source:
        for target in unmatched_target:
            # Compute various similarity scores
            key_score = _compute_title_similarity(source.key, target.key)
            title_score = _compute_title_similarity(source.title, target.title)

            # Use the best score
            score = max(key_score, title_score)

            if score >= suggestion_threshold:
                suggestions.append((source, target, score))

    # Sort by score descending
    suggestions.sort(key=lambda x: x[2], reverse=True)

    return suggestions


# Re-export from section_aligner for advanced usage
from docdiff.aligners.section_aligner import (
    SectionAlignment,
    SectionIndex,
    build_section_index,
    flatten_sections,
    compute_alignment_stats,
    align_sections as align_sections_detailed,
    find_missing_sections as find_missing_detailed,
    find_extra_sections as find_extra_detailed,
    MATCH_EXACT_NUMBER,
    MATCH_EXACT_TITLE,
    MATCH_FUZZY_TITLE,
    MATCH_PARENT_CONTEXT,
    MATCH_UNMATCHED,
)
