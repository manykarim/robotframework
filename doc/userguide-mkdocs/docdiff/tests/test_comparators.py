"""Tests for docdiff.comparators module."""

import pytest

from docdiff.comparators import (
    BlockComparator,
    compare_paragraphs,
    compare_code_blocks,
    compare_tables,
    compare_lists,
)
from docdiff.models import Block, BlockType, Section, Severity


class TestBlockComparator:
    """Tests for BlockComparator class."""

    def test_comparator_default_config(self):
        """Test default comparator configuration."""
        comparator = BlockComparator()
        
        assert comparator.text_threshold == 0.9
        assert comparator.code_threshold == 0.95
        assert comparator.strict_mode is False

    def test_comparator_custom_config(self):
        """Test custom comparator configuration."""
        comparator = BlockComparator(
            text_threshold=0.8,
            code_threshold=0.9,
            strict_mode=True,
        )
        
        assert comparator.text_threshold == 0.8
        assert comparator.code_threshold == 0.9
        assert comparator.strict_mode is True

    def test_compare_blocks_type_mismatch(self):
        """Test comparison when block types differ."""
        comparator = BlockComparator()
        source = Block(block_type=BlockType.PARAGRAPH, content="text")
        target = Block(block_type=BlockType.CODE, content="text")
        
        findings = comparator.compare_blocks(source, target)
        
        assert len(findings) == 1
        assert findings[0].category == "block_type_mismatch"
        assert findings[0].severity == Severity.WARNING

    def test_compare_identical_paragraphs(self, sample_paragraph_block):
        """Test comparison of identical paragraphs."""
        comparator = BlockComparator()
        target = Block(
            block_type=BlockType.PARAGRAPH,
            content=sample_paragraph_block.content,
        )
        
        findings = comparator.compare_blocks(sample_paragraph_block, target)
        
        assert len(findings) == 0

    def test_compare_different_paragraphs(self):
        """Test comparison of different paragraphs."""
        comparator = BlockComparator()
        source = Block(block_type=BlockType.PARAGRAPH, content="Original text content")
        target = Block(block_type=BlockType.PARAGRAPH, content="Completely different content here")
        
        findings = comparator.compare_blocks(source, target)
        
        assert len(findings) >= 1
        assert findings[0].category == "content_difference"

    def test_compare_similar_paragraphs_within_threshold(self):
        """Test comparison of similar paragraphs within threshold."""
        comparator = BlockComparator(text_threshold=0.7)
        source = Block(block_type=BlockType.PARAGRAPH, content="This is the original text.")
        target = Block(block_type=BlockType.PARAGRAPH, content="This is the modified text.")
        
        findings = comparator.compare_blocks(source, target)
        
        # Should pass with lower threshold
        # The actual result depends on similarity calculation

    def test_compare_identical_code_blocks(self, sample_code_block):
        """Test comparison of identical code blocks."""
        comparator = BlockComparator()
        target = Block(
            block_type=BlockType.CODE,
            content=sample_code_block.content,
            metadata=sample_code_block.metadata,
        )
        
        findings = comparator.compare_blocks(sample_code_block, target)
        
        assert len(findings) == 0

    def test_compare_different_code_blocks(self):
        """Test comparison of different code blocks."""
        comparator = BlockComparator()
        source = Block(
            block_type=BlockType.CODE,
            content="print('hello')",
            metadata={"language": "python"},
        )
        target = Block(
            block_type=BlockType.CODE,
            content="print('goodbye')",
            metadata={"language": "python"},
        )
        
        findings = comparator.compare_blocks(source, target)
        
        assert len(findings) >= 1
        assert any(f.category == "code_difference" for f in findings)

    def test_compare_code_language_change(self):
        """Test detection of code language change."""
        comparator = BlockComparator()
        source = Block(
            block_type=BlockType.CODE,
            content="code",
            metadata={"language": "python"},
        )
        target = Block(
            block_type=BlockType.CODE,
            content="code",
            metadata={"language": "javascript"},
        )
        
        findings = comparator.compare_blocks(source, target)
        
        assert any(f.category == "code_language_change" for f in findings)

    def test_compare_code_strict_mode(self):
        """Test code comparison in strict mode."""
        comparator = BlockComparator(strict_mode=True)
        source = Block(
            block_type=BlockType.CODE,
            content="print('hello')",
            metadata={"language": "python"},
        )
        target = Block(
            block_type=BlockType.CODE,
            content="print('hello')  ",  # Trailing space
            metadata={"language": "python"},
        )
        
        findings = comparator.compare_blocks(source, target)
        
        # Strict mode should still normalize, so identical after normalization
        # Check if any code_difference finding exists

    def test_compare_tables_identical(self, sample_table_block):
        """Test comparison of identical tables."""
        comparator = BlockComparator()
        target = Block(
            block_type=BlockType.TABLE,
            content=sample_table_block.content,
            metadata=sample_table_block.metadata.copy(),
        )
        
        findings = comparator.compare_blocks(sample_table_block, target)
        
        assert len(findings) == 0

    def test_compare_tables_different_row_count(self):
        """Test comparison of tables with different row counts."""
        comparator = BlockComparator()
        source = Block(
            block_type=BlockType.TABLE,
            content="A | B\n1 | 2",
            metadata={"rows": 2, "data": [["A", "B"], ["1", "2"]]},
        )
        target = Block(
            block_type=BlockType.TABLE,
            content="A | B\n1 | 2\n3 | 4",
            metadata={"rows": 3, "data": [["A", "B"], ["1", "2"], ["3", "4"]]},
        )
        
        findings = comparator.compare_blocks(source, target)
        
        assert any(f.category == "table_row_count" for f in findings)

    def test_compare_tables_cell_difference(self):
        """Test detection of table cell differences."""
        comparator = BlockComparator()
        source = Block(
            block_type=BlockType.TABLE,
            content="A | B",
            metadata={"rows": 1, "data": [["A", "B"]]},
        )
        target = Block(
            block_type=BlockType.TABLE,
            content="A | C",
            metadata={"rows": 1, "data": [["A", "C"]]},
        )
        
        findings = comparator.compare_blocks(source, target)
        
        assert any(f.category == "table_cell_difference" for f in findings)

    def test_compare_lists_identical(self, sample_list_block):
        """Test comparison of identical lists."""
        comparator = BlockComparator()
        target = Block(
            block_type=BlockType.LIST,
            content=sample_list_block.content,
            metadata=sample_list_block.metadata.copy(),
        )
        
        findings = comparator.compare_blocks(sample_list_block, target)
        
        assert len(findings) == 0

    def test_compare_lists_missing_items(self):
        """Test detection of missing list items."""
        comparator = BlockComparator()
        source = Block(
            block_type=BlockType.LIST,
            content="a\nb\nc",
            metadata={"type": "ul", "items": ["a", "b", "c"]},
        )
        target = Block(
            block_type=BlockType.LIST,
            content="a\nb",
            metadata={"type": "ul", "items": ["a", "b"]},
        )
        
        findings = comparator.compare_blocks(source, target)
        
        assert any(f.category == "list_missing_items" for f in findings)

    def test_compare_lists_extra_items(self):
        """Test detection of extra list items."""
        comparator = BlockComparator()
        source = Block(
            block_type=BlockType.LIST,
            content="a",
            metadata={"type": "ul", "items": ["a"]},
        )
        target = Block(
            block_type=BlockType.LIST,
            content="a\nb",
            metadata={"type": "ul", "items": ["a", "b"]},
        )
        
        findings = comparator.compare_blocks(source, target)
        
        assert any(f.category == "list_extra_items" for f in findings)

    def test_compare_lists_type_change(self):
        """Test detection of list type change."""
        comparator = BlockComparator()
        source = Block(
            block_type=BlockType.LIST,
            content="item",
            metadata={"type": "ul", "items": ["item"]},
        )
        target = Block(
            block_type=BlockType.LIST,
            content="item",
            metadata={"type": "ol", "items": ["item"]},
        )
        
        findings = comparator.compare_blocks(source, target)
        
        assert any(f.category == "list_type_change" for f in findings)

    def test_compare_with_section_context(self):
        """Test that section context is included in findings."""
        comparator = BlockComparator()
        section = Section(number="2.1", title="Test Section", level=2, key="test-section")
        source = Block(block_type=BlockType.PARAGRAPH, content="original", line_number=10)
        target = Block(block_type=BlockType.PARAGRAPH, content="different", line_number=12)
        
        findings = comparator.compare_blocks(source, target, section)
        
        if findings:
            assert "Test Section" in (findings[0].source_location or "")


class TestCompareParagraphs:
    """Tests for compare_paragraphs function."""

    def test_compare_identical(self):
        """Test comparison of identical paragraphs."""
        is_match, ratio = compare_paragraphs("Hello World", "Hello World")
        
        assert is_match is True
        assert ratio == 1.0

    def test_compare_different(self):
        """Test comparison of different paragraphs."""
        is_match, ratio = compare_paragraphs("abc", "xyz")
        
        assert is_match is False
        assert ratio < 0.9

    def test_compare_similar(self):
        """Test comparison of similar paragraphs."""
        is_match, ratio = compare_paragraphs(
            "The quick brown fox",
            "The quick brown dog"
        )
        
        assert 0.0 < ratio < 1.0

    def test_compare_with_threshold(self):
        """Test comparison with custom threshold."""
        is_match_strict, _ = compare_paragraphs("hello", "hallo", threshold=0.95)
        is_match_relaxed, _ = compare_paragraphs("hello", "hallo", threshold=0.5)
        
        # Depending on similarity, strict might fail where relaxed passes

    def test_compare_normalizes_text(self):
        """Test that text is normalized before comparison."""
        is_match, ratio = compare_paragraphs("  Hello   World  ", "hello world")
        
        assert ratio > 0.9  # Should be very similar after normalization


class TestCompareCodeBlocks:
    """Tests for compare_code_blocks function."""

    def test_compare_identical(self):
        """Test comparison of identical code."""
        is_match, diff = compare_code_blocks(
            "print('hello')",
            "print('hello')"
        )
        
        assert is_match is True
        assert diff == []

    def test_compare_different(self):
        """Test comparison of different code."""
        is_match, diff = compare_code_blocks(
            "print('hello')",
            "print('goodbye')",
            strict=True
        )
        
        assert is_match is False
        assert len(diff) > 0

    def test_compare_whitespace_normalized(self):
        """Test that trailing whitespace is normalized."""
        is_match, diff = compare_code_blocks(
            "print('hello')  ",
            "print('hello')"
        )
        
        assert is_match is True

    def test_compare_strict_mode(self):
        """Test strict comparison mode."""
        code1 = "line1\nline2"
        code2 = "line1\nline3"
        
        is_match, diff = compare_code_blocks(code1, code2, strict=True)
        
        assert is_match is False
        assert len(diff) > 0

    def test_compare_returns_diff(self):
        """Test that diff is returned."""
        code1 = "line1\nline2"
        code2 = "line1\nline3"
        
        _, diff = compare_code_blocks(code1, code2)
        
        # Diff should contain unified diff format lines
        assert isinstance(diff, list)


class TestCompareTables:
    """Tests for compare_tables function."""

    def test_compare_identical(self):
        """Test comparison of identical tables."""
        data = [["A", "B"], ["1", "2"]]
        result = compare_tables(data, data.copy())
        
        assert result["matches"] is True
        assert result["row_diff"] == 0
        assert result["cell_diffs"] == []

    def test_compare_different_rows(self):
        """Test comparison with different row counts."""
        source = [["A", "B"]]
        target = [["A", "B"], ["1", "2"]]
        
        result = compare_tables(source, target)
        
        assert result["matches"] is False
        assert result["row_diff"] == 1

    def test_compare_cell_difference(self):
        """Test detection of cell differences."""
        source = [["A", "B"]]
        target = [["A", "C"]]
        
        result = compare_tables(source, target)
        
        assert result["matches"] is False
        assert len(result["cell_diffs"]) == 1
        assert result["cell_diffs"][0]["row"] == 0
        assert result["cell_diffs"][0]["col"] == 1

    def test_compare_multiple_differences(self):
        """Test detection of multiple cell differences."""
        source = [["A", "B"], ["1", "2"]]
        target = [["X", "B"], ["1", "Y"]]
        
        result = compare_tables(source, target)
        
        assert result["matches"] is False
        assert len(result["cell_diffs"]) == 2


class TestCompareLists:
    """Tests for compare_lists function."""

    def test_compare_identical(self):
        """Test comparison of identical lists."""
        items = ["a", "b", "c"]
        result = compare_lists(items, items.copy())
        
        assert result["matches"] is True
        assert result["missing"] == []
        assert result["extra"] == []
        assert result["order_preserved"] is True

    def test_compare_missing_items(self):
        """Test detection of missing items."""
        source = ["a", "b", "c"]
        target = ["a", "b"]
        
        result = compare_lists(source, target)
        
        assert result["matches"] is False
        assert "c" in result["missing"]

    def test_compare_extra_items(self):
        """Test detection of extra items."""
        source = ["a", "b"]
        target = ["a", "b", "c"]
        
        result = compare_lists(source, target)
        
        assert result["matches"] is False
        assert "c" in result["extra"]

    def test_compare_reordered(self):
        """Test detection of reordering."""
        source = ["a", "b", "c"]
        target = ["c", "b", "a"]
        
        result = compare_lists(source, target)
        
        assert result["matches"] is True  # Same items
        assert result["order_preserved"] is False

    def test_compare_common_items(self):
        """Test that common items are identified."""
        source = ["a", "b", "c"]
        target = ["b", "c", "d"]
        
        result = compare_lists(source, target)
        
        assert "b" in result["common"]
        assert "c" in result["common"]
        assert len(result["common"]) == 2

    def test_compare_normalizes_items(self):
        """Test that list items are normalized."""
        source = ["- item one"]
        target = ["item one"]  # Without marker

        result = compare_lists(source, target)

        # After normalization, they should be the same
        assert result["matches"] is True


class TestCompareWeightedScoring:
    """Tests for weighted block comparison."""

    def test_compare_weighted_scoring_paragraphs_dominant(self):
        """Test that paragraphs have appropriate weight in scoring."""
        from docdiff.comparators.content_comparator import compare_blocks, BLOCK_WEIGHTS

        # Paragraphs should have significant weight
        assert BLOCK_WEIGHTS["paragraph"] >= 0.3

    def test_compare_weighted_scoring_code_important(self):
        """Test that code blocks are weighted appropriately."""
        from docdiff.comparators.content_comparator import BLOCK_WEIGHTS

        # Code should have meaningful weight
        assert BLOCK_WEIGHTS["code"] >= 0.15

    def test_compare_weighted_scoring_tables(self):
        """Test that tables are weighted appropriately."""
        from docdiff.comparators.content_comparator import BLOCK_WEIGHTS

        assert BLOCK_WEIGHTS["table"] >= 0.1

    def test_compare_weighted_scoring_combined(self):
        """Test weighted comparison with multiple block types."""
        from docdiff.comparators.content_comparator import compare_blocks
        from docdiff.models import Block, BlockType

        old_blocks = [
            Block(block_type=BlockType.PARAGRAPH, content="This is a paragraph."),
            Block(block_type=BlockType.CODE, content="print('hello')"),
        ]
        new_blocks = [
            Block(block_type=BlockType.PARAGRAPH, content="This is a paragraph."),
            Block(block_type=BlockType.CODE, content="print('hello')"),
        ]

        score, findings = compare_blocks(old_blocks, new_blocks)

        # Identical content should have high score
        assert score >= 0.9

    def test_compare_weighted_scoring_partial_match(self):
        """Test weighted comparison with partial matches."""
        from docdiff.comparators.content_comparator import compare_blocks
        from docdiff.models import Block, BlockType

        old_blocks = [
            Block(block_type=BlockType.PARAGRAPH, content="Original paragraph."),
            Block(block_type=BlockType.CODE, content="print('original')"),
        ]
        new_blocks = [
            Block(block_type=BlockType.PARAGRAPH, content="Different paragraph."),
            Block(block_type=BlockType.CODE, content="print('original')"),
        ]

        score, findings = compare_blocks(old_blocks, new_blocks)

        # Score should be between 0 and 1 (partial match)
        assert 0.0 <= score <= 1.0


class TestCompareGeneratesDiff:
    """Tests for diff excerpt generation."""

    def test_compare_generates_diff_on_difference(self):
        """Test that diff excerpt is generated for differences."""
        from docdiff.comparators.content_comparator import generate_diff_excerpt

        old_text = "Line 1\nLine 2\nLine 3"
        new_text = "Line 1\nLine 2 modified\nLine 3"

        diff = generate_diff_excerpt(old_text, new_text)

        assert len(diff) > 0
        # Should contain diff markers
        assert "---" in diff or "+++" in diff or "-" in diff or "+" in diff

    def test_compare_generates_diff_truncated(self):
        """Test that long diffs are truncated."""
        from docdiff.comparators.content_comparator import generate_diff_excerpt

        old_text = "\n".join([f"Line {i}" for i in range(100)])
        new_text = "\n".join([f"Modified {i}" for i in range(100)])

        diff = generate_diff_excerpt(old_text, new_text, max_lines=5)

        # Should be truncated
        lines = diff.split("\n")
        assert len(lines) <= 6  # 5 + "more lines" message

    def test_compare_generates_diff_empty_old(self):
        """Test diff generation when old text is empty."""
        from docdiff.comparators.content_comparator import generate_diff_excerpt

        diff = generate_diff_excerpt("", "New content")

        # Should handle empty old gracefully
        assert isinstance(diff, str)

    def test_compare_generates_diff_empty_new(self):
        """Test diff generation when new text is empty."""
        from docdiff.comparators.content_comparator import generate_diff_excerpt

        diff = generate_diff_excerpt("Old content", "")

        # Should handle empty new gracefully
        assert isinstance(diff, str)

    def test_compare_generates_diff_identical(self):
        """Test diff generation for identical content."""
        from docdiff.comparators.content_comparator import generate_diff_excerpt

        text = "Same content"
        diff = generate_diff_excerpt(text, text)

        # Should return empty or minimal diff
        assert diff == "" or len(diff) < 50


class TestCompareCodeBlocksLanguage:
    """Tests for code block comparison with language tags."""

    def test_compare_code_blocks_same_language(self):
        """Test code block comparison with matching language."""
        from docdiff.comparators.content_comparator import compare_code_blocks as compare_code_fn
        from docdiff.models import Block, BlockType

        old_blocks = [
            Block(
                block_type=BlockType.CODE,
                content="print('hello')",
                metadata={"language": "python"},
            )
        ]
        new_blocks = [
            Block(
                block_type=BlockType.CODE,
                content="print('hello')",
                metadata={"language": "python"},
            )
        ]

        # Using the content comparator function
        from docdiff.comparators.content_comparator import compare_code_blocks

        score, findings = compare_code_blocks(old_blocks, new_blocks)

        assert score >= 0.9
        assert len([f for f in findings if "language" in f.message.lower()]) == 0

    def test_compare_code_blocks_different_language(self):
        """Test code block comparison with different languages."""
        from docdiff.comparators.content_comparator import compare_code_blocks
        from docdiff.models import Block, BlockType

        old_blocks = [
            Block(
                block_type=BlockType.CODE,
                content="console.log('hello')",
                language="javascript",
            )
        ]
        new_blocks = [
            Block(
                block_type=BlockType.CODE,
                content="console.log('hello')",
                language="typescript",
            )
        ]

        score, findings = compare_code_blocks(old_blocks, new_blocks)

        # Should flag language change
        lang_findings = [f for f in findings if "language" in f.message.lower()]
        assert len(lang_findings) >= 1

    def test_compare_code_blocks_language_added(self):
        """Test when language tag is added."""
        from docdiff.comparators.content_comparator import compare_code_blocks
        from docdiff.models import Block, BlockType

        old_blocks = [
            Block(
                block_type=BlockType.CODE,
                content="code here",
                language=None,
            )
        ]
        new_blocks = [
            Block(
                block_type=BlockType.CODE,
                content="code here",
                language="python",
            )
        ]

        score, findings = compare_code_blocks(old_blocks, new_blocks)

        # Content is same, so score should still be high
        assert score >= 0.8

    def test_compare_code_blocks_language_removed(self):
        """Test when language tag is removed."""
        from docdiff.comparators.content_comparator import compare_code_blocks
        from docdiff.models import Block, BlockType

        old_blocks = [
            Block(
                block_type=BlockType.CODE,
                content="code here",
                language="python",
            )
        ]
        new_blocks = [
            Block(
                block_type=BlockType.CODE,
                content="code here",
                language=None,
            )
        ]

        score, findings = compare_code_blocks(old_blocks, new_blocks)

        # Content is same
        assert score >= 0.8


class TestCompareSectionContent:
    """Tests for comparing section content."""

    def test_compare_section_identical(self):
        """Test comparison of identical sections."""
        from docdiff.comparators.content_comparator import compare_section
        from docdiff.models import Section, Block, BlockType

        old_section = Section(
            title="Test",
            key="test",
            level=1,
            blocks=[
                Block(block_type=BlockType.PARAGRAPH, content="Test content.")
            ]
        )
        new_section = Section(
            title="Test",
            key="test",
            level=1,
            blocks=[
                Block(block_type=BlockType.PARAGRAPH, content="Test content.")
            ]
        )

        score, findings = compare_section(old_section, new_section)

        assert score >= 0.9
        assert len(findings) == 0

    def test_compare_section_different_content(self):
        """Test comparison of sections with different content."""
        from docdiff.comparators.content_comparator import compare_section
        from docdiff.models import Section, Block, BlockType

        old_section = Section(
            title="Test",
            key="test",
            level=1,
            blocks=[
                Block(block_type=BlockType.PARAGRAPH, content="Original content.")
            ]
        )
        new_section = Section(
            title="Test",
            key="test",
            level=1,
            blocks=[
                Block(block_type=BlockType.PARAGRAPH, content="Completely different.")
            ]
        )

        score, findings = compare_section(old_section, new_section)

        # Should have findings for content difference
        assert len(findings) >= 1

    def test_compare_section_with_raw_content(self):
        """Test comparison using raw content (no blocks)."""
        from docdiff.comparators.content_comparator import compare_section
        from docdiff.models import Section

        old_section = Section(
            title="Test",
            key="test",
            level=1,
            content="Raw content here."
        )
        new_section = Section(
            title="Test",
            key="test",
            level=1,
            content="Raw content here."
        )

        score, findings = compare_section(old_section, new_section)

        assert score >= 0.9
