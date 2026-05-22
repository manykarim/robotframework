"""Content comparators for different block types."""

from difflib import unified_diff
from typing import Any

from docdiff.models import Block, BlockType, Finding, Section, Severity
from docdiff.normalizers import (
    fuzzy_match,
    normalize_code,
    normalize_list_item,
    normalize_table_cell,
    normalize_text,
    similarity_ratio,
    word_overlap_ratio,
)

# Import from content_comparator module
from docdiff.comparators.content_comparator import (
    BLOCK_WEIGHTS,
    compare_blocks,
    compare_section,
    generate_diff_excerpt,
)


class BlockComparator:
    """Compare content blocks between source and target."""

    def __init__(
        self,
        text_threshold: float = 0.9,
        code_threshold: float = 0.95,
        strict_mode: bool = False,
    ):
        """Initialize the comparator.

        Args:
            text_threshold: Minimum similarity for text blocks
            code_threshold: Minimum similarity for code blocks
            strict_mode: If True, require exact matches for code
        """
        self.text_threshold = text_threshold
        self.code_threshold = code_threshold
        self.strict_mode = strict_mode

    def compare_blocks(
        self,
        source_block: Block,
        target_block: Block,
        section: Section | None = None,
    ) -> list[Finding]:
        """Compare two blocks and return findings.

        Args:
            source_block: Block from source document
            target_block: Block from target document
            section: Parent section for context

        Returns:
            List of findings (empty if blocks match)
        """
        if source_block.block_type != target_block.block_type:
            return [Finding(
                category="block_type_mismatch",
                severity=Severity.WARNING,
                message=f"Block type changed from {source_block.block_type.value} to {target_block.block_type.value}",
                source_location=self._get_location(section, source_block),
                target_location=self._get_location(section, target_block),
                source_content=source_block.content[:200],
                target_content=target_block.content[:200],
            )]

        comparators = {
            BlockType.PARAGRAPH: self._compare_paragraphs,
            BlockType.CODE: self._compare_code,
            BlockType.TABLE: self._compare_tables,
            BlockType.LIST: self._compare_lists,
        }

        comparator = comparators.get(source_block.block_type, self._compare_generic)
        return comparator(source_block, target_block, section)

    def _compare_paragraphs(
        self,
        source: Block,
        target: Block,
        section: Section | None,
    ) -> list[Finding]:
        """Compare paragraph blocks."""
        findings: list[Finding] = []

        source_text = normalize_text(source.content)
        target_text = normalize_text(target.content)

        if source_text == target_text:
            return findings

        sim = similarity_ratio(source_text, target_text)

        if sim < self.text_threshold:
            severity = Severity.ERROR if sim < 0.5 else Severity.WARNING
            findings.append(Finding(
                category="content_difference",
                severity=severity,
                message=f"Paragraph content differs (similarity: {sim:.1%})",
                source_location=self._get_location(section, source),
                target_location=self._get_location(section, target),
                source_content=source_text[:500],
                target_content=target_text[:500],
                suggestion="Review content for accuracy",
            ))

        return findings

    def _compare_code(
        self,
        source: Block,
        target: Block,
        section: Section | None,
    ) -> list[Finding]:
        """Compare code blocks."""
        findings: list[Finding] = []

        source_code = normalize_code(source.content)
        target_code = normalize_code(target.content)

        # Check language
        source_lang = source.metadata.get('language')
        target_lang = target.metadata.get('language')

        if source_lang and target_lang and source_lang != target_lang:
            findings.append(Finding(
                category="code_language_change",
                severity=Severity.INFO,
                message=f"Code language changed from '{source_lang}' to '{target_lang}'",
                source_location=self._get_location(section, source),
                target_location=self._get_location(section, target),
            ))

        # Compare content
        if source_code == target_code:
            return findings

        if self.strict_mode:
            # In strict mode, any difference is an error
            diff = list(unified_diff(
                source_code.splitlines(),
                target_code.splitlines(),
                lineterm='',
            ))
            findings.append(Finding(
                category="code_difference",
                severity=Severity.ERROR,
                message="Code block content differs",
                source_location=self._get_location(section, source),
                target_location=self._get_location(section, target),
                source_content=source_code,
                target_content=target_code,
                suggestion='\n'.join(diff),
            ))
        else:
            sim = similarity_ratio(source_code, target_code)
            if sim < self.code_threshold:
                severity = Severity.ERROR if sim < 0.7 else Severity.WARNING
                findings.append(Finding(
                    category="code_difference",
                    severity=severity,
                    message=f"Code block content differs (similarity: {sim:.1%})",
                    source_location=self._get_location(section, source),
                    target_location=self._get_location(section, target),
                    source_content=source_code,
                    target_content=target_code,
                ))

        return findings

    def _compare_tables(
        self,
        source: Block,
        target: Block,
        section: Section | None,
    ) -> list[Finding]:
        """Compare table blocks."""
        findings: list[Finding] = []

        source_data = source.metadata.get('data', [])
        target_data = target.metadata.get('data', [])

        # Compare row counts
        if len(source_data) != len(target_data):
            findings.append(Finding(
                category="table_row_count",
                severity=Severity.WARNING,
                message=f"Table row count differs: {len(source_data)} vs {len(target_data)}",
                source_location=self._get_location(section, source),
                target_location=self._get_location(section, target),
            ))

        # Compare cell by cell
        for row_idx, (source_row, target_row) in enumerate(zip(source_data, target_data)):
            if len(source_row) != len(target_row):
                findings.append(Finding(
                    category="table_column_count",
                    severity=Severity.WARNING,
                    message=f"Table row {row_idx} column count differs: {len(source_row)} vs {len(target_row)}",
                    source_location=self._get_location(section, source),
                    target_location=self._get_location(section, target),
                ))
                continue

            for col_idx, (source_cell, target_cell) in enumerate(zip(source_row, target_row)):
                source_norm = normalize_table_cell(source_cell)
                target_norm = normalize_table_cell(target_cell)

                if source_norm != target_norm:
                    sim = similarity_ratio(source_norm, target_norm)
                    if sim < self.text_threshold:
                        findings.append(Finding(
                            category="table_cell_difference",
                            severity=Severity.WARNING,
                            message=f"Table cell [{row_idx},{col_idx}] differs",
                            source_location=self._get_location(section, source),
                            target_location=self._get_location(section, target),
                            source_content=source_cell,
                            target_content=target_cell,
                        ))

        return findings

    def _compare_lists(
        self,
        source: Block,
        target: Block,
        section: Section | None,
    ) -> list[Finding]:
        """Compare list blocks."""
        findings: list[Finding] = []

        source_items = source.metadata.get('items', [source.content])
        target_items = target.metadata.get('items', [target.content])

        # Normalize items
        if isinstance(source_items, str):
            source_items = [source_items]
        if isinstance(target_items, str):
            target_items = [target_items]

        source_normalized = [normalize_list_item(item) for item in source_items]
        target_normalized = [normalize_list_item(item) for item in target_items]

        # Check for missing/extra items
        source_set = set(source_normalized)
        target_set = set(target_normalized)

        missing = source_set - target_set
        extra = target_set - source_set

        if missing:
            findings.append(Finding(
                category="list_missing_items",
                severity=Severity.WARNING,
                message=f"List missing {len(missing)} item(s) from source",
                source_location=self._get_location(section, source),
                target_location=self._get_location(section, target),
                source_content='\n'.join(missing),
            ))

        if extra:
            findings.append(Finding(
                category="list_extra_items",
                severity=Severity.INFO,
                message=f"List has {len(extra)} extra item(s) not in source",
                source_location=self._get_location(section, source),
                target_location=self._get_location(section, target),
                target_content='\n'.join(extra),
            ))

        # Check list type
        source_type = source.metadata.get('type')
        target_type = target.metadata.get('type')

        if source_type and target_type and source_type != target_type:
            findings.append(Finding(
                category="list_type_change",
                severity=Severity.INFO,
                message=f"List type changed from '{source_type}' to '{target_type}'",
                source_location=self._get_location(section, source),
                target_location=self._get_location(section, target),
            ))

        return findings

    def _compare_generic(
        self,
        source: Block,
        target: Block,
        section: Section | None,
    ) -> list[Finding]:
        """Generic comparison for other block types."""
        findings: list[Finding] = []

        source_text = normalize_text(source.content)
        target_text = normalize_text(target.content)

        if source_text != target_text:
            sim = similarity_ratio(source_text, target_text)
            if sim < self.text_threshold:
                findings.append(Finding(
                    category="content_difference",
                    severity=Severity.WARNING,
                    message=f"Block content differs (similarity: {sim:.1%})",
                    source_location=self._get_location(section, source),
                    target_location=self._get_location(section, target),
                    source_content=source_text[:300],
                    target_content=target_text[:300],
                ))

        return findings

    def _get_location(self, section: Section | None, block: Block) -> str:
        """Get a location string for a block."""
        parts = []
        if section:
            parts.append(section.get_full_path())
        if block.line_number:
            parts.append(f"line {block.line_number}")
        return " - ".join(parts) if parts else "unknown"


def compare_paragraphs(
    source: str,
    target: str,
    threshold: float = 0.9,
) -> tuple[bool, float]:
    """Compare two paragraph texts.

    Args:
        source: Source paragraph text
        target: Target paragraph text
        threshold: Minimum similarity for a match

    Returns:
        Tuple of (is_match, similarity_ratio)
    """
    source_norm = normalize_text(source)
    target_norm = normalize_text(target)

    sim = similarity_ratio(source_norm, target_norm)
    return sim >= threshold, sim


def compare_code_blocks(
    source: str,
    target: str,
    strict: bool = False,
) -> tuple[bool, list[str]]:
    """Compare two code blocks.

    Args:
        source: Source code content
        target: Target code content
        strict: If True, require exact match

    Returns:
        Tuple of (is_match, diff_lines)
    """
    source_norm = normalize_code(source)
    target_norm = normalize_code(target)

    if source_norm == target_norm:
        return True, []

    diff = list(unified_diff(
        source_norm.splitlines(),
        target_norm.splitlines(),
        lineterm='',
    ))

    if strict:
        return False, diff

    # Allow minor differences if similarity is high
    sim = similarity_ratio(source_norm, target_norm)
    return sim >= 0.95, diff


def compare_tables(
    source_data: list[list[str]],
    target_data: list[list[str]],
) -> dict[str, Any]:
    """Compare two tables.

    Args:
        source_data: Source table as list of rows
        target_data: Target table as list of rows

    Returns:
        Dictionary with comparison results
    """
    result: dict[str, Any] = {
        'matches': True,
        'row_diff': len(target_data) - len(source_data),
        'cell_diffs': [],
    }

    for row_idx, (source_row, target_row) in enumerate(zip(source_data, target_data)):
        for col_idx, (source_cell, target_cell) in enumerate(zip(source_row, target_row)):
            source_norm = normalize_table_cell(source_cell)
            target_norm = normalize_table_cell(target_cell)

            if source_norm != target_norm:
                result['matches'] = False
                result['cell_diffs'].append({
                    'row': row_idx,
                    'col': col_idx,
                    'source': source_cell,
                    'target': target_cell,
                })

    if len(source_data) != len(target_data):
        result['matches'] = False

    return result


def compare_lists(
    source_items: list[str],
    target_items: list[str],
) -> dict[str, Any]:
    """Compare two lists.

    Args:
        source_items: Source list items
        target_items: Target list items

    Returns:
        Dictionary with comparison results
    """
    source_norm = [normalize_list_item(item) for item in source_items]
    target_norm = [normalize_list_item(item) for item in target_items]

    source_set = set(source_norm)
    target_set = set(target_norm)

    return {
        'matches': source_set == target_set,
        'missing': list(source_set - target_set),
        'extra': list(target_set - source_set),
        'common': list(source_set & target_set),
        'order_preserved': source_norm == target_norm,
    }
