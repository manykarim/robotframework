"""Tests for docdiff.models module."""

import pytest

from docdiff.models import (
    Block,
    BlockType,
    Finding,
    Section,
    Severity,
    AlignmentResult,
    ComparisonResult,
)


class TestBlockType:
    """Tests for BlockType enum."""

    def test_block_type_values(self):
        """Test that all expected block types exist."""
        expected = ["paragraph", "code", "table", "list", "heading", "link", "image", "admonition", "unknown"]
        actual = [bt.value for bt in BlockType]
        assert set(expected) == set(actual)

    def test_block_type_from_value(self):
        """Test creating BlockType from string value."""
        assert BlockType("paragraph") == BlockType.PARAGRAPH
        assert BlockType("code") == BlockType.CODE


class TestSeverity:
    """Tests for Severity enum."""

    def test_severity_values(self):
        """Test that all expected severities exist."""
        expected = ["info", "warning", "error", "critical"]
        actual = [s.value for s in Severity]
        assert set(expected) == set(actual)

    def test_severity_ordering(self):
        """Test that severity names are correct."""
        assert Severity.INFO.value == "info"
        assert Severity.WARNING.value == "warning"
        assert Severity.ERROR.value == "error"
        assert Severity.CRITICAL.value == "critical"


class TestBlock:
    """Tests for Block dataclass."""

    def test_block_creation_minimal(self):
        """Test creating a block with minimal arguments."""
        block = Block(block_type=BlockType.PARAGRAPH, content="Test content")
        assert block.block_type == BlockType.PARAGRAPH
        assert block.content == "Test content"
        assert block.metadata == {}
        assert block.line_number is None

    def test_block_creation_full(self):
        """Test creating a block with all arguments."""
        block = Block(
            block_type=BlockType.CODE,
            content="print('hello')",
            metadata={"language": "python"},
            line_number=42,
        )
        assert block.block_type == BlockType.CODE
        assert block.content == "print('hello')"
        assert block.metadata == {"language": "python"}
        assert block.line_number == 42

    def test_block_to_dict(self, sample_paragraph_block):
        """Test Block.to_dict() method."""
        result = sample_paragraph_block.to_dict()
        
        assert result["type"] == "paragraph"
        assert result["content"] == sample_paragraph_block.content
        assert result["metadata"] == {}
        assert result["line_number"] == 5

    def test_block_to_dict_with_metadata(self, sample_code_block):
        """Test Block.to_dict() with metadata."""
        result = sample_code_block.to_dict()
        
        assert result["type"] == "code"
        assert result["metadata"] == {"language": "python"}

    def test_block_to_dict_preserves_all_fields(self):
        """Test that to_dict() includes all fields."""
        block = Block(
            block_type=BlockType.TABLE,
            content="col1 | col2",
            metadata={"rows": 2, "data": [["a", "b"]]},
            line_number=100,
        )
        result = block.to_dict()
        
        assert "type" in result
        assert "content" in result
        assert "metadata" in result
        assert "line_number" in result


class TestSection:
    """Tests for Section dataclass."""

    def test_section_creation_minimal(self):
        """Test creating a section with minimal arguments."""
        section = Section(number="1", title="Intro", level=1, key="intro")
        assert section.number == "1"
        assert section.title == "Intro"
        assert section.level == 1
        assert section.key == "intro"
        assert section.blocks == []
        assert section.subsections == []
        assert section.parent is None

    def test_section_creation_full(self, sample_section):
        """Test creating a section with all arguments."""
        assert sample_section.number == "2.1"
        assert sample_section.title == "Getting Started"
        assert sample_section.level == 2
        assert sample_section.key == "getting-started"
        assert sample_section.line_number == 10

    def test_section_to_dict(self, sample_section):
        """Test Section.to_dict() method."""
        result = sample_section.to_dict()
        
        assert result["number"] == "2.1"
        assert result["title"] == "Getting Started"
        assert result["level"] == 2
        assert result["key"] == "getting-started"
        assert result["line_number"] == 10
        assert result["blocks"] == []
        assert result["subsections"] == []

    def test_section_to_dict_with_blocks(self, sample_section_with_blocks):
        """Test Section.to_dict() with blocks."""
        result = sample_section_with_blocks.to_dict()
        
        assert len(result["blocks"]) == 2
        assert result["blocks"][0]["type"] == "paragraph"
        assert result["blocks"][1]["type"] == "code"

    def test_section_to_dict_with_subsections(self, sample_section_hierarchy):
        """Test Section.to_dict() with subsections."""
        root = sample_section_hierarchy["root"]
        result = root.to_dict()
        
        assert len(result["subsections"]) == 2
        assert result["subsections"][0]["title"] == "Introduction"
        assert result["subsections"][1]["title"] == "Installation"

    def test_section_get_full_path_no_parent(self, sample_section):
        """Test get_full_path() for root section."""
        assert sample_section.get_full_path() == "Getting Started"

    def test_section_get_full_path_with_parent(self, sample_section_hierarchy):
        """Test get_full_path() with parent hierarchy."""
        grandchild = sample_section_hierarchy["grandchild"]
        path = grandchild.get_full_path()
        
        assert path == "User Guide > Introduction > Overview"

    def test_section_hierarchy_parent_references(self, sample_section_hierarchy):
        """Test that parent references are correct."""
        root = sample_section_hierarchy["root"]
        child1 = sample_section_hierarchy["child1"]
        grandchild = sample_section_hierarchy["grandchild"]
        
        assert child1.parent == root
        assert grandchild.parent == child1
        assert root.parent is None


class TestFinding:
    """Tests for Finding dataclass."""

    def test_finding_creation_minimal(self):
        """Test creating a finding with minimal arguments."""
        finding = Finding(
            category="test",
            severity=Severity.INFO,
            message="Test message",
        )
        assert finding.category == "test"
        assert finding.severity == Severity.INFO
        assert finding.message == "Test message"
        assert finding.source_location is None
        assert finding.suggestion is None

    def test_finding_creation_full(self, sample_finding):
        """Test creating a finding with all arguments."""
        assert sample_finding.category == "content_difference"
        assert sample_finding.severity == Severity.WARNING
        assert sample_finding.message == "Paragraph content differs"
        assert sample_finding.source_location == "Section 2.1 - line 10"
        assert sample_finding.target_location == "Section 2.1 - line 12"
        assert sample_finding.source_content == "Original text here"
        assert sample_finding.target_content == "Modified text here"
        assert sample_finding.suggestion == "Review the changes"

    def test_finding_to_markdown_minimal(self):
        """Test to_markdown() with minimal finding."""
        finding = Finding(
            category="test_category",
            severity=Severity.ERROR,
            message="Something went wrong",
        )
        md = finding.to_markdown()
        
        assert "### ERROR: test_category" in md
        assert "Something went wrong" in md

    def test_finding_to_markdown_with_locations(self, sample_finding):
        """Test to_markdown() includes locations."""
        md = sample_finding.to_markdown()
        
        assert "**Source Location:**" in md
        assert "Section 2.1 - line 10" in md
        assert "**Target Location:**" in md
        assert "Section 2.1 - line 12" in md

    def test_finding_to_markdown_with_content(self, sample_finding):
        """Test to_markdown() includes content in code blocks."""
        md = sample_finding.to_markdown()
        
        assert "**Source Content:**" in md
        assert "```\nOriginal text here\n```" in md
        assert "**Target Content:**" in md
        assert "```\nModified text here\n```" in md

    def test_finding_to_markdown_with_suggestion(self, sample_finding):
        """Test to_markdown() includes suggestion."""
        md = sample_finding.to_markdown()
        
        assert "**Suggestion:**" in md
        assert "Review the changes" in md

    def test_finding_severity_levels_in_markdown(self):
        """Test all severity levels appear correctly in markdown."""
        for severity in Severity:
            finding = Finding(
                category="test",
                severity=severity,
                message="test",
            )
            md = finding.to_markdown()
            assert f"### {severity.value.upper()}:" in md


class TestAlignmentResult:
    """Tests for AlignmentResult dataclass."""

    def test_alignment_result_creation_empty(self):
        """Test creating an empty alignment result."""
        result = AlignmentResult()
        assert result.matched == []
        assert result.source_only == []
        assert result.target_only == []
        assert result.match_stats == {}

    def test_alignment_result_get_match_rate_empty(self):
        """Test get_match_rate() with no sections."""
        result = AlignmentResult()
        assert result.get_match_rate() == 100.0

    def test_alignment_result_get_match_rate_all_matched(self):
        """Test get_match_rate() when all sections match."""
        source = Section(number="1", title="Test", level=1, key="test")
        target = Section(number="1", title="Test", level=1, key="test")
        result = AlignmentResult(matched=[(source, target)])
        
        assert result.get_match_rate() == 100.0

    def test_alignment_result_get_match_rate_partial(self, sample_alignment_result):
        """Test get_match_rate() with partial matches."""
        # 1 matched, 2 source_only, 2 target_only = 5 total
        # 1/5 = 20%
        assert sample_alignment_result.get_match_rate() == 20.0

    def test_alignment_result_get_match_rate_no_matches(self):
        """Test get_match_rate() with no matches."""
        source = Section(number="1", title="Test", level=1, key="test")
        result = AlignmentResult(source_only=[source])
        
        assert result.get_match_rate() == 0.0


class TestComparisonResult:
    """Tests for ComparisonResult dataclass."""

    def test_comparison_result_creation_minimal(self):
        """Test creating a comparison result with minimal arguments."""
        result = ComparisonResult(source_file="a.html", target_file="b.md")
        
        assert result.source_file == "a.html"
        assert result.target_file == "b.md"
        assert result.findings == []
        assert result.alignment is None
        assert result.metadata == {}

    def test_comparison_result_summary_empty(self):
        """Test summary() with no findings."""
        result = ComparisonResult(source_file="a.html", target_file="b.md")
        summary = result.summary()
        
        assert summary["source_file"] == "a.html"
        assert summary["target_file"] == "b.md"
        assert summary["total_findings"] == 0
        assert summary["match_rate"] == 0.0
        assert all(v == 0 for v in summary["by_severity"].values())

    def test_comparison_result_summary_with_findings(self, sample_comparison_result):
        """Test summary() counts findings correctly."""
        summary = sample_comparison_result.summary()
        
        assert summary["total_findings"] == 4
        assert summary["by_severity"]["error"] == 1
        assert summary["by_severity"]["warning"] == 1
        assert summary["by_severity"]["info"] == 1
        assert summary["by_severity"]["critical"] == 1

    def test_comparison_result_summary_by_category(self, sample_comparison_result):
        """Test summary() groups by category."""
        summary = sample_comparison_result.summary()
        
        assert "missing_section" in summary["by_category"]
        assert "content_difference" in summary["by_category"]
        assert "formatting_change" in summary["by_category"]
        assert "broken_link" in summary["by_category"]

    def test_comparison_result_summary_match_rate(self, sample_comparison_result):
        """Test summary() includes alignment match rate."""
        summary = sample_comparison_result.summary()
        
        # From sample_alignment_result: 1 matched out of 5 = 20%
        assert summary["match_rate"] == 20.0

    def test_comparison_result_summary_metadata(self, sample_comparison_result):
        """Test summary() includes metadata."""
        summary = sample_comparison_result.summary()
        
        assert summary["metadata"] == {"comparison_time": 1.5}
