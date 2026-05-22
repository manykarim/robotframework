# DocDiff API Reference

This document provides comprehensive API documentation for all public modules in DocDiff.

## Table of Contents

- [Models](#models)
- [Extractors](#extractors)
- [Normalizers](#normalizers)
- [Aligners](#aligners)
- [Comparators](#comparators)
- [Validators](#validators)
- [Reporters](#reporters)
- [CLI](#cli)

---

## Models

**Module:** `docdiff.models`

Core data classes representing documents, sections, blocks, and comparison results.

### Enumerations

#### `BlockType`

Types of content blocks within a section.

```python
class BlockType(Enum):
    PARAGRAPH = "paragraph"
    CODE = "code"
    TABLE = "table"
    LIST = "list"
    HEADING = "heading"
    LINK = "link"
    IMAGE = "image"
    ADMONITION = "admonition"
    UNKNOWN = "unknown"
```

#### `Severity`

Severity levels for findings.

```python
class Severity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
```

#### `Priority`

Priority levels for findings (compatible with CLI exit codes).

```python
class Priority(Enum):
    P0 = 0  # Critical - must fix immediately
    P1 = 1  # Important - should fix soon
    P2 = 2  # Minor - nice to fix
```

**Methods:**

- `from_severity(severity: Severity) -> Priority`: Convert severity to priority level

#### `FindingCategory`

Categories for classifying findings.

```python
class FindingCategory(Enum):
    CONTENT_MISSING = "content_missing"
    CONTENT_CHANGED = "content_changed"
    CONTENT_ADDED = "content_added"
    STRUCTURE_CHANGED = "structure_changed"
    FORMATTING_CHANGED = "formatting_changed"
    LINK_BROKEN = "link_broken"
    LINK_CHANGED = "link_changed"
    CODE_BLOCK_CHANGED = "code_block_changed"
    TABLE_CHANGED = "table_changed"
    IMAGE_MISSING = "image_missing"
    ANCHOR_MISSING = "anchor_missing"
    HEADING_LEVEL_CHANGED = "heading_level_changed"
    SEMANTIC_DRIFT = "semantic_drift"
    WHITESPACE_ONLY = "whitespace_only"
```

### Data Classes

#### `Block`

A content block within a section.

```python
@dataclass
class Block:
    block_type: BlockType | str = BlockType.UNKNOWN
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    line_number: int | None = None
    # Extended attributes
    text: str | None = None          # Alias for content
    language: str | None = None      # For code blocks
    admonition_type: str | None = None
    level: int | None = None         # For lists
    ordered: bool | None = None      # For lists
    items: list[str] | None = None   # For lists
    href: str | None = None          # For links
    src: str | None = None           # For images
    alt: str | None = None           # For images
    matrix: list[list[str]] | None = None  # For tables
    anchor: str | None = None        # For headings
```

**Methods:**

- `to_dict() -> dict[str, Any]`: Convert block to dictionary representation

#### `Section`

A section of the document with heading and content blocks.

```python
@dataclass
class Section:
    title: str
    key: str                         # Normalized key for matching
    level: int = 1                   # Heading level (1-6)
    number: str = ""                 # Section number (e.g., "2.1.3")
    blocks: list[Block] = field(default_factory=list)
    subsections: list["Section"] = field(default_factory=list)
    parent: "Section | None" = None
    line_number: int | None = None
    content: str = ""                # Raw content
    source_type: str = ""            # "markdown" or "html"
    source_path: str = ""            # File path
    anchor: str = ""                 # Anchor ID
```

**Methods:**

- `to_dict() -> dict[str, Any]`: Convert section to dictionary
- `get_full_path() -> str`: Get hierarchical path (e.g., "Chapter > Section > Subsection")

#### `Finding`

A comparison finding or issue.

```python
@dataclass
class Finding:
    category: str
    severity: Severity
    message: str
    source_location: str | None = None
    target_location: str | None = None
    source_content: str | None = None
    target_content: str | None = None
    suggestion: str | None = None
    priority: Priority | None = None
    # Extended attributes
    location: str | None = None      # Alias for source_location
    section_key: str | None = None
    old_value: str | None = None     # Alias for source_content
    new_value: str | None = None     # Alias for target_content
    evidence: str | None = None
    line_number: int | None = None
```

**Methods:**

- `get_priority() -> Priority`: Get priority (explicit or derived from severity)
- `to_markdown() -> str`: Convert finding to Markdown format

#### `AlignmentResult`

Result of section alignment.

```python
@dataclass
class AlignmentResult:
    matched: list[tuple[Section, Section]] = field(default_factory=list)
    source_only: list[Section] = field(default_factory=list)
    target_only: list[Section] = field(default_factory=list)
    match_stats: dict[str, int] = field(default_factory=dict)
```

**Methods:**

- `get_match_rate() -> float`: Calculate match rate as percentage

#### `SectionMatch`

Represents a match between old and new sections.

```python
@dataclass
class SectionMatch:
    old_section: Section
    new_section: Section | None = None
    similarity: float = 0.0
    matched: bool = False
    findings: list[Finding] = field(default_factory=list)
```

**Methods:**

- `to_dict() -> dict[str, Any]`: Convert to dictionary

#### `ComparisonResult`

Overall comparison result.

```python
@dataclass
class ComparisonResult:
    source_file: str
    target_file: str
    findings: list[Finding] = field(default_factory=list)
    alignment: AlignmentResult | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    matches: list[SectionMatch] = field(default_factory=list)
    missing_sections: list[Section] = field(default_factory=list)
    extra_sections: list[Section] = field(default_factory=list)
    timestamp: str = ""
```

**Properties:**

- `old_source`: Alias for source_file
- `new_source`: Alias for target_file
- `total_old_sections`: Total sections in old document
- `matched_count`: Number of successfully matched sections
- `match_percentage`: Percentage of matched sections

**Methods:**

- `get_findings_by_priority(priority: Priority) -> list[Finding]`
- `get_findings_by_category(category: str) -> list[Finding]`
- `has_critical_findings() -> bool`: Check for P0/P1 findings
- `has_warnings() -> bool`: Check for P2 findings
- `get_exit_code(strict: bool = False) -> int`: Determine CLI exit code
- `to_dict() -> dict[str, Any]`: Convert to dictionary for JSON
- `summary() -> dict[str, Any]`: Generate summary statistics

---

## Extractors

**Module:** `docdiff.extractors`

Extract structured content from HTML and Markdown documents.

### Functions

#### `extract_from_html_file(file_path: str) -> list[Section]`

Extract sections from an HTML file.

```python
from docdiff.extractors import extract_from_html_file

sections = extract_from_html_file("userguide.html")
for section in sections:
    print(f"{section.number} {section.title}")
```

#### `extract_sections_from_html(content: str) -> list[Section]`

Extract sections from HTML content string.

```python
from docdiff.extractors import extract_sections_from_html

html = "<h1>Title</h1><p>Content</p>"
sections = extract_sections_from_html(html)
```

#### `extract_from_directory(dir_path: str) -> dict[str, list[Section]]`

Extract sections from all Markdown files in a directory.

```python
from docdiff.extractors import extract_from_directory

sections_by_file = extract_from_directory("docs/")
for file_path, sections in sections_by_file.items():
    print(f"{file_path}: {len(sections)} sections")
```

#### `extract_sections_from_markdown(content: str) -> list[Section]`

Extract sections from Markdown content string.

```python
from docdiff.extractors import extract_sections_from_markdown

md = "# Title\n\nParagraph content"
sections = extract_sections_from_markdown(md)
```

#### `generate_anchor(title: str) -> str`

Generate an anchor ID from a heading title.

```python
from docdiff.extractors import generate_anchor

anchor = generate_anchor("2.1 Creating Variables")
# Returns: "creating-variables"
```

### Classes

#### `HTMLContentExtractor`

Parse HTML and extract structured content.

```python
from docdiff.extractors import HTMLContentExtractor

extractor = HTMLContentExtractor()
extractor.feed(html_content)
sections = extractor.get_sections()
```

#### `MarkdownExtractor`

Extract structured content from Markdown.

```python
from docdiff.extractors import MarkdownExtractor

extractor = MarkdownExtractor()
sections = extractor.extract(markdown_content)
```

---

## Normalizers

**Module:** `docdiff.normalizers`

Text normalization utilities for comparison.

### Functions

#### `normalize_text(text: str) -> str`

Normalize text for comparison (HTML entities, whitespace, quotes).

```python
from docdiff.normalizers import normalize_text

text = normalize_text("Hello&nbsp;World  ")
# Returns: "Hello World"
```

#### `normalize_text_for_comparison(text: str) -> str`

Aggressive normalization for fuzzy matching (lowercase, no punctuation).

```python
from docdiff.normalizers import normalize_text_for_comparison

text = normalize_text_for_comparison("Hello, World!")
# Returns: "hello world"
```

#### `normalize_code(code: str) -> str`

Normalize code while preserving indentation structure.

```python
from docdiff.normalizers import normalize_code

code = normalize_code("  def foo():\n    pass  \n\n")
# Returns: "  def foo():\n    pass"
```

#### `normalize_heading(heading: str) -> str`

Normalize heading text (removes numbering prefix).

```python
from docdiff.normalizers import normalize_heading

heading = normalize_heading("2.1.3 Creating Test Data")
# Returns: "Creating Test Data"
```

#### `generate_heading_key(heading: str) -> str`

Generate normalized key for heading matching.

```python
from docdiff.normalizers import generate_heading_key

key = generate_heading_key("2.1 Creating Test Data")
# Returns: "creating-test-data"
```

#### `similarity_ratio(text1: str, text2: str) -> float`

Calculate similarity ratio between two texts (0.0 to 1.0).

```python
from docdiff.normalizers import similarity_ratio

ratio = similarity_ratio("hello world", "hello there")
# Returns: ~0.6
```

#### `fuzzy_match(text1: str, text2: str, threshold: float = 0.8) -> bool`

Check if two texts are a fuzzy match.

```python
from docdiff.normalizers import fuzzy_match

match = fuzzy_match("Creating Variables", "Create Variables", threshold=0.8)
# Returns: True
```

#### `word_overlap_ratio(text1: str, text2: str) -> float`

Calculate word overlap (Jaccard similarity).

```python
from docdiff.normalizers import word_overlap_ratio

ratio = word_overlap_ratio("hello world", "world hello there")
# Returns: 0.666...
```

#### `normalize_table_cell(cell: str) -> str`

Normalize table cell value (removes Markdown formatting).

#### `normalize_list_item(item: str) -> str`

Normalize list item (removes markers).

---

## Aligners

**Module:** `docdiff.aligners`

Section alignment utilities for matching source and target sections.

### Functions

#### `align_sections(source: list[Section], target: list[Section], config: AlignmentConfig = None) -> AlignmentResult`

Align source sections with target sections using multi-stage matching.

```python
from docdiff.aligners import align_sections

result = align_sections(old_sections, new_sections)
print(f"Matched: {len(result.matched)}")
print(f"Missing: {len(result.source_only)}")
print(f"Extra: {len(result.target_only)}")
```

Matching strategies (in order):
1. Exact number matching (e.g., "2.1.3")
2. Exact key matching (normalized title)
3. Fuzzy title matching (threshold >= 0.8)

#### `find_missing_sections(source: list[Section], target: list[Section], config: AlignmentConfig = None) -> list[Section]`

Find sections in source that don't exist in target.

#### `find_extra_sections(source: list[Section], target: list[Section], config: AlignmentConfig = None) -> list[Section]`

Find sections in target that don't exist in source.

#### `get_alignment_statistics(result: AlignmentResult) -> dict[str, Any]`

Get detailed alignment statistics.

```python
from docdiff.aligners import align_sections, get_alignment_statistics

result = align_sections(old_sections, new_sections)
stats = get_alignment_statistics(result)
print(f"Match rate: {stats['match_rate']:.1f}%")
```

#### `suggest_matches(unmatched_source: list[Section], unmatched_target: list[Section], config: AlignmentConfig = None) -> list[tuple[Section, Section, float]]`

Suggest potential matches for unmatched sections (below normal threshold).

### Classes

#### `AlignmentConfig`

Configuration for section alignment.

```python
@dataclass
class AlignmentConfig:
    fuzzy_threshold: float = 0.8
    number_weight: float = 0.3
    key_weight: float = 0.4
    title_weight: float = 0.3
    allow_reordering: bool = True
```

---

## Comparators

**Module:** `docdiff.comparators`

Content comparison for different block types.

### Functions

#### `compare_paragraphs(source: str, target: str, threshold: float = 0.9) -> tuple[bool, float]`

Compare two paragraph texts.

```python
from docdiff.comparators import compare_paragraphs

is_match, similarity = compare_paragraphs(old_text, new_text)
if not is_match:
    print(f"Paragraphs differ: {similarity:.1%} similar")
```

#### `compare_code_blocks(source: str, target: str, strict: bool = False) -> tuple[bool, list[str]]`

Compare two code blocks.

```python
from docdiff.comparators import compare_code_blocks

is_match, diff_lines = compare_code_blocks(old_code, new_code)
if not is_match:
    print("Code differs:")
    for line in diff_lines:
        print(line)
```

#### `compare_tables(source_data: list[list[str]], target_data: list[list[str]]) -> dict[str, Any]`

Compare two tables.

```python
from docdiff.comparators import compare_tables

result = compare_tables(old_table, new_table)
if not result['matches']:
    print(f"Row difference: {result['row_diff']}")
    for cell_diff in result['cell_diffs']:
        print(f"  [{cell_diff['row']},{cell_diff['col']}]: "
              f"'{cell_diff['source']}' -> '{cell_diff['target']}'")
```

#### `compare_lists(source_items: list[str], target_items: list[str]) -> dict[str, Any]`

Compare two lists.

```python
from docdiff.comparators import compare_lists

result = compare_lists(old_items, new_items)
print(f"Missing: {result['missing']}")
print(f"Extra: {result['extra']}")
print(f"Order preserved: {result['order_preserved']}")
```

### Classes

#### `BlockComparator`

Compare content blocks between source and target.

```python
from docdiff.comparators import BlockComparator

comparator = BlockComparator(
    text_threshold=0.9,
    code_threshold=0.95,
    strict_mode=False
)

findings = comparator.compare_blocks(source_block, target_block, section)
for finding in findings:
    print(finding.message)
```

**Constructor:**

```python
BlockComparator(
    text_threshold: float = 0.9,    # Min similarity for text
    code_threshold: float = 0.95,   # Min similarity for code
    strict_mode: bool = False       # Require exact code matches
)
```

**Methods:**

- `compare_blocks(source: Block, target: Block, section: Section = None) -> list[Finding]`

---

## Validators

**Module:** `docdiff.validators`

Link and resource validators.

### Functions

#### `extract_all_links(sections: list[Section]) -> list[LinkInfo]`

Extract all links from sections.

#### `validate_internal_links(links: list[LinkInfo], anchor_map: dict) -> list[Finding]`

Validate internal links against available anchors.

#### `check_anchor_drift(old_sections: list[Section], new_sections: list[Section]) -> list[Finding]`

Check for anchor drift between old and new sections.

#### `build_anchor_map(sections: list[Section]) -> dict[str, Section]`

Build a map of anchors to their sections.

#### `extract_all_images(sections: list[Section]) -> list[ImageInfo]`

Extract all images from sections.

#### `validate_images(images: list[ImageInfo], base_dir: str) -> list[Finding]`

Validate that image files exist.

#### `compare_image_sets(old_images: list[ImageInfo], new_images: list[ImageInfo]) -> list[Finding]`

Compare image sets between old and new documentation.

### Classes

#### `LinkValidator`

Validate links in documents.

```python
from docdiff.validators import LinkValidator
from pathlib import Path

validator = LinkValidator(base_path=Path("docs/"))

# Extract links
links = validator.extract_links(content)

# Validate a single link
is_valid, reason = validator.validate_link("../images/logo.png")

# Validate internal anchor links
findings = validator.validate_internal_links(sections, all_section_keys)
```

#### `ImageValidator`

Validate images in documents.

```python
from docdiff.validators import ImageValidator
from pathlib import Path

validator = ImageValidator(base_path=Path("docs/"))

# Extract images
images = validator.extract_images(content)

# Validate a single image
is_valid, reason = validator.validate_image("images/screenshot.png")

# Validate all images in sections
findings = validator.validate_images_in_sections(sections)
```

---

## Reporters

**Module:** `docdiff.reporters`

Report generation for comparison results.

### Functions

#### `generate_markdown_report(result: ComparisonResult) -> str`

Generate a comprehensive Markdown report.

```python
from docdiff.reporters import generate_markdown_report

report = generate_markdown_report(comparison_result)
with open("report.md", "w") as f:
    f.write(report)
```

#### `generate_json_report(result: ComparisonResult) -> str`

Generate a JSON report for machine processing.

```python
from docdiff.reporters import generate_json_report
import json

report_json = generate_json_report(comparison_result)
data = json.loads(report_json)
print(f"P0 findings: {data['findings_by_priority']['P0']['count']}")
```

#### `format_finding(finding: Finding) -> str`

Format a single finding as Markdown.

```python
from docdiff.reporters import format_finding

markdown = format_finding(finding)
print(markdown)
```

#### `format_diff(old_text: str, new_text: str, context: int = 3, max_lines: int = 50) -> str`

Format a unified diff as a Markdown code block.

```python
from docdiff.reporters import format_diff

diff = format_diff(old_content, new_content)
print(diff)
```

#### `generate_summary_stats(result: ComparisonResult) -> dict[str, Any]`

Compute aggregate statistics from comparison results.

```python
from docdiff.reporters import generate_summary_stats

stats = generate_summary_stats(result)
print(f"Match rate: {stats['match_percentage']:.1f}%")
print(f"Total findings: {stats['total_findings']}")
print(f"P0 findings: {stats['by_priority']['P0']['count']}")
```

---

## CLI

**Module:** `docdiff.cli`

Command-line interface for docdiff.

### Functions

#### `main(argv: list[str] = None) -> int`

Main entry point for the CLI.

```python
from docdiff.cli import main

# Run with custom arguments
exit_code = main(["--old-html", "old.html", "--new-md-dir", "docs/"])
```

#### `create_parser() -> argparse.ArgumentParser`

Create and configure the argument parser.

```python
from docdiff.cli import create_parser

parser = create_parser()
args = parser.parse_args(["--old-html", "old.html", "--new-md-dir", "docs/"])
```

#### `run_comparison(args: argparse.Namespace) -> ComparisonResult`

Run the documentation comparison.

```python
from docdiff.cli import create_parser, run_comparison

parser = create_parser()
args = parser.parse_args(["--old-html", "old.html", "--new-md-dir", "docs/"])
result = run_comparison(args)
```

#### `generate_report(result: ComparisonResult, format: str) -> str`

Generate a report from comparison results.

```python
from docdiff.cli import generate_report

markdown_report = generate_report(result, "markdown")
json_report = generate_report(result, "json")
```

#### `setup_logging(verbose: bool = False, quiet: bool = False) -> None`

Configure logging based on verbosity settings.

```python
from docdiff.cli import setup_logging

setup_logging(verbose=True)  # DEBUG level
setup_logging(quiet=True)    # ERROR level only
```
