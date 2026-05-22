# Contributing to DocDiff

Thank you for your interest in contributing to DocDiff! This guide will help you get started.

## Table of Contents

- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Code Style](#code-style)
- [Testing](#testing)
- [Making Changes](#making-changes)
- [Pull Request Process](#pull-request-process)

## Development Setup

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) package manager

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/robotframework/robotframework.git
   cd robotframework/doc/userguide-mkdocs/docdiff
   ```

2. Install dependencies with uv:
   ```bash
   uv sync --dev
   ```

3. Verify installation:
   ```bash
   uv run python -m docdiff --version
   ```

## Project Structure

```
docdiff/
├── docdiff/                 # Main package
│   ├── __init__.py          # Package metadata
│   ├── __main__.py          # Entry point
│   ├── cli.py               # Command-line interface
│   ├── models.py            # Core data models
│   ├── extractors/          # Document parsing
│   │   ├── html_extractor.py
│   │   └── md_extractor.py
│   ├── normalizers/         # Text normalization
│   ├── aligners/            # Section matching
│   ├── comparators/         # Content comparison
│   ├── validators/          # Link/image validation
│   └── reporters/           # Report generation
├── tests/                   # Test suite
├── docs/                    # Documentation
├── reports/                 # Output reports
├── pyproject.toml           # Project configuration
└── uv.lock                  # Dependency lock file
```

## Code Style

### Python Style Guide

DocDiff follows PEP 8 with these conventions:

1. **Line length**: 88 characters (Black compatible)
2. **Imports**: Standard library first, then local imports
3. **Type hints**: Required for all public functions
4. **Docstrings**: Google style for all public APIs

### Example

```python
"""Module description.

More detailed description if needed.
"""

import re
from dataclasses import dataclass
from typing import Any

from docdiff.models import Section


@dataclass
class MyConfig:
    """Configuration for my feature.

    Attributes:
        threshold: Minimum value (0.0 to 1.0).
        strict: If True, require exact matches.
    """
    threshold: float = 0.8
    strict: bool = False


def process_section(
    section: Section,
    config: MyConfig | None = None,
) -> list[str]:
    """Process a section and return results.

    Args:
        section: The section to process.
        config: Optional configuration (uses defaults if None).

    Returns:
        List of processed strings.

    Raises:
        ValueError: If section is invalid.
    """
    if config is None:
        config = MyConfig()

    # Implementation...
    return []
```

### Pure stdlib Requirement

DocDiff uses only Python standard library. **Do not add external dependencies.**

Allowed modules include:
- `dataclasses`, `typing`, `enum`
- `html.parser`, `re`, `difflib`
- `pathlib`, `os`, `json`
- `argparse`, `logging`
- `collections`, `datetime`

## Testing

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=docdiff --cov-report=html

# Run specific test file
uv run pytest tests/test_models.py

# Run specific test
uv run pytest tests/test_models.py::test_section_creation -v
```

### Test Structure

```python
"""Tests for my_module."""

import pytest

from docdiff.my_module import my_function


class TestMyFunction:
    """Tests for my_function."""

    def test_basic_case(self):
        """Test basic functionality."""
        result = my_function("input")
        assert result == "expected"

    def test_edge_case_empty(self):
        """Test with empty input."""
        result = my_function("")
        assert result == ""

    def test_error_case(self):
        """Test that errors are raised correctly."""
        with pytest.raises(ValueError, match="invalid input"):
            my_function(None)


@pytest.fixture
def sample_section():
    """Create a sample section for testing."""
    return Section(
        title="Test Section",
        key="test-section",
        level=1,
    )
```

### Test Coverage

- Aim for 80%+ coverage on new code
- All edge cases should be tested
- Include both positive and negative tests

## Making Changes

### 1. Create a Branch

```bash
git checkout -b feature/my-feature
# or
git checkout -b fix/my-bugfix
```

### 2. Make Your Changes

- Follow the code style guidelines
- Add tests for new functionality
- Update documentation if needed

### 3. Run Tests

```bash
# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=docdiff

# Check types (optional, if mypy is available)
uv run mypy docdiff/
```

### 4. Commit Your Changes

Use clear commit messages:

```bash
git commit -m "Add fuzzy matching for table cells"
git commit -m "Fix anchor extraction from nested headings"
git commit -m "Update docs for new --filter option"
```

## Pull Request Process

### Before Submitting

1. **Tests pass**: All tests should pass
2. **Coverage maintained**: New code should have tests
3. **Documentation updated**: Update docs for new features
4. **No dependencies added**: Stdlib only

### PR Description Template

```markdown
## Description

Brief description of the changes.

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Changes Made

- Change 1
- Change 2

## Testing

Describe how you tested the changes.

## Checklist

- [ ] Tests pass locally
- [ ] New tests added for new functionality
- [ ] Documentation updated
- [ ] No new dependencies added
```

### Review Process

1. Create pull request with description
2. Address reviewer feedback
3. Ensure CI passes
4. Maintainer merges

## Adding New Features

### Adding a New Block Type

1. Add to `BlockType` enum in `models.py`:
   ```python
   class BlockType(Enum):
       # ... existing types
       NEW_TYPE = "new_type"
   ```

2. Add extraction in appropriate extractor:
   ```python
   # In html_extractor.py or md_extractor.py
   def _extract_new_type(self, content: str) -> Block:
       # Parse and create block
       return Block(
           block_type=BlockType.NEW_TYPE,
           content=parsed_content,
           metadata={'key': 'value'},
       )
   ```

3. Add comparison in `BlockComparator`:
   ```python
   def _compare_new_type(
       self,
       source: Block,
       target: Block,
       section: Section | None,
   ) -> list[Finding]:
       # Comparison logic
       return findings
   ```

4. Add tests for extraction and comparison

### Adding a New Validator

1. Create validator class:
   ```python
   # validators/new_validator.py
   class NewValidator:
       def validate(self, content: str) -> list[Finding]:
           findings = []
           # Validation logic
           return findings
   ```

2. Export from `validators/__init__.py`:
   ```python
   from .new_validator import NewValidator
   __all__ = [..., 'NewValidator']
   ```

3. Integrate in `cli.py`:
   ```python
   # In run_comparison()
   new_findings = validators.NewValidator().validate(content)
   all_findings.extend(new_findings)
   ```

4. Add tests

### Adding a New Report Format

1. Add generation function:
   ```python
   # reporters/new_format.py
   def generate_new_format_report(result: ComparisonResult) -> str:
       # Format report
       return formatted_output
   ```

2. Export from `reporters/__init__.py`

3. Add CLI option:
   ```python
   # In cli.py create_parser()
   output.add_argument(
       "--format",
       choices=["markdown", "json", "new_format"],
       # ...
   )
   ```

4. Update `generate_report()` function

## Getting Help

- Open an issue for bugs or feature requests
- Check existing issues and PRs before starting work
- Ask questions in issues or discussions

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help newcomers get started
