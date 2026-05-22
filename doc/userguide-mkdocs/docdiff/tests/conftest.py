"""Pytest fixtures for docdiff tests."""

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


# ============================================================================
# Sample HTML Content Fixtures
# ============================================================================

@pytest.fixture
def sample_html_basic():
    """Basic HTML document with headings and paragraphs."""
    return """
    <html>
    <body>
        <h1>Introduction</h1>
        <p>This is the introduction paragraph.</p>
        
        <h2>Getting Started</h2>
        <p>Here's how to get started with the tool.</p>
        
        <h3>Installation</h3>
        <p>Install using pip:</p>
        <pre><code class="language-bash">pip install docdiff</code></pre>
    </body>
    </html>
    """


@pytest.fixture
def sample_html_with_table():
    """HTML document with a table."""
    return """
    <html>
    <body>
        <h1>Data</h1>
        <table>
            <tr><th>Name</th><th>Value</th></tr>
            <tr><td>Item 1</td><td>100</td></tr>
            <tr><td>Item 2</td><td>200</td></tr>
        </table>
    </body>
    </html>
    """


@pytest.fixture
def sample_html_with_lists():
    """HTML document with lists."""
    return """
    <html>
    <body>
        <h1>Features</h1>
        <ul>
            <li>Feature one</li>
            <li>Feature two</li>
            <li>Feature three</li>
        </ul>
        <ol>
            <li>Step one</li>
            <li>Step two</li>
        </ol>
    </body>
    </html>
    """


@pytest.fixture
def sample_html_with_links():
    """HTML document with links and images."""
    return """
    <html>
    <body>
        <h1>Resources</h1>
        <p>Visit <a href="https://example.com">our website</a> for more info.</p>
        <p>See the <a href="#installation">installation section</a>.</p>
        <img src="images/logo.png" alt="Company Logo">
    </body>
    </html>
    """


# ============================================================================
# Sample Markdown Content Fixtures
# ============================================================================

@pytest.fixture
def sample_markdown_basic():
    """Basic Markdown document."""
    return """# Introduction

This is the introduction paragraph.

## Getting Started

Here's how to get started with the tool.

### Installation

Install using pip:

```bash
pip install docdiff
```
"""


@pytest.fixture
def sample_markdown_with_table():
    """Markdown document with a table."""
    return """# Data

| Name | Value |
|------|-------|
| Item 1 | 100 |
| Item 2 | 200 |
"""


@pytest.fixture
def sample_markdown_with_lists():
    """Markdown document with lists."""
    return """# Features

- Feature one
- Feature two
- Feature three

1. Step one
2. Step two
"""


@pytest.fixture
def sample_markdown_with_links():
    """Markdown document with links and images."""
    return """# Resources

Visit [our website](https://example.com) for more info.

See the [installation section](#installation).

![Company Logo](images/logo.png)
"""


@pytest.fixture
def sample_markdown_complex():
    """Complex Markdown document with multiple elements."""
    return """# Robot Framework User Guide

Welcome to the Robot Framework User Guide.

## 2.1 Introduction

Robot Framework is a generic open source automation framework.

### 2.1.1 Why Robot Framework

Robot Framework provides:

- Easy-to-use tabular test data syntax
- Support for keyword-driven testing
- Rich ecosystem of libraries

### 2.1.2 High-level architecture

```python
from robot import run

run('tests.robot')
```

| Component | Description |
|-----------|-------------|
| Core | Test execution engine |
| Libraries | Functionality providers |

## 2.2 Installation

See [installation instructions](#installation).
"""


# ============================================================================
# Sample Section Fixtures
# ============================================================================

@pytest.fixture
def sample_section():
    """A basic Section instance."""
    return Section(
        number="2.1",
        title="Getting Started",
        level=2,
        key="getting-started",
        line_number=10,
    )


@pytest.fixture
def sample_section_with_blocks():
    """A Section with blocks."""
    section = Section(
        number="2.1",
        title="Getting Started",
        level=2,
        key="getting-started",
        line_number=10,
    )
    section.blocks = [
        Block(
            block_type=BlockType.PARAGRAPH,
            content="This section covers getting started.",
            line_number=12,
        ),
        Block(
            block_type=BlockType.CODE,
            content="pip install robot",
            metadata={"language": "bash"},
            line_number=14,
        ),
    ]
    return section


@pytest.fixture
def sample_section_hierarchy():
    """A hierarchy of sections."""
    root = Section(
        number="2",
        title="User Guide",
        level=1,
        key="user-guide",
    )
    child1 = Section(
        number="2.1",
        title="Introduction",
        level=2,
        key="introduction",
        parent=root,
    )
    child2 = Section(
        number="2.2",
        title="Installation",
        level=2,
        key="installation",
        parent=root,
    )
    grandchild = Section(
        number="2.1.1",
        title="Overview",
        level=3,
        key="overview",
        parent=child1,
    )
    
    root.subsections = [child1, child2]
    child1.subsections = [grandchild]
    
    return {
        "root": root,
        "child1": child1,
        "child2": child2,
        "grandchild": grandchild,
    }


# ============================================================================
# Sample Block Fixtures
# ============================================================================

@pytest.fixture
def sample_paragraph_block():
    """A paragraph block."""
    return Block(
        block_type=BlockType.PARAGRAPH,
        content="This is a sample paragraph with some text content.",
        line_number=5,
    )


@pytest.fixture
def sample_code_block():
    """A code block."""
    return Block(
        block_type=BlockType.CODE,
        content="def hello():\n    print('Hello, World!')",
        metadata={"language": "python"},
        line_number=10,
    )


@pytest.fixture
def sample_table_block():
    """A table block."""
    return Block(
        block_type=BlockType.TABLE,
        content="Name | Value\nItem 1 | 100\nItem 2 | 200",
        metadata={
            "rows": 3,
            "data": [
                ["Name", "Value"],
                ["Item 1", "100"],
                ["Item 2", "200"],
            ],
        },
        line_number=20,
    )


@pytest.fixture
def sample_list_block():
    """A list block."""
    return Block(
        block_type=BlockType.LIST,
        content="First item\nSecond item\nThird item",
        metadata={
            "type": "ul",
            "items": ["First item", "Second item", "Third item"],
        },
        line_number=30,
    )


# ============================================================================
# Sample Finding Fixtures
# ============================================================================

@pytest.fixture
def sample_finding():
    """A basic finding."""
    return Finding(
        category="content_difference",
        severity=Severity.WARNING,
        message="Paragraph content differs",
        source_location="Section 2.1 - line 10",
        target_location="Section 2.1 - line 12",
        source_content="Original text here",
        target_content="Modified text here",
        suggestion="Review the changes",
    )


@pytest.fixture
def sample_findings_list():
    """A list of findings with different severities."""
    return [
        Finding(
            category="missing_section",
            severity=Severity.ERROR,
            message="Section 2.3 is missing from target",
        ),
        Finding(
            category="content_difference",
            severity=Severity.WARNING,
            message="Minor text difference detected",
        ),
        Finding(
            category="formatting_change",
            severity=Severity.INFO,
            message="Formatting was updated",
        ),
        Finding(
            category="broken_link",
            severity=Severity.CRITICAL,
            message="Link to external resource is broken",
        ),
    ]


# ============================================================================
# Sample Alignment Fixtures
# ============================================================================

@pytest.fixture
def sample_alignment_result():
    """A sample alignment result."""
    source1 = Section(number="1", title="Introduction", level=1, key="introduction")
    source2 = Section(number="2", title="Getting Started", level=1, key="getting-started")
    source3 = Section(number="3", title="Advanced", level=1, key="advanced")
    
    target1 = Section(number="1", title="Introduction", level=1, key="introduction")
    target2 = Section(number="2", title="Quick Start", level=1, key="quick-start")
    target3 = Section(number="4", title="FAQ", level=1, key="faq")
    
    return AlignmentResult(
        matched=[(source1, target1)],
        source_only=[source2, source3],
        target_only=[target2, target3],
        match_stats={
            "exact_number": 1,
            "exact_key": 0,
            "fuzzy": 0,
            "unmatched_source": 2,
            "unmatched_target": 2,
        },
    )


# ============================================================================
# Sample Comparison Result Fixtures
# ============================================================================

@pytest.fixture
def sample_comparison_result(sample_findings_list, sample_alignment_result):
    """A complete comparison result."""
    return ComparisonResult(
        source_file="source.html",
        target_file="target.md",
        findings=sample_findings_list,
        alignment=sample_alignment_result,
        metadata={"comparison_time": 1.5},
    )
