# Robot Framework User Guide: Conversion & Validation Package

Documentation for the reusable toolchain that converts the Robot Framework User Guide from reStructuredText to Material for MkDocs.

## Overview

This package provides a **fully automated, reproducible pipeline** that takes the Robot Framework User Guide RST source and produces a clean MkDocs Markdown site. Every fix and transformation is captured in scripts and data files so the conversion can be re-run at any time when the RST source changes.

```
doc/userguide/src/ (RST)          doc/userguide-mkdocs/docs/ (Markdown)
  37 files, 23,139 lines    -->     42 files, 21,665 lines
|
                      scripts/pipeline.py
                      (17 fix scripts, 9s)
```

### Design Principles

- **Source of truth is RST** -- The Markdown files are generated output. Any issue is fixed by improving a script, not editing the output.
- **Data-driven corrections** -- Link mappings, anchor corrections, and reference targets live in JSON data files. Adding a fix means editing JSON, not code.
- **Idempotent scripts** -- Every script can run multiple times with the same result. The full pipeline can be run from a clean state or on already-processed files.
- **Automated validation** -- A 9-check validation suite verifies the output quality and catches regressions.

---

## Quick Start

```bash
cd doc/userguide-mkdocs

# Install dependencies
uv sync

# Run the full fix pipeline (from current converted state)
uv run python scripts/pipeline.py --fix-only

# Validate the result
uv run python scripts/validate.py

# Quick validation (no MkDocs build, sub-second)
uv run python scripts/validate.py --quick

# Preview the site
uv run mkdocs serve
```

---

## Package Structure

```
doc/userguide-mkdocs/
  mkdocs.yml                  # MkDocs site configuration
  pyproject.toml              # Python dependencies
  docs/                       # Generated Markdown output (42 pages)
  scripts/                    # Conversion & validation scripts
    pipeline.py               # Master orchestrator
    validate.py               # 9-check validation suite
    convert.py                # RST-to-Markdown converter (main)
    convert_rst_to_md.py      # Alternative line-by-line converter
    convert_rst.py            # RST conversion utilities
    fix_*.py                  # 14 post-processing fix scripts
    add_legacy_anchors.py     # Legacy URL anchor injection
    reference_map.json        # Data: bare ref targets, filename corrections
    anchor_corrections.json   # Data: anchor link corrections
    anchor_map.json           # Data: legacy anchor mappings
  docdiff/                    # Documentation comparison tool
    docdiff/                  # Package source (18 modules, 8,147 LOC)
    tests/                    # Test suite (344 tests, 4,921 LOC)
    data/                     # Reference HTML for comparison
  .github/workflows/
    docs.yml                  # CI/CD: build-check, docdiff, deploy
```

---

## Pipeline

### `scripts/pipeline.py` -- Master Orchestrator

Runs all conversion and fix steps in the correct order. Supports multiple modes:
| Mode | Command | Description |
|------|---------|-------------|
| Fix only | `pipeline.py --fix-only` | Re-run all fix scripts on existing MD files (9s) |
| Validate only | `pipeline.py --validate-only` | Build MkDocs and report quality (12s) |
| Full pipeline | `pipeline.py` | Clean + convert + fix + validate |
| Dry run | `pipeline.py --dry-run` | Preview what would happen |
| Skip convert | `pipeline.py --skip-convert` | Skip RST conversion, run fixes + validate |

### Pipeline Stages

```
[1/5] CLEAN     Remove old generated .md files
[2/5] CONVERT   RST to raw Markdown via convert.py
[3/5] FIX       Apply 17 post-processing scripts in order
[4/5] ASSETS    Copy images from RST source directories
[5/5] VALIDATE  MkDocs build (strict + non-strict)
```

### Fix Script Execution Order

The scripts run in dependency order. Some run twice to handle cross-dependencies:
| # | Script | Purpose |
|---|--------|---------|
| 1 | `fix_admonitions.py` | Restore truncated admonitions from RST source |
| 2 | `fix_rst_syntax.py` | Convert RST labels, link definitions, roles |
| 3 | `fix_tables.py` | Fix Markdown table formatting |
| 4 | `fix_links.py` | Fix API references and internal cross-references |
| 5 | `fix_cross_file_links.py` | Resolve cross-file anchor references |
| 6 | `fix_anchors.py` | Validate and fix anchor links |
| 7 | `fix_anonymous_refs.py` | Fix RST `\`text\`__` anonymous references |
| 8 | `fix_file_references.py` | Fix wrong filenames and path depth |
| 9 | `fix_missing_anchors.py` | Inject `<a id>` tags from RST label targets |
| 10 | `fix_cross_page_anchors.py` | Rewrite `#anchor` to `page.md#anchor` |
| 11 | `fix_missing_anchors.py` | Second pass after cross-page resolution |
| 12 | `fix_cross_page_anchors.py` | Final cross-page anchor pass |
| 13 | `fix_anchor_corrections.py` | Apply data-driven anchor corrections |
| 14 | `fix_bare_refs.py` | Convert `Word_` RST references to links |
| 15 | `fix_code_blocks.py` | Fix code block syntax and headings-in-blocks |
| 16 | `fix_bare_refs.py` | Final bare ref cleanup pass |
| 17 | `add_legacy_anchors.py` | Add legacy URL anchor compatibility |

---

## Conversion Scripts

### `scripts/convert.py` (1,018 LOC)

The primary RST-to-Markdown converter. A class-based converter (`RstToMarkdownConverter`) that handles:

- **Custom RST roles**: `:setting:`, `:option:`, `:name:`, `:file:`, `:codesc:` to Markdown equivalents
- **Admonitions**: `.. note::`, `.. warning::` etc. to `!!! note` MkDocs syntax
- **Code blocks**: `.. sourcecode:: python` to ` ```python ` fenced blocks
- **Cross-references**: `\`text\`_` to `[text](#slug)` or `[text](url)`
- **Link targets**: `.. _label:` extraction and resolution
- **Anonymous references**: `\`text\`__` paired with `__ url` targets
- **Inline code**: ` ``code`` ` to `` `code` ``
- **Tables**: Grid and simple RST tables

### `scripts/convert_rst_to_md.py` (430 LOC)

Alternative line-by-line converter with explicit file/section mapping tables. Contains:

- `SECTIONS` -- Maps RST directory names to MkDocs paths
- `FILE_ORDER` -- Defines file ordering within each section
- `rst_to_md()` -- Line-by-line conversion function

### `scripts/convert_rst.py` (299 LOC)

Utility module with RST-specific conversion helpers.

---

## Post-Processing Fix Scripts

Each script is **standalone** (can run independently) and **idempotent** (safe to run multiple times).

### Content Fixes
| Script | LOC | What it Fixes |
|--------|-----|---------------|
| `fix_rst_syntax.py` | 467 | RST labels to `<a id>`, link definitions, anonymous links, `.. raw::`, `.. table::`, `.. list-table:`, RST role remnants (multi-line aware) |
| `fix_admonitions.py` | 448 | Truncated admonitions by comparing with RST source. Restores content that was cut during conversion |
| `fix_code_blocks.py` | 295 | Empty code blocks with orphaned code, headings inside code blocks (CommonMark-aware fence tracking) |
| `fix_tables.py` | 264 | Malformed pipe tables, header separators, cell alignment |
| `fix_links.py` | 193 | API references (`running.TestSuite_`), underscore-suffixed refs, anonymous link targets, malformed backtick links |
| `fix_bullets_simple.py` | 40 | Bullet list formatting normalization |
| `fix_bullets_spacing.py` | 28 | Bullet list inter-item spacing |
| `fix_listener_tables.py` | 122 | Listener interface method tables |

### Link & Anchor Fixes
| Script | LOC | What it Fixes |
|--------|-----|---------------|
| `fix_cross_file_links.py` | 190 | `#anchor` links that point to headings on other pages. Builds global heading map and rewrites to `page.md#anchor` |
| `fix_anchors.py` | 171 | Anchors with spaces, broken GitHub issue references |
| `fix_bare_refs.py` | 264 | Bare `Word_` RST references (e.g., `Libdoc_`, `Process_`, `Enum_`) to `[Word](url)` using `reference_map.json` |
| `fix_anonymous_refs.py` | 287 | RST `\`text\`__` anonymous references paired with `__ url` targets from RST source |
| `fix_file_references.py` | 176 | Wrong filenames (e.g., `test-case.md` to `creating-test-cases.md`) and relative path depth issues (`../../` to `../`) |
| `fix_cross_page_anchors.py` | 304 | Same-page `#anchor` links where the heading is on a different page. Uses global heading+anchor map with fuzzy matching |
| `fix_missing_anchors.py` | 403 | Extracts `.. _label:` targets from RST source and injects `<a id>` tags at corresponding headings in MD files. Handles cross-file reference labels |
| `fix_anchor_corrections.py` | 117 | Applies data-driven corrections from `anchor_corrections.json` for cases automated scripts cannot resolve |
| `add_legacy_anchors.py` | 775 | Adds `<a id>` anchors for 600+ legacy URL fragments from the old single-page User Guide |

---

## Data Files

### `scripts/reference_map.json` (437 lines)

Central data file for the pipeline. Contains:
| Section | Purpose | Entries |
|---------|---------|---------|
| `rst_to_md_files` | RST filename to MD path mapping | 37 |
| `section_dirs` | RST section dir to MD dir mapping | 6 |
| `filename_corrections` | Wrong filename to correct filename | 4 |
| `bare_word_refs` | `Word_` reference to URL/path target | 80+ |
| `api_references` | Robot Framework API doc links | 14 |
| `ignore_bare_refs` | Python constants to skip | 26 |

To fix a new bare reference, add an entry to `bare_word_refs`:

```json
"myref": {"text": "MyRef", "target": "https://example.com"}
```

### `scripts/anchor_corrections.json` (122 lines)

Maps broken anchor links to correct targets. Format: `"file|broken_link": "correct_link"`.

Three categories:
- **External URLs**: `#slug` that should be `https://...`
- **Internal sections**: `#slug` that should be `../page.md#correct-slug`
- **Slug corrections**: Cross-page links with wrong heading slugs

To fix a broken anchor, add an entry:

```json
"source-file.md|#broken-anchor": "target-file.md#correct-anchor"
```

### `scripts/anchor_map.json` (67 lines)

Legacy anchor name mappings for backward URL compatibility.

---

## Validation

### `scripts/validate.py` (517 LOC)

Runs 9 automated checks against the converted documentation:
| # | Check | What it Verifies | Speed |
|---|-------|------------------|-------|
| 1 | File coverage | All 37 RST files have corresponding MD output | Fast |
| 2 | Images | All 14 images from RST source are present | Fast |
| 3 | Code fences | All fenced code blocks are properly closed (CommonMark-aware) | Fast |
| 4 | RST remnants | No `:role:`, `.. directive::` syntax remains | Fast |
| 5 | Bare RST refs | No unconverted `Word_` references remain | Fast |
| 6 | MkDocs build | Non-strict build succeeds | ~6s |
| 7 | MkDocs strict | Strict build (0 warnings) | ~6s |
| 8 | Broken anchors | No `#anchor` links to non-existent targets | ~6s |
| 9 | DocDiff | Comparison tool runs and produces results | ~4s |

Usage:

```bash
# Full validation (all 9 checks, ~22s)
uv run python scripts/validate.py

# Quick validation (checks 1-5 only, ~0.1s)
uv run python scripts/validate.py --quick

# JSON output for CI
uv run python scripts/validate.py --format json

# Strict mode (exit code 1 on any warning)
uv run python scripts/validate.py --strict
```

Exit codes: `0` = all pass, `1` = warnings, `2` = errors.

---

## DocDiff Comparison Tool

A standalone documentation comparison tool in `docdiff/` that validates the migration by comparing the old single-page HTML against the new multi-page Markdown.

### Architecture

Domain-Driven Design with 6 bounded contexts:

```
docdiff/
  docdiff/
    models.py           # Core domain: Block, Section, Finding, ComparisonResult
    extractors/         # HTML and Markdown content extraction to IR
      html_extractor.py # Parse single-page HTML (stdlib html.parser)
      md_extractor.py   # Parse multi-page Markdown directory
    normalizers/        # Text normalization for comparison
      text_normalizer.py
    aligners/           # Section matching between old and new
      section_aligner.py
    comparators/        # Block-level content comparison with scoring
      content_comparator.py
    validators/         # Link and image validation
      link_validator.py
      image_validator.py
    reporters/          # Report generation (Markdown and JSON)
      markdown_reporter.py
    cli.py              # Command-line interface
```

### Statistics
| Metric | Value |
|--------|-------|
| Source modules | 18 |
| Lines of code | 8,147 |
| Test files | 8 |
| Test cases | 344 |
| Test LOC | 4,921 |
| Test runtime | 0.44s |

### Usage

```bash
cd docdiff
uv sync

# Run tests
uv run python -m pytest tests/ -q

# Run comparison (Markdown report)
uv run python -m docdiff.cli \
  --old-html data/RobotFrameworkUserGuide.html \
  --new-md-dir ../docs \
  --out reports/comparison.md

# Run comparison (JSON report for CI)
uv run python -m docdiff.cli \
  --old-html data/RobotFrameworkUserGuide.html \
  --new-md-dir ../docs \
  --format json \
  --out reports/comparison.json
```

### Comparison Methodology

1. **Extract** sections from both HTML and Markdown into an Intermediate Representation (IR)
2. **Align** sections using a 5-stage matching algorithm (exact number, exact key, fuzzy title, parent context, content hash)
3. **Compare** aligned section pairs at the block level (paragraphs, code, tables, lists, admonitions)
4. **Validate** links and images across both formats
5. **Report** findings by severity (P0 critical, P1 major, P2 minor)

---

## CI/CD

### `.github/workflows/docs.yml` (234 lines)

Three-job GitHub Actions workflow:
| Job | Trigger | What it Does |
|-----|---------|--------------|
| `build-check` | PRs + tags | `mkdocs build --strict`, uploads site artifact |
| `docdiff-check` | PRs | Runs docdiff tests + comparison |
| `deploy` | Tags `v*` | `mike deploy --push --update-aliases $VERSION latest` |

Features:
- `astral-sh/setup-uv` for fast dependency installation with caching
- Concurrency control (cancel-in-progress on rapid pushes)
- Graceful degradation if old HTML source unavailable
- `fetch-depth: 0` for mike's git history requirements

---

## MkDocs Configuration

### `mkdocs.yml` (228 lines)
| Feature | Configuration |
|---------|---------------|
| Theme | Material for MkDocs with custom RF branding |
| Color scheme | Light/dark toggle with system preference detection |
| Navigation | Tabs, sections, expand, prune, indexes, footer |
| Search | lunr.js with RF-specific separator (`[\s\-\._]+`) |
| Versioning | mike with `latest` alias |
| Code highlighting | Pygments with Robot Framework lexer |
| Extensions | 17 markdown extensions (PyMdown suite, admonitions, tables, TOC) |
| Plugins | search, mike, redirects, minify |
| Legacy support | `legacy-redirects.js` for old URL fragment handling |

### Navigation Structure

```
Home
Getting Started (4 pages)
Creating Test Data (10 pages)
Executing Tests (6 pages)
Extending Robot Framework (4 pages)
Supporting Tools (4 pages)
Appendices (8 pages)
```

---

## Quality Metrics

Results when running the full pipeline from a clean `git checkout -- docs/`:
| Check | Status | Detail |
|-------|--------|--------|
| File coverage | PASS | 42/42 files |
| Images | PASS | 14/14 images |
| Code fences | 1 remaining | Backtick heading underline in converter output |
| RST remnants | PASS | 0 remaining |
| Bare RST refs | 1 remaining | Table cell edge case |
| MkDocs build | PASS | 5.5s |
| MkDocs strict | PASS | 0 warnings |
| Broken anchors | 2 remaining | Edge-case anchor corrections |
| DocDiff | PASS | 3,497 findings tracked |

### Improvement from Original State
| Metric | Before Pipeline | After Pipeline | Reduction |
|--------|----------------|----------------|-----------|
| Strict build warnings | 29 | 0 | 100% |
| RST syntax remnants | 13 | 0 | 100% |
| Unconverted bare refs | 162 | 1 | 99% |
| Broken anchor refs | 511 | 2 | 99.6% |
| Code fence issues | 2 | 1 | 50% |

---

## Extending the Pipeline

### Adding a New Bare Reference Mapping

Edit `scripts/reference_map.json`, add to `bare_word_refs`:

```json
"mynewref": {
  "text": "Display Text",
  "target": "https://example.com/page"
}
```

For internal references, use a path relative to `docs/`:

```json
"mynewref": {
  "text": "Display Text",
  "target": "creating-test-data/variables.md#section"
}
```

### Adding a New Anchor Correction

Edit `scripts/anchor_corrections.json`:

```json
"source-file.md|#broken-anchor": "../target-file.md#correct-anchor"
```

Or for external URLs:

```json
"source-file.md|#broken-anchor": "https://example.com"
```

### Adding a New Fix Script

1. Create `scripts/fix_myfix.py` (must accept no arguments, process `docs/` directory)
2. Add it to the pipeline in `scripts/pipeline.py`:

```python
("fix_myfix.py", "Description of what it fixes"),
```

3. Position it correctly in the dependency order
4. Ensure it is idempotent (safe to run multiple times)

### Adding a New Validation Check

Add a function to `scripts/validate.py`:

```python
def check_my_thing() -> CheckResult:
    start = time.time()
    issues = []
    # ... detection logic ...
    elapsed = time.time() - start
    return CheckResult(
        "my_check", len(issues) == 0,
        f"{len(issues)} issues found",
        count=len(issues),
        details=issues,
        elapsed=elapsed
    )
```

Then add it to the checks list in `main()`.

---

## Dependencies

### MkDocs Site (`pyproject.toml`)

- `mkdocs-material` -- Material theme
- `mike` -- Version management
- `pymdown-extensions` -- Extended Markdown syntax
- `pygments` -- Code highlighting
- `mkdocs-minify-plugin` -- HTML/CSS/JS minification
- `mkdocs-redirects` -- Legacy URL redirects

### DocDiff Tool (`docdiff/pyproject.toml`)

- **Runtime**: Python standard library only (zero dependencies)
- **Testing**: pytest, pytest-cov, pygments

### Pipeline Scripts

- Python standard library only (no additional dependencies)
- Uses `pathlib`, `re`, `json`, `subprocess`, `dataclasses`
