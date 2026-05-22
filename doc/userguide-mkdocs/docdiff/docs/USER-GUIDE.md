# DocDiff User Guide

## Overview

DocDiff is a pure-Python documentation comparison tool for auditing RST to Markdown migrations. It compares old HTML documentation (generated from RST) with new Markdown documentation, identifying content drift, missing sections, broken links, and other migration issues.

## Features

- **Zero dependencies**: Uses only Python standard library (3.10+)
- **Section alignment**: Multi-stage matching algorithm using exact numbers, keys, and fuzzy matching
- **Content comparison**: Weighted similarity scoring for paragraphs, code, tables, lists, and admonitions
- **Link validation**: Internal/external link checking with anchor drift detection
- **Image validation**: Verifies image existence and alt text compliance
- **Prioritized findings**: P0 (critical), P1 (important), P2 (minor) classification
- **Multiple output formats**: Markdown reports and JSON for machine processing

## Installation

DocDiff uses `uv` for dependency management:

```bash
cd docdiff
uv sync
```

For development with test dependencies:

```bash
uv sync --dev
```

## Quick Start

### Basic Comparison

Compare old HTML documentation with a new Markdown directory:

```bash
uv run python -m docdiff --old-html userguide.html --new-md-dir docs/
```

### JSON Output

Generate a machine-readable JSON report:

```bash
uv run python -m docdiff --old-html userguide.html --new-md-dir docs/ \
    --format json --out report.json
```

### Strict Mode (CI/CD)

Fail on P0/P1 findings (useful for CI pipelines):

```bash
uv run python -m docdiff --old-html userguide.html --new-md-dir docs/ --strict
```

### Filter Sections

Compare only specific sections using regex:

```bash
# Compare only sections starting with "2."
uv run python -m docdiff --old-html userguide.html --new-md-dir docs/ \
    --section "^2\."

# Compare only "Installation" sections
uv run python -m docdiff --old-html userguide.html --new-md-dir docs/ \
    --section "installation"
```

## Command Line Options

### Required Arguments
| Option | Description |
|--------|-------------|
| `--old-html FILE` | Path to old HTML documentation file |
| `--new-md-dir DIR` | Path to new Markdown documentation directory |

### Output Options
| Option | Description |
|--------|-------------|
| `--out FILE`, `-o FILE` | Output report file (default: stdout) |
| `--format FORMAT`, `-f FORMAT` | Output format: `markdown` or `json` (default: markdown) |

### URL Options
| Option | Description |
|--------|-------------|
| `--base-url-old URL` | Base URL for old documentation (for link validation) |
| `--base-url-new URL` | Base URL for new documentation (for link validation) |

### Filtering Options
| Option | Description |
|--------|-------------|
| `--section PATTERN` | Only compare sections matching regex pattern |
| `--min-similarity N` | Minimum similarity threshold 0-1 (default: 0.90) |

### Behavior Options
| Option | Description |
|--------|-------------|
| `--strict` | Exit with code 2 on P0/P1 findings |
| `--verbose`, `-v` | Verbose output (DEBUG level logging) |
| `--quiet`, `-q` | Quiet mode (ERROR level logging only) |
| `--version` | Show version number |

## Understanding the Report

### Report Structure

The Markdown report includes:

1. **Executive Summary**: High-level statistics
2. **Findings Summary**: Count by priority
3. **Critical Issues (P0)**: Must fix before release
4. **Important Issues (P1)**: Should fix soon
5. **Minor Issues (P2)**: Nice to fix
6. **Section-by-Section Analysis**: Detailed comparison
7. **Missing Sections**: Old sections not found in new docs
8. **Extra Sections**: New sections not in old docs
9. **Appendix: Detailed Diffs**: Content differences

### Finding Priorities
| Priority | Severity | Description | Exit Code |
|----------|----------|-------------|-----------|
| **P0** | Critical/Error | Missing sections, broken code, semantic drift | 2 |
| **P1** | Warning | Content differences, table changes, link issues | 2 |
| **P2** | Info | Added content, minor formatting changes | 1 |

### Finding Categories
| Category | Description |
|----------|-------------|
| `content_missing` | Section completely missing from new documentation |
| `content_changed` | Significant content differences detected |
| `content_added` | New section not in original documentation |
| `structure_changed` | Document structure differs |
| `formatting_changed` | Formatting differences (usually cosmetic) |
| `link_broken` | Internal or external link not working |
| `link_changed` | Link target has changed |
| `code_block_changed` | Code example differs from original |
| `table_changed` | Table content or structure differs |
| `image_missing` | Image file not found |
| `anchor_missing` | Internal anchor target not found |
| `heading_level_changed` | Heading hierarchy changed |
| `semantic_drift` | Meaning has changed significantly |

### Similarity Scoring

Content similarity uses weighted scoring:
| Block Type | Weight |
|------------|--------|
| Paragraphs | 35% |
| Code blocks | 20% |
| Tables | 15% |
| Lists | 15% |
| Admonitions | 10% |
| Images/Links | 5% |

## Common Use Cases

### Pre-Migration Planning

Analyze the old documentation structure:

```bash
uv run python -m docdiff --old-html old-docs.html --new-md-dir empty-dir/ \
    --format json --out structure.json
```

### Continuous Integration

Add to your CI pipeline:

```bash
#!/bin/bash
set -e

# Run comparison in strict mode
uv run python -m docdiff \
    --old-html reference/userguide.html \
    --new-md-dir docs/ \
    --strict \
    --out reports/comparison.md

echo "Documentation comparison passed!"
```

### Incremental Migration

Focus on one chapter at a time:

```bash
# Chapter 2: Creating Test Data
uv run python -m docdiff --old-html userguide.html --new-md-dir docs/ \
    --section "^2\." --out chapter2-review.md

# Chapter 3: Execution
uv run python -m docdiff --old-html userguide.html --new-md-dir docs/ \
    --section "^3\." --out chapter3-review.md
```

### Link Audit

Focus on link validation with verbose output:

```bash
uv run python -m docdiff --old-html userguide.html --new-md-dir docs/ \
    --verbose 2>&1 | grep -i link
```

### Generate Report for Review

Create a detailed report for documentation review:

```bash
uv run python -m docdiff --old-html userguide.html --new-md-dir docs/ \
    --min-similarity 0.85 \
    --out reports/migration-audit.md

# Open in browser (if you have a Markdown viewer)
open reports/migration-audit.md
```

## Exit Codes
| Code | Meaning | When |
|------|---------|------|
| 0 | Success | No P0/P1 findings |
| 1 | Warnings | P2 findings only |
| 2 | Errors | P0/P1 findings, or `--strict` with any findings |

## Tips and Best Practices

### 1. Start with a Baseline

Run the tool on your current state to establish a baseline:

```bash
uv run python -m docdiff --old-html userguide.html --new-md-dir docs/ \
    --format json --out baseline.json
```

### 2. Address P0 Issues First

Critical issues indicate missing or broken content:

```bash
uv run python -m docdiff --old-html userguide.html --new-md-dir docs/ \
    --format json --out report.json

# Extract P0 issues
jq '.findings_by_priority.P0' report.json
```

### 3. Use Section Filters for Large Documentation

For large documentation sets, process in chunks:

```bash
for i in {1..9}; do
    uv run python -m docdiff --old-html userguide.html --new-md-dir docs/ \
        --section "^$i\." --out "chapter${i}.md"
done
```

### 4. Adjust Similarity Threshold

Lower the threshold if too many false positives:

```bash
# More lenient matching
uv run python -m docdiff --old-html userguide.html --new-md-dir docs/ \
    --min-similarity 0.80
```

### 5. Review Extra Sections

Extra sections might indicate:
- New content added (good)
- Duplicated content (review needed)
- Renamed sections (check mapping)

## Troubleshooting

### "HTML file not found"

Ensure the path to the HTML file is correct:

```bash
ls -la path/to/userguide.html
```

### "Markdown directory not found"

Ensure the directory exists and contains `.md` files:

```bash
ls -la docs/*.md
```

### "No sections extracted"

The HTML might not have proper heading structure. Check:

```bash
grep -o '<h[1-6][^>]*>' userguide.html | head -20
```

### High Number of P0 Findings

This usually indicates:
1. Incomplete migration (sections truly missing)
2. Different document structure (headings renamed)
3. Wrong comparison targets

Try with verbose logging:

```bash
uv run python -m docdiff --old-html userguide.html --new-md-dir docs/ --verbose
```

## Integration with MkDocs

DocDiff works well with MkDocs documentation:

1. Build the old RST documentation to HTML
2. Run DocDiff against the new MkDocs source
3. Review the comparison report
4. Address findings before publishing

```bash
# Build MkDocs (optional, for rendered comparison)
mkdocs build

# Compare source Markdown against old HTML
uv run python -m docdiff \
    --old-html old-sphinx-build/userguide.html \
    --new-md-dir docs/ \
    --out migration-report.md
```
