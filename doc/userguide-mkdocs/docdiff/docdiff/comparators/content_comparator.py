"""Content comparison logic for docdiff.

This module provides functions for comparing different types of content blocks
between documentation versions, computing similarity scores, and generating
findings for discrepancies.
"""

import difflib
from typing import Dict, List, Optional, Set, Tuple

from docdiff.models import (
    Block,
    BlockType,
    Finding,
    Priority,
    Section,
)
from docdiff.normalizers import normalize_whitespace, strip_formatting


# Block type weights for computing overall similarity score
BLOCK_WEIGHTS: Dict[str, float] = {
    "paragraph": 0.35,
    "list": 0.15,
    "code": 0.20,
    "table": 0.15,
    "admonition": 0.10,
    "image": 0.025,
    "link": 0.025,
}

# Similarity threshold below which content differences are flagged
PARAGRAPH_SIMILARITY_THRESHOLD = 0.90


def _get_block_type_str(block: Block) -> str:
    """Extract block type as string from a Block object.

    Args:
        block: The block to get the type from.

    Returns:
        The block type as a lowercase string.
    """
    if isinstance(block.block_type, BlockType):
        return block.block_type.value.lower()
    return str(block.block_type).lower()


def _filter_blocks_by_type(blocks: List[Block], block_type: str) -> List[Block]:
    """Filter blocks by their type.

    Args:
        blocks: List of blocks to filter.
        block_type: The type to filter by (case-insensitive).

    Returns:
        List of blocks matching the specified type.
    """
    block_type_lower = block_type.lower()
    return [b for b in blocks if _get_block_type_str(b) == block_type_lower]


def _compute_text_similarity(old_text: str, new_text: str) -> float:
    """Compute similarity ratio between two text strings.

    Uses difflib.SequenceMatcher to compute the similarity ratio.

    Args:
        old_text: The reference text.
        new_text: The text to compare against.

    Returns:
        Similarity ratio between 0.0 and 1.0.
    """
    if not old_text and not new_text:
        return 1.0
    if not old_text or not new_text:
        return 0.0
    matcher = difflib.SequenceMatcher(None, old_text, new_text)
    return matcher.ratio()


def _normalize_text_for_comparison(text: str) -> str:
    """Normalize text for comparison.

    Applies whitespace normalization and formatting stripping.

    Args:
        text: The text to normalize.

    Returns:
        Normalized text.
    """
    text = strip_formatting(text)
    text = normalize_whitespace(text)
    return text.lower()


def generate_diff_excerpt(
    old_text: str, new_text: str, max_lines: int = 5
) -> str:
    """Generate a truncated unified diff excerpt for findings evidence.

    Uses difflib.unified_diff to generate a diff, then truncates to max_lines.

    Args:
        old_text: The old/reference text.
        new_text: The new text.
        max_lines: Maximum number of diff lines to include (default 5).

    Returns:
        Truncated diff excerpt as a string.
    """
    old_lines = old_text.splitlines(keepends=True) if old_text else []
    new_lines = new_text.splitlines(keepends=True) if new_text else []

    diff_lines = list(difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile="old",
        tofile="new",
        lineterm=""
    ))

    if not diff_lines:
        return ""

    # Truncate to max_lines
    if len(diff_lines) > max_lines:
        truncated = diff_lines[:max_lines]
        truncated.append(f"... ({len(diff_lines) - max_lines} more lines)")
        return "\n".join(line.rstrip() for line in truncated)

    return "\n".join(line.rstrip() for line in diff_lines)


def compare_paragraphs(
    old: List[Block], new: List[Block]
) -> Tuple[float, List[Finding]]:
    """Compare paragraph blocks between old and new content.

    Normalizes text and computes similarity. Flags significant differences
    (similarity < 0.90) as P2 findings.

    Args:
        old: List of paragraph blocks from the old document.
        new: List of paragraph blocks from the new document.

    Returns:
        Tuple of (similarity_score, list_of_findings).
    """
    findings: List[Finding] = []

    # Extract and normalize paragraph content
    old_paragraphs = _filter_blocks_by_type(old, "paragraph")
    new_paragraphs = _filter_blocks_by_type(new, "paragraph")

    if not old_paragraphs and not new_paragraphs:
        return 1.0, findings

    if not old_paragraphs:
        # All paragraphs are new - not necessarily a problem
        return 1.0, findings

    if not new_paragraphs:
        # All paragraphs removed
        findings.append(Finding(
            priority=Priority.P2,
            category="content_missing",
            message="All paragraphs removed from section",
            old_value=f"{len(old_paragraphs)} paragraphs",
            new_value="0 paragraphs",
            block_type="paragraph"
        ))
        return 0.0, findings

    # Compare each old paragraph to find best match in new
    total_similarity = 0.0
    matched_new: Set[int] = set()

    for old_p in old_paragraphs:
        old_text = _normalize_text_for_comparison(old_p.text)
        best_similarity = 0.0
        best_match_idx = -1

        for idx, new_p in enumerate(new_paragraphs):
            if idx in matched_new:
                continue
            new_text = _normalize_text_for_comparison(new_p.text)
            sim = _compute_text_similarity(old_text, new_text)
            if sim > best_similarity:
                best_similarity = sim
                best_match_idx = idx

        if best_match_idx >= 0:
            matched_new.add(best_match_idx)

        total_similarity += best_similarity

        # Flag significant differences
        if best_similarity < PARAGRAPH_SIMILARITY_THRESHOLD:
            new_text_display = ""
            if best_match_idx >= 0:
                new_text_display = new_paragraphs[best_match_idx].text[:200]

            findings.append(Finding(
                priority=Priority.P2,
                category="content_changed",
                message=f"Paragraph content differs (similarity: {best_similarity:.2%})",
                old_value=old_p.text[:200] + ("..." if len(old_p.text) > 200 else ""),
                new_value=new_text_display + ("..." if len(new_text_display) > 200 else ""),
                evidence=generate_diff_excerpt(old_p.text, new_text_display),
                block_type="paragraph"
            ))

    avg_similarity = total_similarity / len(old_paragraphs) if old_paragraphs else 1.0
    return avg_similarity, findings


def compare_lists(
    old: List[Block], new: List[Block]
) -> Tuple[float, List[Finding]]:
    """Compare list blocks between old and new content.

    Compares list items accounting for reordering. Checks list type
    (ordered vs unordered) and nesting levels. Flags missing items as P2 findings.

    Args:
        old: List of list blocks from the old document.
        new: List of list blocks from the new document.

    Returns:
        Tuple of (similarity_score, list_of_findings).
    """
    findings: List[Finding] = []

    old_lists = _filter_blocks_by_type(old, "list")
    new_lists = _filter_blocks_by_type(new, "list")

    if not old_lists and not new_lists:
        return 1.0, findings

    if not old_lists:
        return 1.0, findings

    if not new_lists:
        findings.append(Finding(
            priority=Priority.P2,
            category="content_missing",
            message="All lists removed from section",
            old_value=f"{len(old_lists)} lists",
            new_value="0 lists",
            block_type="list"
        ))
        return 0.0, findings

    total_similarity = 0.0

    for old_idx, old_list in enumerate(old_lists):
        # Find best matching new list
        best_similarity = 0.0
        best_match: Optional[Block] = None

        for new_list in new_lists:
            sim = _compare_single_list(old_list, new_list)
            if sim > best_similarity:
                best_similarity = sim
                best_match = new_list

        total_similarity += best_similarity

        # Check for list type mismatch
        if best_match and old_list.list_type != best_match.list_type:
            findings.append(Finding(
                priority=Priority.P2,
                category="formatting_changed",
                message="List type changed",
                old_value=old_list.list_type or "unordered",
                new_value=best_match.list_type or "unordered",
                block_type="list"
            ))

        # Check for nesting level changes
        if best_match and old_list.level != best_match.level:
            findings.append(Finding(
                priority=Priority.P2,
                category="structure_changed",
                message="List nesting level changed",
                old_value=f"level {old_list.level}",
                new_value=f"level {best_match.level}",
                block_type="list"
            ))

        # Check for missing items (handle None items)
        old_list_items = old_list.items if old_list.items is not None else []
        old_items = set(_normalize_text_for_comparison(item) for item in old_list_items)
        new_items = set()
        if best_match and best_match.items is not None:
            new_items = set(_normalize_text_for_comparison(item) for item in best_match.items)

        missing_items = old_items - new_items
        if missing_items:
            findings.append(Finding(
                priority=Priority.P2,
                category="content_missing",
                message=f"List items missing: {len(missing_items)} item(s)",
                old_value=", ".join(list(missing_items)[:3]),
                new_value="(not found)",
                block_type="list"
            ))

    avg_similarity = total_similarity / len(old_lists) if old_lists else 1.0
    return avg_similarity, findings


def _compare_single_list(old_list: Block, new_list: Block) -> float:
    """Compare two individual list blocks.

    Args:
        old_list: The reference list block.
        new_list: The list block to compare.

    Returns:
        Similarity score between 0.0 and 1.0.
    """
    # Handle None items gracefully
    old_list_items = old_list.items if old_list.items is not None else []
    new_list_items = new_list.items if new_list.items is not None else []

    old_items = [_normalize_text_for_comparison(item) for item in old_list_items]
    new_items = [_normalize_text_for_comparison(item) for item in new_list_items]

    if not old_items and not new_items:
        return 1.0
    if not old_items or not new_items:
        return 0.0

    # Calculate Jaccard similarity for item sets (accounts for reordering)
    old_set = set(old_items)
    new_set = set(new_items)

    intersection = len(old_set & new_set)
    union = len(old_set | new_set)

    return intersection / union if union > 0 else 1.0


def compare_code_blocks(
    old: List[Block], new: List[Block]
) -> Tuple[float, List[Finding]]:
    """Compare code blocks between old and new content.

    Compares code content preserving whitespace significance. Checks language
    tags match. Flags missing code blocks as P1 findings and content drift as P2.

    Args:
        old: List of code blocks from the old document.
        new: List of code blocks from the new document.

    Returns:
        Tuple of (similarity_score, list_of_findings).
    """
    findings: List[Finding] = []

    old_code = _filter_blocks_by_type(old, "code")
    new_code = _filter_blocks_by_type(new, "code")

    if not old_code and not new_code:
        return 1.0, findings

    if not old_code:
        return 1.0, findings

    if not new_code:
        findings.append(Finding(
            priority=Priority.P1,
            category="code_block_changed",
            message="All code blocks removed from section",
            old_value=f"{len(old_code)} code blocks",
            new_value="0 code blocks",
            block_type="code"
        ))
        return 0.0, findings

    total_similarity = 0.0
    matched_new: Set[int] = set()

    for old_block in old_code:
        best_similarity = 0.0
        best_match_idx = -1
        best_match: Optional[Block] = None

        # Try to match by language first, then by content
        for idx, new_block in enumerate(new_code):
            if idx in matched_new:
                continue

            # Compute content similarity (preserve whitespace for code)
            old_content = old_block.text.strip()
            new_content = new_block.text.strip()
            sim = _compute_text_similarity(old_content, new_content)

            # Boost similarity if languages match
            if old_block.language and new_block.language:
                if old_block.language.lower() == new_block.language.lower():
                    sim = min(1.0, sim + 0.1)

            if sim > best_similarity:
                best_similarity = sim
                best_match_idx = idx
                best_match = new_block

        if best_match_idx >= 0:
            matched_new.add(best_match_idx)

        total_similarity += best_similarity

        # Flag missing code blocks (P1)
        if best_similarity < 0.3:
            findings.append(Finding(
                priority=Priority.P1,
                category="code_block_changed",
                message="Code block not found or significantly changed",
                old_value=old_block.text[:200] + ("..." if len(old_block.text) > 200 else ""),
                new_value="(not found or <30% similar)",
                evidence=generate_diff_excerpt(old_block.text, ""),
                block_type="code"
            ))
        elif best_similarity < PARAGRAPH_SIMILARITY_THRESHOLD and best_match:
            # Flag content drift (P2)
            findings.append(Finding(
                priority=Priority.P2,
                category="code_block_changed",
                message=f"Code block content differs (similarity: {best_similarity:.2%})",
                old_value=old_block.text[:200] + ("..." if len(old_block.text) > 200 else ""),
                new_value=best_match.text[:200] + ("..." if len(best_match.text) > 200 else ""),
                evidence=generate_diff_excerpt(old_block.text, best_match.text),
                block_type="code"
            ))

        # Check language tag mismatch
        if best_match:
            old_lang = (old_block.language or "").lower()
            new_lang = (best_match.language or "").lower()
            if old_lang and new_lang and old_lang != new_lang:
                findings.append(Finding(
                    priority=Priority.P2,
                    category="code_block_changed",
                    message="Code block language tag changed",
                    old_value=old_lang,
                    new_value=new_lang,
                    block_type="code"
                ))

    avg_similarity = total_similarity / len(old_code) if old_code else 1.0
    return avg_similarity, findings


def compare_tables(
    old: List[Block], new: List[Block]
) -> Tuple[float, List[Finding]]:
    """Compare table blocks between old and new content.

    Compares table dimensions (rows/cols) and cell contents.
    Dimension mismatch is P1, content mismatch is P2.

    Args:
        old: List of table blocks from the old document.
        new: List of table blocks from the new document.

    Returns:
        Tuple of (similarity_score, list_of_findings).
    """
    findings: List[Finding] = []

    old_tables = _filter_blocks_by_type(old, "table")
    new_tables = _filter_blocks_by_type(new, "table")

    if not old_tables and not new_tables:
        return 1.0, findings

    if not old_tables:
        return 1.0, findings

    if not new_tables:
        findings.append(Finding(
            priority=Priority.P1,
            category="table_changed",
            message="All tables removed from section",
            old_value=f"{len(old_tables)} tables",
            new_value="0 tables",
            block_type="table"
        ))
        return 0.0, findings

    total_similarity = 0.0

    for old_table in old_tables:
        best_similarity = 0.0
        best_match: Optional[Block] = None

        for new_table in new_tables:
            sim = _compare_single_table(old_table, new_table)
            if sim > best_similarity:
                best_similarity = sim
                best_match = new_table

        total_similarity += best_similarity

        if best_match:
            # Check dimension mismatch (P1)
            old_rows = len(old_table.items) if old_table.items else 0
            new_rows = len(best_match.items) if best_match.items else 0

            # Parse table text to get dimensions if items not available
            if old_rows == 0:
                old_rows = old_table.text.count("\n") + 1 if old_table.text else 0
            if new_rows == 0:
                new_rows = best_match.text.count("\n") + 1 if best_match.text else 0

            if old_rows != new_rows:
                findings.append(Finding(
                    priority=Priority.P1,
                    category="table_changed",
                    message="Table row count changed",
                    old_value=f"{old_rows} rows",
                    new_value=f"{new_rows} rows",
                    block_type="table"
                ))

            # Check content mismatch (P2)
            if best_similarity < PARAGRAPH_SIMILARITY_THRESHOLD:
                findings.append(Finding(
                    priority=Priority.P2,
                    category="table_changed",
                    message=f"Table content differs (similarity: {best_similarity:.2%})",
                    old_value=old_table.text[:200] + ("..." if len(old_table.text) > 200 else ""),
                    new_value=best_match.text[:200] + ("..." if len(best_match.text) > 200 else ""),
                    evidence=generate_diff_excerpt(old_table.text, best_match.text),
                    block_type="table"
                ))

    avg_similarity = total_similarity / len(old_tables) if old_tables else 1.0
    return avg_similarity, findings


def _compare_single_table(old_table: Block, new_table: Block) -> float:
    """Compare two individual table blocks.

    Args:
        old_table: The reference table block.
        new_table: The table block to compare.

    Returns:
        Similarity score between 0.0 and 1.0.
    """
    old_text = _normalize_text_for_comparison(old_table.text)
    new_text = _normalize_text_for_comparison(new_table.text)
    return _compute_text_similarity(old_text, new_text)


def compare_admonitions(
    old: List[Block], new: List[Block]
) -> Tuple[float, List[Finding]]:
    """Compare admonition blocks between old and new content.

    Compares admonition types (note, warning, tip) and content.
    Missing admonitions are flagged as P2 findings.

    Args:
        old: List of admonition blocks from the old document.
        new: List of admonition blocks from the new document.

    Returns:
        Tuple of (similarity_score, list_of_findings).
    """
    findings: List[Finding] = []

    old_admonitions = _filter_blocks_by_type(old, "admonition")
    new_admonitions = _filter_blocks_by_type(new, "admonition")

    if not old_admonitions and not new_admonitions:
        return 1.0, findings

    if not old_admonitions:
        return 1.0, findings

    if not new_admonitions:
        findings.append(Finding(
            priority=Priority.P2,
            category="content_missing",
            message="All admonitions removed from section",
            old_value=f"{len(old_admonitions)} admonitions",
            new_value="0 admonitions",
            block_type="admonition"
        ))
        return 0.0, findings

    total_similarity = 0.0
    matched_new: Set[int] = set()

    for old_adm in old_admonitions:
        best_similarity = 0.0
        best_match_idx = -1
        best_match: Optional[Block] = None

        for idx, new_adm in enumerate(new_admonitions):
            if idx in matched_new:
                continue

            # Compute content similarity
            old_content = _normalize_text_for_comparison(old_adm.text)
            new_content = _normalize_text_for_comparison(new_adm.text)
            sim = _compute_text_similarity(old_content, new_content)

            # Boost if admonition types match
            old_type = (old_adm.admonition_type or "").lower()
            new_type = (new_adm.admonition_type or "").lower()
            if old_type and new_type and old_type == new_type:
                sim = min(1.0, sim + 0.1)

            if sim > best_similarity:
                best_similarity = sim
                best_match_idx = idx
                best_match = new_adm

        if best_match_idx >= 0:
            matched_new.add(best_match_idx)

        total_similarity += best_similarity

        # Flag missing admonition (P2)
        if best_similarity < 0.5:
            findings.append(Finding(
                priority=Priority.P2,
                category="content_missing",
                message=f"Admonition not found or significantly changed (type: {old_adm.admonition_type or 'unknown'})",
                old_value=old_adm.text[:200] + ("..." if len(old_adm.text) > 200 else ""),
                new_value="(not found)",
                block_type="admonition"
            ))
        elif best_match:
            # Check admonition type mismatch
            old_type = (old_adm.admonition_type or "").lower()
            new_type = (best_match.admonition_type or "").lower()
            if old_type and new_type and old_type != new_type:
                findings.append(Finding(
                    priority=Priority.P2,
                    category="formatting_changed",
                    message="Admonition type changed",
                    old_value=old_type,
                    new_value=new_type,
                    block_type="admonition"
                ))

    avg_similarity = total_similarity / len(old_admonitions) if old_admonitions else 1.0
    return avg_similarity, findings


def compare_blocks(
    old_blocks: List[Block], new_blocks: List[Block]
) -> Tuple[float, List[Finding]]:
    """Compare blocks by type and content.

    Compares all block types and returns a weighted similarity score
    along with a list of findings.

    Weights:
        - paragraphs: 35%
        - lists: 15%
        - code: 20%
        - tables: 15%
        - admonitions: 10%
        - images/links: 5%

    Args:
        old_blocks: List of blocks from the old document.
        new_blocks: List of blocks from the new document.

    Returns:
        Tuple of (weighted_similarity_score, aggregated_findings).
    """
    all_findings: List[Finding] = []
    weighted_sum = 0.0
    total_weight = 0.0

    # Compare paragraphs (35%)
    para_score, para_findings = compare_paragraphs(old_blocks, new_blocks)
    all_findings.extend(para_findings)
    if _has_blocks_of_type(old_blocks, "paragraph") or _has_blocks_of_type(new_blocks, "paragraph"):
        weighted_sum += para_score * BLOCK_WEIGHTS["paragraph"]
        total_weight += BLOCK_WEIGHTS["paragraph"]

    # Compare lists (15%)
    list_score, list_findings = compare_lists(old_blocks, new_blocks)
    all_findings.extend(list_findings)
    if _has_blocks_of_type(old_blocks, "list") or _has_blocks_of_type(new_blocks, "list"):
        weighted_sum += list_score * BLOCK_WEIGHTS["list"]
        total_weight += BLOCK_WEIGHTS["list"]

    # Compare code blocks (20%)
    code_score, code_findings = compare_code_blocks(old_blocks, new_blocks)
    all_findings.extend(code_findings)
    if _has_blocks_of_type(old_blocks, "code") or _has_blocks_of_type(new_blocks, "code"):
        weighted_sum += code_score * BLOCK_WEIGHTS["code"]
        total_weight += BLOCK_WEIGHTS["code"]

    # Compare tables (15%)
    table_score, table_findings = compare_tables(old_blocks, new_blocks)
    all_findings.extend(table_findings)
    if _has_blocks_of_type(old_blocks, "table") or _has_blocks_of_type(new_blocks, "table"):
        weighted_sum += table_score * BLOCK_WEIGHTS["table"]
        total_weight += BLOCK_WEIGHTS["table"]

    # Compare admonitions (10%)
    adm_score, adm_findings = compare_admonitions(old_blocks, new_blocks)
    all_findings.extend(adm_findings)
    if _has_blocks_of_type(old_blocks, "admonition") or _has_blocks_of_type(new_blocks, "admonition"):
        weighted_sum += adm_score * BLOCK_WEIGHTS["admonition"]
        total_weight += BLOCK_WEIGHTS["admonition"]

    # Compare images and links (5% combined)
    img_link_score, img_link_findings = _compare_images_and_links(old_blocks, new_blocks)
    all_findings.extend(img_link_findings)
    img_weight = BLOCK_WEIGHTS["image"] + BLOCK_WEIGHTS["link"]
    if (_has_blocks_of_type(old_blocks, "image") or _has_blocks_of_type(new_blocks, "image") or
            _has_blocks_of_type(old_blocks, "link") or _has_blocks_of_type(new_blocks, "link")):
        weighted_sum += img_link_score * img_weight
        total_weight += img_weight

    # Compute final weighted score
    if total_weight > 0:
        final_score = weighted_sum / total_weight
    else:
        final_score = 1.0  # No content to compare

    return final_score, all_findings


def _has_blocks_of_type(blocks: List[Block], block_type: str) -> bool:
    """Check if block list contains blocks of a specific type.

    Args:
        blocks: List of blocks to check.
        block_type: The type to check for.

    Returns:
        True if any blocks of the specified type exist.
    """
    return len(_filter_blocks_by_type(blocks, block_type)) > 0


def _compare_images_and_links(
    old: List[Block], new: List[Block]
) -> Tuple[float, List[Finding]]:
    """Compare image and link blocks between old and new content.

    Args:
        old: List of blocks from the old document.
        new: List of blocks from the new document.

    Returns:
        Tuple of (similarity_score, list_of_findings).
    """
    findings: List[Finding] = []

    old_images = _filter_blocks_by_type(old, "image")
    new_images = _filter_blocks_by_type(new, "image")
    old_links = _filter_blocks_by_type(old, "link")
    new_links = _filter_blocks_by_type(new, "link")

    image_score = 1.0
    link_score = 1.0

    # Compare images
    if old_images:
        if not new_images:
            findings.append(Finding(
                priority=Priority.P2,
                category="image_missing",
                message="All images removed from section",
                old_value=f"{len(old_images)} images",
                new_value="0 images",
                block_type="image"
            ))
            image_score = 0.0
        else:
            # Check for missing images by src or alt_text
            old_srcs = {img.src or img.alt_text or img.text for img in old_images}
            new_srcs = {img.src or img.alt_text or img.text for img in new_images}
            missing = old_srcs - new_srcs
            if missing:
                findings.append(Finding(
                    priority=Priority.P2,
                    category="image_missing",
                    message=f"Images missing: {len(missing)} image(s)",
                    old_value=", ".join(list(missing)[:3]),
                    new_value="(not found)",
                    block_type="image"
                ))
            image_score = len(old_srcs & new_srcs) / len(old_srcs) if old_srcs else 1.0

    # Compare links
    if old_links:
        if not new_links:
            findings.append(Finding(
                priority=Priority.P2,
                category="link_changed",
                message="All links removed from section",
                old_value=f"{len(old_links)} links",
                new_value="0 links",
                block_type="link"
            ))
            link_score = 0.0
        else:
            # Check for missing links by href
            old_hrefs = {link.href or link.text for link in old_links}
            new_hrefs = {link.href or link.text for link in new_links}
            missing = old_hrefs - new_hrefs
            if missing:
                findings.append(Finding(
                    priority=Priority.P2,
                    category="link_changed",
                    message=f"Links missing: {len(missing)} link(s)",
                    old_value=", ".join(list(missing)[:3]),
                    new_value="(not found)",
                    block_type="link"
                ))
            link_score = len(old_hrefs & new_hrefs) / len(old_hrefs) if old_hrefs else 1.0

    # Combine scores (weighted average based on counts)
    total_old = len(old_images) + len(old_links)
    if total_old == 0:
        return 1.0, findings

    combined_score = (
        (image_score * len(old_images) + link_score * len(old_links)) / total_old
    )
    return combined_score, findings


def compare_section(
    old_section: Section, new_section: Section
) -> Tuple[float, List[Finding]]:
    """Compare two sections using all block comparators.

    Uses all block comparators to compute a weighted average score
    and aggregates all findings.

    Args:
        old_section: The reference section.
        new_section: The section to compare.

    Returns:
        Tuple of (weighted_similarity_score, aggregated_findings).
    """
    findings: List[Finding] = []

    # Extract blocks from sections if they have a blocks attribute
    old_blocks: List[Block] = []
    new_blocks: List[Block] = []

    if hasattr(old_section, "blocks") and old_section.blocks:
        old_blocks = old_section.blocks
    elif old_section.content:
        # Create a paragraph block from content if no blocks available
        old_blocks = [Block(text=old_section.content, block_type="paragraph")]

    if hasattr(new_section, "blocks") and new_section.blocks:
        new_blocks = new_section.blocks
    elif new_section.content:
        new_blocks = [Block(text=new_section.content, block_type="paragraph")]

    # Compare blocks
    score, block_findings = compare_blocks(old_blocks, new_blocks)

    # Add location to each finding
    location = old_section.title or old_section.key
    for finding in block_findings:
        finding.location = location

    findings.extend(block_findings)

    return score, findings
