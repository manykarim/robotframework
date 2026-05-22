"""Section alignment algorithms for comparing old HTML and new Markdown docs.

This module provides multi-stage alignment algorithms to match sections
between documents with different formats.
"""

import difflib
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from docdiff.models import Section
from docdiff.normalizers import normalize_key


# Match type constants
MATCH_EXACT_NUMBER = "exact_number"
MATCH_EXACT_TITLE = "exact_title"
MATCH_FUZZY_TITLE = "fuzzy_title"
MATCH_PARENT_CONTEXT = "parent_context"
MATCH_UNMATCHED = "unmatched"


@dataclass
class SectionAlignment:
    """Represents an alignment between an old and new section.

    Attributes:
        old_section: Section from the old (HTML) document, or None if added.
        new_section: Section from the new (Markdown) document, or None if removed.
        confidence: Confidence score between 0.0 and 1.0.
        match_type: Type of match that was used to align these sections.
    """
    old_section: Optional[Section]
    new_section: Optional[Section]
    confidence: float
    match_type: str

    def __post_init__(self) -> None:
        """Validate confidence is in valid range."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")

    @property
    def is_matched(self) -> bool:
        """Return True if both sections are present (matched)."""
        return self.old_section is not None and self.new_section is not None

    @property
    def is_missing(self) -> bool:
        """Return True if only old section present (removed in new)."""
        return self.old_section is not None and self.new_section is None

    @property
    def is_extra(self) -> bool:
        """Return True if only new section present (added in new)."""
        return self.old_section is None and self.new_section is not None


@dataclass
class SectionIndex:
    """Index structure for fast section lookup.

    Attributes:
        by_number: Sections indexed by their section number (e.g., "2.1.3").
        by_key: Sections indexed by their normalized key.
        by_title: Sections indexed by their original title.
    """
    by_number: Dict[str, Section]
    by_key: Dict[str, Section]
    by_title: Dict[str, Section]


def build_section_index(sections: List[Section]) -> SectionIndex:
    """Build indexes for fast section lookup.

    Creates multiple index structures to support different matching strategies.
    Handles nested sections recursively by flattening first.

    Args:
        sections: List of sections to index (may be nested).

    Returns:
        SectionIndex with by_number, by_key, and by_title dictionaries.
    """
    by_number: Dict[str, Section] = {}
    by_key: Dict[str, Section] = {}
    by_title: Dict[str, Section] = {}

    # Flatten sections to handle nested structure
    flat_sections = flatten_sections(sections)

    for section in flat_sections:
        # Index by section number if present
        if section.number:
            by_number[section.number] = section

        # Index by normalized key
        if section.key:
            by_key[section.key] = section

        # Index by original title
        if section.title:
            by_title[section.title] = section

    return SectionIndex(
        by_number=by_number,
        by_key=by_key,
        by_title=by_title,
    )


def flatten_sections(sections: List[Section]) -> List[Section]:
    """Recursively flatten nested section hierarchy.

    Preserves parent context in the sections' parent_key attribute.

    Args:
        sections: List of sections that may have nested children.

    Returns:
        Flat list of all sections including nested children.
    """
    result: List[Section] = []

    def _flatten(section_list: List[Section], parent_key: Optional[str] = None) -> None:
        for section in section_list:
            # Update parent_key if we're in a nested context
            if parent_key and not section.parent_key:
                section.parent_key = parent_key
            result.append(section)

            # Recursively flatten children
            if section.children:
                _flatten(section.children, section.key)

    _flatten(sections)
    return result


def _compute_similarity(text1: str, text2: str) -> float:
    """Compute similarity ratio between two strings using SequenceMatcher.

    Args:
        text1: First string to compare.
        text2: Second string to compare.

    Returns:
        Similarity ratio between 0.0 and 1.0.
    """
    if not text1 or not text2:
        return 0.0
    return difflib.SequenceMatcher(None, text1, text2).ratio()


def _match_by_number(
    old_sections: List[Section],
    new_sections: List[Section],
    matched_old: Set[str],
    matched_new: Set[str],
) -> List[SectionAlignment]:
    """Stage 1: Match sections by exact section number.

    This is the highest confidence match as section numbers are explicit.

    Args:
        old_sections: Flattened list of old sections.
        new_sections: Flattened list of new sections.
        matched_old: Set of already matched old section keys (modified in place).
        matched_new: Set of already matched new section keys (modified in place).

    Returns:
        List of alignments from number matching.
    """
    alignments: List[SectionAlignment] = []
    new_index = build_section_index(new_sections)

    for old_section in old_sections:
        if not old_section.number:
            continue
        if old_section.key in matched_old:
            continue

        new_section = new_index.by_number.get(old_section.number)
        if new_section and new_section.key not in matched_new:
            alignments.append(SectionAlignment(
                old_section=old_section,
                new_section=new_section,
                confidence=1.0,
                match_type=MATCH_EXACT_NUMBER,
            ))
            matched_old.add(old_section.key)
            matched_new.add(new_section.key)

    return alignments


def _match_by_key(
    old_sections: List[Section],
    new_sections: List[Section],
    matched_old: Set[str],
    matched_new: Set[str],
) -> List[SectionAlignment]:
    """Stage 2: Match sections by exact normalized key.

    Args:
        old_sections: Flattened list of old sections.
        new_sections: Flattened list of new sections.
        matched_old: Set of already matched old section keys (modified in place).
        matched_new: Set of already matched new section keys (modified in place).

    Returns:
        List of alignments from key matching.
    """
    alignments: List[SectionAlignment] = []
    new_index = build_section_index(new_sections)

    for old_section in old_sections:
        if old_section.key in matched_old:
            continue

        new_section = new_index.by_key.get(old_section.key)
        if new_section and new_section.key not in matched_new:
            alignments.append(SectionAlignment(
                old_section=old_section,
                new_section=new_section,
                confidence=0.95,
                match_type=MATCH_EXACT_TITLE,
            ))
            matched_old.add(old_section.key)
            matched_new.add(new_section.key)

    return alignments


def _match_by_fuzzy(
    old_sections: List[Section],
    new_sections: List[Section],
    matched_old: Set[str],
    matched_new: Set[str],
    threshold: float = 0.85,
) -> List[SectionAlignment]:
    """Stage 3: Match sections by fuzzy title comparison.

    Uses difflib.SequenceMatcher to find similar titles.

    Args:
        old_sections: Flattened list of old sections.
        new_sections: Flattened list of new sections.
        matched_old: Set of already matched old section keys (modified in place).
        matched_new: Set of already matched new section keys (modified in place).
        threshold: Minimum similarity ratio to consider a match.

    Returns:
        List of alignments from fuzzy matching.
    """
    alignments: List[SectionAlignment] = []

    # Get unmatched sections
    unmatched_old = [s for s in old_sections if s.key not in matched_old]
    unmatched_new = [s for s in new_sections if s.key not in matched_new]

    # Find best fuzzy matches
    for old_section in unmatched_old:
        best_match: Optional[Section] = None
        best_score = 0.0

        for new_section in unmatched_new:
            if new_section.key in matched_new:
                continue

            # Compare normalized keys
            score = _compute_similarity(old_section.key, new_section.key)

            # Also compare titles for better matching
            title_score = _compute_similarity(
                old_section.title.lower(),
                new_section.title.lower()
            )

            # Use the better of the two scores
            final_score = max(score, title_score)

            if final_score >= threshold and final_score > best_score:
                best_match = new_section
                best_score = final_score

        if best_match:
            alignments.append(SectionAlignment(
                old_section=old_section,
                new_section=best_match,
                confidence=best_score,
                match_type=MATCH_FUZZY_TITLE,
            ))
            matched_old.add(old_section.key)
            matched_new.add(best_match.key)

    return alignments


def _match_by_context(
    old_sections: List[Section],
    new_sections: List[Section],
    matched_old: Set[str],
    matched_new: Set[str],
) -> List[SectionAlignment]:
    """Stage 4: Match sections by parent context.

    Matches sections that have the same parent and similar child titles.

    Args:
        old_sections: Flattened list of old sections.
        new_sections: Flattened list of new sections.
        matched_old: Set of already matched old section keys (modified in place).
        matched_new: Set of already matched new section keys (modified in place).

    Returns:
        List of alignments from context matching.
    """
    alignments: List[SectionAlignment] = []

    # Get unmatched sections
    unmatched_old = [s for s in old_sections if s.key not in matched_old]
    unmatched_new = [s for s in new_sections if s.key not in matched_new]

    # Group by parent key
    old_by_parent: Dict[Optional[str], List[Section]] = {}
    new_by_parent: Dict[Optional[str], List[Section]] = {}

    for section in unmatched_old:
        parent = section.parent_key
        if parent not in old_by_parent:
            old_by_parent[parent] = []
        old_by_parent[parent].append(section)

    for section in unmatched_new:
        parent = section.parent_key
        if parent not in new_by_parent:
            new_by_parent[parent] = []
        new_by_parent[parent].append(section)

    # Match within same parent context
    for parent_key, old_children in old_by_parent.items():
        if parent_key is None:
            continue  # Skip root-level sections (no parent context)

        # Look for matching parent key or similar parent key
        matching_parents = []
        if parent_key in new_by_parent:
            matching_parents.append(parent_key)
        else:
            # Try fuzzy match on parent key
            for new_parent in new_by_parent:
                if new_parent and _compute_similarity(parent_key, new_parent) >= 0.8:
                    matching_parents.append(new_parent)

        for matching_parent in matching_parents:
            new_children = new_by_parent.get(matching_parent, [])

            for old_child in old_children:
                if old_child.key in matched_old:
                    continue

                for new_child in new_children:
                    if new_child.key in matched_new:
                        continue

                    # Compare titles within parent context
                    score = _compute_similarity(
                        old_child.title.lower(),
                        new_child.title.lower()
                    )

                    if score >= 0.75:  # Lower threshold for context matches
                        alignments.append(SectionAlignment(
                            old_section=old_child,
                            new_section=new_child,
                            confidence=score * 0.9,  # Slight penalty for context-only match
                            match_type=MATCH_PARENT_CONTEXT,
                        ))
                        matched_old.add(old_child.key)
                        matched_new.add(new_child.key)
                        break

    return alignments


def align_sections(
    old_sections: List[Section],
    new_sections: List[Section],
) -> List[SectionAlignment]:
    """Align sections between old and new documents using multi-stage algorithm.

    The alignment proceeds in stages with decreasing confidence:
    1. EXACT NUMBER MATCH: Match by section number prefix (highest confidence)
    2. EXACT KEY MATCH: Match by normalized title key
    3. FUZZY MATCH: Use difflib.SequenceMatcher with threshold >= 0.85
    4. CONTEXT MATCH: Match by parent section + child title

    Each section is matched at most once. Unmatched sections are included
    in the result with appropriate match_type.

    Args:
        old_sections: List of sections from old (HTML) document.
        new_sections: List of sections from new (Markdown) document.

    Returns:
        List of SectionAlignment objects including matched and unmatched sections.
    """
    # Flatten nested structures
    flat_old = flatten_sections(old_sections)
    flat_new = flatten_sections(new_sections)

    # Track which sections have been matched
    matched_old: Set[str] = set()
    matched_new: Set[str] = set()

    alignments: List[SectionAlignment] = []

    # Stage 1: Exact number match (highest confidence)
    alignments.extend(_match_by_number(flat_old, flat_new, matched_old, matched_new))

    # Stage 2: Exact key match
    alignments.extend(_match_by_key(flat_old, flat_new, matched_old, matched_new))

    # Stage 3: Fuzzy title match
    alignments.extend(_match_by_fuzzy(flat_old, flat_new, matched_old, matched_new))

    # Stage 4: Parent context match
    alignments.extend(_match_by_context(flat_old, flat_new, matched_old, matched_new))

    # Add unmatched old sections (missing in new)
    for section in flat_old:
        if section.key not in matched_old:
            alignments.append(SectionAlignment(
                old_section=section,
                new_section=None,
                confidence=0.0,
                match_type=MATCH_UNMATCHED,
            ))

    # Add unmatched new sections (extra in new)
    for section in flat_new:
        if section.key not in matched_new:
            alignments.append(SectionAlignment(
                old_section=None,
                new_section=section,
                confidence=0.0,
                match_type=MATCH_UNMATCHED,
            ))

    return alignments


def find_missing_sections(alignments: List[SectionAlignment]) -> List[Section]:
    """Find old sections that have no match in new document.

    Args:
        alignments: List of section alignments.

    Returns:
        List of sections from old document that are missing in new.
    """
    return [
        alignment.old_section
        for alignment in alignments
        if alignment.is_missing and alignment.old_section is not None
    ]


def find_extra_sections(alignments: List[SectionAlignment]) -> List[Section]:
    """Find new sections that have no match in old document.

    Args:
        alignments: List of section alignments.

    Returns:
        List of sections from new document that are extra (not in old).
    """
    return [
        alignment.new_section
        for alignment in alignments
        if alignment.is_extra and alignment.new_section is not None
    ]


def compute_alignment_stats(alignments: List[SectionAlignment]) -> Dict:
    """Compute statistics about the alignment results.

    Args:
        alignments: List of section alignments.

    Returns:
        Dictionary with statistics including:
        - total_old: Total sections in old document
        - total_new: Total sections in new document
        - matched_count: Number of matched sections
        - missing_count: Number of sections missing in new
        - extra_count: Number of extra sections in new
        - avg_confidence: Average confidence of matched sections
        - match_type_distribution: Count of each match type
    """
    matched = [a for a in alignments if a.is_matched]
    missing = [a for a in alignments if a.is_missing]
    extra = [a for a in alignments if a.is_extra]

    total_old = len(matched) + len(missing)
    total_new = len(matched) + len(extra)

    # Calculate average confidence of matched sections
    avg_confidence = 0.0
    if matched:
        avg_confidence = sum(a.confidence for a in matched) / len(matched)

    # Count match types
    match_type_distribution: Dict[str, int] = {}
    for alignment in alignments:
        match_type = alignment.match_type
        match_type_distribution[match_type] = match_type_distribution.get(match_type, 0) + 1

    return {
        "total_old": total_old,
        "total_new": total_new,
        "matched_count": len(matched),
        "missing_count": len(missing),
        "extra_count": len(extra),
        "avg_confidence": round(avg_confidence, 4),
        "match_type_distribution": match_type_distribution,
    }
