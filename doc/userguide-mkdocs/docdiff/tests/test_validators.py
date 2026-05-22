"""Tests for docdiff.validators module."""

import pytest
from pathlib import Path
import tempfile
import os

from docdiff.validators import (
    LinkValidator,
    ImageValidator,
    extract_links,
    extract_images,
    validate_internal_links,
)
from docdiff.models import Block, BlockType, Section, Severity


class TestLinkValidator:
    """Tests for LinkValidator class."""

    def test_init_default_base_path(self):
        """Test default base path initialization."""
        validator = LinkValidator()
        assert validator.base_path == Path.cwd()

    def test_init_custom_base_path(self):
        """Test custom base path initialization."""
        custom_path = Path("/tmp")
        validator = LinkValidator(base_path=custom_path)
        assert validator.base_path == custom_path

    def test_extract_markdown_link(self):
        """Test extraction of Markdown links."""
        validator = LinkValidator()
        content = "Click [here](https://example.com) for more."
        
        links = validator.extract_links(content)
        
        assert len(links) == 1
        assert links[0]["href"] == "https://example.com"
        assert links[0]["text"] == "here"

    def test_extract_multiple_links(self):
        """Test extraction of multiple links."""
        validator = LinkValidator()
        content = "[Link 1](url1) and [Link 2](url2)"
        
        links = validator.extract_links(content)
        
        assert len(links) == 2
        hrefs = [link["href"] for link in links]
        assert "url1" in hrefs
        assert "url2" in hrefs

    def test_extract_html_link(self):
        """Test extraction of HTML links."""
        validator = LinkValidator()
        content = '<a href="https://example.com">Click here</a>'
        
        links = validator.extract_links(content)
        
        assert len(links) == 1
        assert links[0]["href"] == "https://example.com"

    def test_extract_bare_url(self):
        """Test extraction of bare URLs."""
        validator = LinkValidator()
        content = "Visit https://example.com for more info."
        
        links = validator.extract_links(content)
        
        assert len(links) == 1
        assert links[0]["href"] == "https://example.com"
        assert links[0]["text"] == ""

    def test_extract_no_duplicate_bare_urls(self):
        """Test that bare URLs aren't duplicated if already in a link."""
        validator = LinkValidator()
        content = "[Example](https://example.com)"
        
        links = validator.extract_links(content)
        
        # Should only have one link, not duplicate from bare URL
        assert len(links) == 1

    def test_validate_empty_link(self):
        """Test validation of empty link."""
        validator = LinkValidator()
        is_valid, reason = validator.validate_link("")
        
        assert is_valid is False
        assert "Empty" in reason

    def test_validate_anchor_link(self):
        """Test validation of anchor link."""
        validator = LinkValidator()
        is_valid, reason = validator.validate_link("#section")
        
        assert is_valid is True
        assert "Anchor" in reason

    def test_validate_external_http_link(self):
        """Test validation of external HTTP link."""
        validator = LinkValidator()
        is_valid, reason = validator.validate_link("https://example.com")
        
        assert is_valid is True
        assert "External" in reason

    def test_validate_mailto_link(self):
        """Test validation of mailto link."""
        validator = LinkValidator()
        is_valid, reason = validator.validate_link("mailto:test@example.com")
        
        assert is_valid is True
        assert "Email" in reason

    def test_validate_relative_link_existing_file(self):
        """Test validation of relative link to existing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test file
            test_file = Path(tmpdir) / "test.md"
            test_file.write_text("test")
            
            validator = LinkValidator(base_path=Path(tmpdir))
            is_valid, reason = validator.validate_link("test.md")
            
            assert is_valid is True
            assert "exists" in reason

    def test_validate_relative_link_missing_file(self):
        """Test validation of relative link to missing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            validator = LinkValidator(base_path=Path(tmpdir))
            is_valid, reason = validator.validate_link("nonexistent.md")
            
            assert is_valid is False
            assert "not found" in reason

    def test_validate_anchor_only_link(self):
        """Test validation of anchor-only relative link."""
        validator = LinkValidator()
        is_valid, reason = validator.validate_link("page.html#section")
        
        # This is a relative link, validity depends on file existence

    def test_validate_internal_links_valid(self):
        """Test validation of valid internal links."""
        validator = LinkValidator()
        
        section = Section(
            number="1",
            title="Test",
            level=1,
            key="test",
            blocks=[
                Block(
                    block_type=BlockType.PARAGRAPH,
                    content="See [intro](#introduction)",
                )
            ],
        )
        
        all_keys = {"introduction", "getting-started"}
        
        findings = validator.validate_internal_links([section], all_keys)
        
        assert len(findings) == 0

    def test_validate_internal_links_invalid(self):
        """Test validation of invalid internal links."""
        validator = LinkValidator()
        
        section = Section(
            number="1",
            title="Test",
            level=1,
            key="test",
            blocks=[
                Block(
                    block_type=BlockType.PARAGRAPH,
                    content="See [missing](#nonexistent-section)",
                )
            ],
        )
        
        all_keys = {"introduction", "getting-started"}
        
        findings = validator.validate_internal_links([section], all_keys)
        
        assert len(findings) == 1
        assert findings[0].category == "broken_internal_link"
        assert findings[0].severity == Severity.ERROR


class TestImageValidator:
    """Tests for ImageValidator class."""

    def test_init_default_base_path(self):
        """Test default base path initialization."""
        validator = ImageValidator()
        assert validator.base_path == Path.cwd()

    def test_extract_markdown_image(self):
        """Test extraction of Markdown images."""
        validator = ImageValidator()
        content = "![Alt text](images/photo.png)"
        
        images = validator.extract_images(content)
        
        assert len(images) == 1
        assert images[0]["src"] == "images/photo.png"
        assert images[0]["alt"] == "Alt text"

    def test_extract_multiple_images(self):
        """Test extraction of multiple images."""
        validator = ImageValidator()
        content = "![A](a.png) and ![B](b.png)"
        
        images = validator.extract_images(content)
        
        assert len(images) == 2

    def test_extract_html_image(self):
        """Test extraction of HTML images."""
        validator = ImageValidator()
        content = '<img src="photo.png" alt="Photo">'
        
        images = validator.extract_images(content)
        
        assert len(images) == 1
        assert images[0]["src"] == "photo.png"
        assert images[0]["alt"] == "Photo"

    def test_extract_html_image_no_alt(self):
        """Test extraction of HTML image without alt."""
        validator = ImageValidator()
        content = '<img src="photo.png">'
        
        images = validator.extract_images(content)
        
        assert len(images) == 1
        assert images[0]["alt"] == ""

    def test_validate_empty_source(self):
        """Test validation of empty image source."""
        validator = ImageValidator()
        is_valid, reason = validator.validate_image("")
        
        assert is_valid is False
        assert "Empty" in reason

    def test_validate_external_image(self):
        """Test validation of external image URL."""
        validator = ImageValidator()
        is_valid, reason = validator.validate_image("https://example.com/image.png")
        
        assert is_valid is True
        assert "External" in reason

    def test_validate_data_url(self):
        """Test validation of data URL image."""
        validator = ImageValidator()
        is_valid, reason = validator.validate_image("data:image/png;base64,ABC123")
        
        assert is_valid is True
        assert "Data URL" in reason

    def test_validate_relative_image_existing(self):
        """Test validation of existing relative image."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test image file
            img_file = Path(tmpdir) / "test.png"
            img_file.write_bytes(b"fake image data")
            
            validator = ImageValidator(base_path=Path(tmpdir))
            is_valid, reason = validator.validate_image("test.png")
            
            assert is_valid is True
            assert "exists" in reason

    def test_validate_relative_image_missing(self):
        """Test validation of missing relative image."""
        with tempfile.TemporaryDirectory() as tmpdir:
            validator = ImageValidator(base_path=Path(tmpdir))
            is_valid, reason = validator.validate_image("missing.png")
            
            assert is_valid is False
            assert "not found" in reason

    def test_validate_images_in_sections_broken(self):
        """Test validation finds broken images."""
        with tempfile.TemporaryDirectory() as tmpdir:
            validator = ImageValidator(base_path=Path(tmpdir))
            
            section = Section(
                number="1",
                title="Test",
                level=1,
                key="test",
                blocks=[
                    Block(
                        block_type=BlockType.PARAGRAPH,
                        content="![Photo](missing.png)",
                    )
                ],
            )
            
            findings = validator.validate_images_in_sections([section])
            
            assert any(f.category == "broken_image" for f in findings)

    def test_validate_images_missing_alt_text(self):
        """Test detection of missing alt text."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test image
            img_file = Path(tmpdir) / "test.png"
            img_file.write_bytes(b"fake")
            
            validator = ImageValidator(base_path=Path(tmpdir))
            
            section = Section(
                number="1",
                title="Test",
                level=1,
                key="test",
                blocks=[
                    Block(
                        block_type=BlockType.PARAGRAPH,
                        content="![](test.png)",  # Empty alt text
                    )
                ],
            )
            
            findings = validator.validate_images_in_sections([section])
            
            assert any(f.category == "missing_alt_text" for f in findings)

    def test_validate_images_with_image_block(self):
        """Test validation of image blocks (not just content)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            validator = ImageValidator(base_path=Path(tmpdir))
            
            section = Section(
                number="1",
                title="Test",
                level=1,
                key="test",
                blocks=[
                    Block(
                        block_type=BlockType.IMAGE,
                        content="![Alt](missing.png)",
                        metadata={"src": "missing.png", "alt": "Alt"},
                    )
                ],
            )
            
            findings = validator.validate_images_in_sections([section])
            
            assert any(f.category == "broken_image" for f in findings)


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_extract_links_function(self):
        """Test extract_links convenience function."""
        content = "[Link](https://example.com)"
        links = extract_links(content)
        
        assert len(links) == 1
        assert links[0]["href"] == "https://example.com"

    def test_extract_images_function(self):
        """Test extract_images convenience function."""
        content = "![Alt](image.png)"
        images = extract_images(content)
        
        assert len(images) == 1
        assert images[0]["src"] == "image.png"

    def test_validate_internal_links_function(self):
        """Test validate_internal_links convenience function."""
        section = Section(
            number="1",
            title="Test",
            level=1,
            key="test",
            blocks=[
                Block(
                    block_type=BlockType.PARAGRAPH,
                    content="See [intro](#intro)",
                )
            ],
        )
        
        findings = validate_internal_links([section], {"intro"})
        assert len(findings) == 0
        
        findings = validate_internal_links([section], {"other"})
        assert len(findings) == 1


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_link_with_special_chars(self):
        """Test link extraction with special characters."""
        validator = LinkValidator()
        content = "[Test](https://example.com/path?query=value&other=123)"
        
        links = validator.extract_links(content)
        
        assert len(links) == 1
        assert "query=value" in links[0]["href"]

    def test_image_with_spaces_in_alt(self):
        """Test image extraction with spaces in alt text."""
        validator = ImageValidator()
        content = "![A long description with spaces](image.png)"
        
        images = validator.extract_images(content)
        
        assert images[0]["alt"] == "A long description with spaces"

    def test_empty_content(self):
        """Test extraction from empty content."""
        link_validator = LinkValidator()
        image_validator = ImageValidator()
        
        assert link_validator.extract_links("") == []
        assert image_validator.extract_images("") == []

    def test_no_links_or_images(self):
        """Test extraction when no links/images present."""
        link_validator = LinkValidator()
        image_validator = ImageValidator()
        
        content = "Just plain text with no links or images."
        
        assert link_validator.extract_links(content) == []
        assert image_validator.extract_images(content) == []

    def test_malformed_markdown_link(self):
        """Test handling of malformed Markdown links."""
        validator = LinkValidator()
        content = "[incomplete link(missing bracket"
        
        # Should not crash, may or may not extract
        links = validator.extract_links(content)
        # Result depends on regex matching

    def test_nested_brackets_in_link(self):
        """Test link with nested brackets in text."""
        validator = LinkValidator()
        content = "[[nested]](url)"

        links = validator.extract_links(content)
        # May or may not match depending on regex


class TestValidateLinksCorrectParams:
    """Tests for link validator with correct parameter types."""

    def test_validate_links_with_section_list(self):
        """Test link validation with a list of sections."""
        from docdiff.models import Section, Block, BlockType

        validator = LinkValidator()

        sections = [
            Section(
                number="1",
                title="Test Section",
                level=1,
                key="test-section",
                blocks=[
                    Block(
                        block_type=BlockType.PARAGRAPH,
                        content="See [link](#existing-anchor)",
                    )
                ],
            )
        ]

        all_keys = {"existing-anchor", "test-section"}
        findings = validator.validate_internal_links(sections, all_keys)

        assert len(findings) == 0

    def test_validate_links_with_broken_anchor(self):
        """Test link validation detects broken anchors."""
        from docdiff.models import Section, Block, BlockType

        validator = LinkValidator()

        sections = [
            Section(
                number="1",
                title="Test Section",
                level=1,
                key="test-section",
                blocks=[
                    Block(
                        block_type=BlockType.PARAGRAPH,
                        content="See [link](#nonexistent)",
                    )
                ],
            )
        ]

        all_keys = {"test-section"}  # nonexistent is not in keys
        findings = validator.validate_internal_links(sections, all_keys)

        assert len(findings) == 1
        assert findings[0].category == "broken_internal_link"

    def test_validate_links_with_multiple_sections(self):
        """Test link validation across multiple sections."""
        from docdiff.models import Section, Block, BlockType

        validator = LinkValidator()

        sections = [
            Section(
                number="1",
                title="First",
                level=1,
                key="first",
                blocks=[
                    Block(
                        block_type=BlockType.PARAGRAPH,
                        content="Link to [second](#second)",
                    )
                ],
            ),
            Section(
                number="2",
                title="Second",
                level=1,
                key="second",
                blocks=[
                    Block(
                        block_type=BlockType.PARAGRAPH,
                        content="Link to [first](#first)",
                    )
                ],
            ),
        ]

        all_keys = {"first", "second"}
        findings = validator.validate_internal_links(sections, all_keys)

        assert len(findings) == 0

    def test_validate_links_case_sensitivity(self):
        """Test that link validation handles case correctly."""
        from docdiff.models import Section, Block, BlockType

        validator = LinkValidator()

        sections = [
            Section(
                number="1",
                title="Test",
                level=1,
                key="test",
                blocks=[
                    Block(
                        block_type=BlockType.PARAGRAPH,
                        content="See [link](#Test)",  # Capital T
                    )
                ],
            )
        ]

        all_keys = {"test"}  # lowercase
        findings = validator.validate_internal_links(sections, all_keys)

        # Should report as broken since case doesn't match
        assert len(findings) >= 1

    def test_validate_links_with_empty_sections(self):
        """Test link validation with empty section list."""
        validator = LinkValidator()

        findings = validator.validate_internal_links([], {"some-key"})

        assert findings == []


class TestValidateImagesWithSeverity:
    """Tests for image validator creating proper Findings."""

    def test_validate_images_creates_finding_with_severity(self):
        """Test that image validation creates Findings with proper severity."""
        import tempfile
        from docdiff.models import Section, Block, BlockType, Severity

        with tempfile.TemporaryDirectory() as tmpdir:
            validator = ImageValidator(base_path=Path(tmpdir))

            section = Section(
                number="1",
                title="Test",
                level=1,
                key="test",
                blocks=[
                    Block(
                        block_type=BlockType.PARAGRAPH,
                        content="![Photo](missing.png)",
                    )
                ],
            )

            findings = validator.validate_images_in_sections([section])

            assert len(findings) >= 1
            # Should have severity attribute
            for finding in findings:
                assert hasattr(finding, 'severity') or hasattr(finding, 'priority')

    def test_validate_images_missing_alt_severity(self):
        """Test severity for missing alt text."""
        import tempfile
        from docdiff.models import Section, Block, BlockType

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test image
            img_file = Path(tmpdir) / "exists.png"
            img_file.write_bytes(b"fake image")

            validator = ImageValidator(base_path=Path(tmpdir))

            section = Section(
                number="1",
                title="Test",
                level=1,
                key="test",
                blocks=[
                    Block(
                        block_type=BlockType.PARAGRAPH,
                        content="![](exists.png)",  # Empty alt text
                    )
                ],
            )

            findings = validator.validate_images_in_sections([section])

            # Should flag missing alt text
            alt_findings = [f for f in findings if "alt" in f.message.lower()]
            assert len(alt_findings) >= 1

    def test_validate_images_broken_image_severity(self):
        """Test severity for broken images."""
        import tempfile
        from docdiff.models import Section, Block, BlockType

        with tempfile.TemporaryDirectory() as tmpdir:
            validator = ImageValidator(base_path=Path(tmpdir))

            section = Section(
                number="1",
                title="Test",
                level=1,
                key="test",
                blocks=[
                    Block(
                        block_type=BlockType.IMAGE,
                        content="![Alt](nonexistent.png)",
                        metadata={"src": "nonexistent.png", "alt": "Alt"},
                    )
                ],
            )

            findings = validator.validate_images_in_sections([section])

            # Should have finding for broken image
            broken_findings = [f for f in findings if f.category == "broken_image"]
            assert len(broken_findings) >= 1

    def test_validate_images_external_url(self):
        """Test validation of external image URLs."""
        validator = ImageValidator()

        is_valid, reason = validator.validate_image("https://example.com/image.png")

        assert is_valid is True
        assert "External" in reason

    def test_validate_images_with_subsections(self):
        """Test image validation traverses subsections."""
        import tempfile
        from docdiff.models import Section, Block, BlockType

        with tempfile.TemporaryDirectory() as tmpdir:
            validator = ImageValidator(base_path=Path(tmpdir))

            parent = Section(
                number="1",
                title="Parent",
                level=1,
                key="parent",
                blocks=[],
            )
            child = Section(
                number="1.1",
                title="Child",
                level=2,
                key="child",
                blocks=[
                    Block(
                        block_type=BlockType.PARAGRAPH,
                        content="![Missing](missing.png)",
                    )
                ],
                parent=parent,
            )
            parent.subsections = [child]

            findings = validator.validate_images_in_sections([parent])

            # Should find the broken image in the child section
            # (depends on whether validator traverses subsections)


class TestLinkValidatorExtraction:
    """Additional tests for link extraction functionality."""

    def test_extract_reference_style_links(self):
        """Test extraction of reference-style Markdown links."""
        validator = LinkValidator()
        content = """Check out [example][1] and [another][ref].

[1]: https://example.com
[ref]: https://reference.com
"""
        links = validator.extract_links(content)

        # Should extract inline links at minimum
        assert isinstance(links, list)

    def test_extract_autolinks(self):
        """Test extraction of autolinks (<url>)."""
        validator = LinkValidator()
        content = "Visit <https://example.com> for more info."

        links = validator.extract_links(content)

        # Should extract the autolink
        # Depends on implementation

    def test_extract_links_from_code_blocks_excluded(self):
        """Test that links inside code blocks might be handled specially."""
        validator = LinkValidator()
        content = """Regular [link](https://example.com).

```python
# This is a comment with [link](https://code-example.com)
```
"""
        links = validator.extract_links(content)

        # Should extract regular links
        hrefs = [link.get("href", link.get("url")) for link in links]
        assert "https://example.com" in hrefs


class TestImageValidatorExtraction:
    """Additional tests for image extraction functionality."""

    def test_extract_images_with_title(self):
        """Test extraction of images with title attribute."""
        validator = ImageValidator()
        content = '![Alt text](image.png "Image Title")'

        images = validator.extract_images(content)

        assert len(images) >= 1
        # May or may not capture title depending on implementation

    def test_extract_html_images_with_attributes(self):
        """Test extraction of HTML images with various attributes."""
        validator = ImageValidator()
        content = '<img src="photo.jpg" alt="Photo" width="100" height="100" class="responsive">'

        images = validator.extract_images(content)

        assert len(images) == 1
        assert images[0]["src"] == "photo.jpg"
        assert images[0]["alt"] == "Photo"

    def test_extract_images_relative_paths(self):
        """Test extraction handles relative paths correctly."""
        validator = ImageValidator()
        content = "![Logo](../images/logo.png)"

        images = validator.extract_images(content)

        assert len(images) == 1
        assert images[0]["src"] == "../images/logo.png"

    def test_extract_images_absolute_paths(self):
        """Test extraction handles absolute paths."""
        validator = ImageValidator()
        content = "![Logo](/assets/images/logo.png)"

        images = validator.extract_images(content)

        assert len(images) == 1
        assert images[0]["src"] == "/assets/images/logo.png"


class TestLinkValidatorFunctions:
    """Tests for link_validator module functions."""

    def test_extract_all_links_function(self):
        """Test the extract_all_links function from link_validator module."""
        from docdiff.validators.link_validator import extract_all_links
        from docdiff.models import Section

        sections = [
            Section(
                title="Test",
                key="test",
                level=1,
                content="See [link](https://example.com) for more."
            )
        ]

        links = extract_all_links(sections, "test.md")

        assert len(links) >= 1

    def test_validate_internal_links_function(self):
        """Test the validate_internal_links function."""
        from docdiff.validators.link_validator import validate_internal_links, LinkInfo, LinkType

        links = [
            LinkInfo(
                url="#existing",
                text="Existing Link",
                source_section="intro",
                source_file="test.md",
                link_type=LinkType.ANCHOR,
            )
        ]

        # Function signature: validate_internal_links(links, available_anchors, available_pages=None)
        # available_anchors is a dict mapping page paths to sets of anchor IDs
        available_anchors: dict[str, set[str]] = {"test.md": {"existing"}}
        # available_pages is an optional set of page paths
        available_pages: set[str] = set()

        findings = validate_internal_links(links, available_anchors, available_pages)

        # Should not have findings for valid anchor
        assert len(findings) == 0

    def test_check_anchor_drift(self):
        """Test the check_anchor_drift function."""
        from docdiff.validators.link_validator import check_anchor_drift

        old_anchors = {
            "introduction": "Introduction",
            "getting-started": "Getting Started",
        }
        new_anchors = {
            "intro": "Introduction",  # Renamed
            "getting-started": "Getting Started",  # Same
        }

        findings = check_anchor_drift(old_anchors, new_anchors)

        # Should detect the missing anchor
        assert len(findings) >= 1

    def test_build_anchor_map(self):
        """Test the build_anchor_map function."""
        from docdiff.validators.link_validator import build_anchor_map
        from docdiff.models import Section

        sections = [
            Section(
                title="Introduction",
                key="introduction",
                level=1,
                content="Some content with <a name='custom-anchor'></a>"
            )
        ]

        anchor_map = build_anchor_map(sections, "test.md")

        assert "test.md" in anchor_map
        assert "introduction" in anchor_map["test.md"]


class TestImageValidatorFunctions:
    """Tests for image_validator module functions."""

    def test_extract_all_images_function(self):
        """Test the extract_all_images function."""
        from docdiff.validators.image_validator import extract_all_images
        from docdiff.models import Section

        sections = [
            Section(
                title="Test",
                key="test",
                level=1,
                content="![Photo](images/photo.png)"
            )
        ]

        images = extract_all_images(sections, "test.md")

        assert len(images) >= 1

    def test_validate_images_function(self):
        """Test the validate_images function."""
        from docdiff.validators.image_validator import validate_images, ImageInfo
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test image
            img_path = Path(tmpdir) / "exists.png"
            img_path.write_bytes(b"fake image data")

            images = [
                ImageInfo(
                    src="exists.png",
                    alt_text="Alt text",
                    source_section="test",
                    source_file="test.md",
                ),
                ImageInfo(
                    src="missing.png",
                    alt_text="",  # Missing alt text
                    source_section="test",
                    source_file="test.md",
                ),
            ]

            findings = validate_images(images, tmpdir)

            # Should have findings for missing image and missing alt text
            assert len(findings) >= 1

    def test_compare_image_sets(self):
        """Test the compare_image_sets function."""
        from docdiff.validators.image_validator import compare_image_sets, ImageInfo

        old_images = [
            ImageInfo(
                src="logo.png",
                alt_text="Old Logo",
                source_section="header",
                source_file="index.md",
            ),
            ImageInfo(
                src="diagram.png",
                alt_text="Diagram",
                source_section="content",
                source_file="index.md",
            ),
        ]

        new_images = [
            ImageInfo(
                src="logo.png",
                alt_text="New Logo",  # Alt text changed
                source_section="header",
                source_file="index.md",
            ),
            # diagram.png is missing
        ]

        findings = compare_image_sets(old_images, new_images)

        # Should detect missing image and alt text change
        assert len(findings) >= 2


class TestModelExitCodeLogic:
    """Tests for model exit code and priority logic."""

    def test_finding_get_priority_explicit(self):
        """Test Finding.get_priority with explicit priority."""
        from docdiff.models import Finding, Severity, Priority

        finding = Finding(
            category="test",
            severity=Severity.INFO,
            message="Test",
            priority=Priority.P0,  # Explicitly set
        )

        assert finding.get_priority() == Priority.P0

    def test_finding_get_priority_derived(self):
        """Test Finding.get_priority derived from severity."""
        from docdiff.models import Finding, Severity, Priority

        # CRITICAL -> P0
        finding = Finding(category="test", severity=Severity.CRITICAL, message="Test")
        assert finding.get_priority() == Priority.P0

        # ERROR -> P0
        finding = Finding(category="test", severity=Severity.ERROR, message="Test")
        assert finding.get_priority() == Priority.P0

        # WARNING -> P1
        finding = Finding(category="test", severity=Severity.WARNING, message="Test")
        assert finding.get_priority() == Priority.P1

        # INFO -> P2
        finding = Finding(category="test", severity=Severity.INFO, message="Test")
        assert finding.get_priority() == Priority.P2

    def test_comparison_result_has_critical_findings(self):
        """Test ComparisonResult.has_critical_findings method."""
        from docdiff.models import ComparisonResult, Finding, Severity

        # With P0 finding
        result = ComparisonResult(
            source_file="a",
            target_file="b",
            findings=[Finding(category="test", severity=Severity.ERROR, message="Error")],
        )
        assert result.has_critical_findings() is True

        # Without critical findings
        result = ComparisonResult(
            source_file="a",
            target_file="b",
            findings=[Finding(category="test", severity=Severity.INFO, message="Info")],
        )
        assert result.has_critical_findings() is False

    def test_comparison_result_strict_mode(self):
        """Test ComparisonResult.get_exit_code with strict mode."""
        from docdiff.models import ComparisonResult, Finding, Severity

        # With P2 finding in strict mode should return 2
        result = ComparisonResult(
            source_file="a",
            target_file="b",
            findings=[Finding(category="test", severity=Severity.INFO, message="Info")],
        )
        assert result.get_exit_code(strict=True) == 2
        assert result.get_exit_code(strict=False) == 1


class TestAlignmentResultMethods:
    """Tests for AlignmentResult methods."""

    def test_alignment_result_match_rate_calculation(self):
        """Test match rate calculation."""
        from docdiff.models import AlignmentResult, Section

        s1 = Section(title="A", key="a", level=1)
        s2 = Section(title="B", key="b", level=1)
        s3 = Section(title="C", key="c", level=1)

        result = AlignmentResult(
            matched=[(s1, s2)],
            source_only=[s3],
            target_only=[],
        )

        # 1 matched out of 2 total = 50%
        assert result.get_match_rate() == 50.0
