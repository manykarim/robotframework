# Robot Framework User Guide Migration - Continuation Guide

**Last Updated:** 2026-01-28
**Status:** In Progress - MkDocs migration ~95% complete, docdiff comparison tool complete
**Branch:** master

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [What Has Been Done](#what-has-been-done)
3. [Current State](#current-state)
4. [Problems Encountered and Fixes Applied](#problems-encountered-and-fixes-applied)
5. [Remaining Work](#remaining-work)
6. [All Created Scripts and Files](#all-created-scripts-and-files)
7. [How to Resume Work](#how-to-resume-work)
8. [Commands Reference](#commands-reference)

---

## Project Overview

Migration of the Robot Framework User Guide v7.4.1 from reStructuredText (docutils, single monolithic HTML) to Material for MkDocs (multi-page Markdown site).
| Aspect | Before | After |
|--------|--------|-------|
| Source Format | reStructuredText (.rst) | Markdown (.md) |
| Build System | Custom `ug2html.py` with docutils | MkDocs with Material theme |
| Output | Single HTML file (~500KB) | Multi-page static site (9.7 MB) |
| Navigation | Fragment identifiers (#section) | Hierarchical page structure |
| Search | Browser Ctrl+F only | Built-in lunr.js search |
| Versioning | Manual | Automated via mike |
| Mobile | Limited | Fully responsive |

**Project root:** `/home/many/workspace/robotframework/doc/userguide-mkdocs/`

---

## What Has Been Done

### Phase 1: MkDocs Infrastructure Setup

- Initialized MkDocs project with Material theme
- Configured `mkdocs.yml` with 33 theme features, 17 markdown extensions, 4 plugins
- Set up `pyproject.toml` with dependencies (mkdocs-material, mike, pymdown-extensions, pygments)
- Created custom CSS (`docs/stylesheets/extra.css`) for Robot Framework branding
- Created version banner template (`docs/overrides/main.html`)
- Created abbreviations include (`includes/abbreviations.md`)

### Phase 2: Content Conversion (RST to Markdown)

- Converted 37 RST source files to 42 Markdown files across 6 sections
- Split single monolithic document into hierarchical page structure
- Converted RST roles (`:setting:`, `:option:`, `:file:`, `:name:`, `:codesc:`) to Markdown equivalents
- Converted admonitions from `.. note::` to `!!! note` syntax
- Converted code blocks from `.. sourcecode::` to fenced code blocks with language identifiers
- Preserved 14 images in section-local directories

### Phase 3: Legacy URL Compatibility

- Created `docs/assets/js/legacy-redirects.js` (478 lines) mapping 600+ legacy fragment identifiers
- Created `redirects.yml` (16.9 KB) with comprehensive anchor-to-page mappings
- Configured mkdocs-redirects plugin for base document redirect

### Phase 4: Content Fix Passes (Multiple Iterations)

Multiple automated and manual fix passes were applied to the converted Markdown:
1. Fixed code blocks without language identifiers
2. Fixed truncated admonitions
3. Cleaned RST syntax remnants (`:role:` references, `.. directive::` blocks)
4. Fixed malformed tables
5. Fixed broken internal and cross-file links
6. Standardized code block language identifiers (`robotframework` -> `robot`)
7. Fixed RST API links (e.g., `running.TestSuite_`)
8. Fixed unbalanced code fences
9. Fixed RST sourcecode blocks inside tables
10. Fixed broken anchor links
11. Fixed translation tables content
12. Fixed duplicate word artifacts
13. Cleaned appendices RST artifacts

### Phase 5: DocDiff Comparison Tool Built

Built a complete documentation comparison tool (`docdiff/`) to systematically validate the migration:
- Pure Python stdlib implementation (zero runtime dependencies)
- DDD architecture with 6 bounded contexts
- 18 Python source files, ~7,100 LOC
- 344 tests passing
- CLI interface with markdown and JSON output

**DocDiff Implementation Phases:**
| Phase | What | Result |
|-------|------|--------|
| 1. MD Section Extraction | Extract all headings, not just file-level | 42 -> 800 sections (19x improvement) |
| 2. Section Alignment | Multi-stage matching algorithm (5 stages) | 84.2% match rate (654/777) |
| 3. Block Extraction | Populate section content blocks | 3,811 blocks extracted |
| 4. Validators | Fix link/image validator parameter types | All validators working |
| 5. Semantic Comparison | Weighted content scoring | Paragraph 35%, Code 20%, Table 15%, List 15% |
| 6. Report Improvements | Mapping tables, grouped findings, diff excerpts | 1.9 MB comprehensive report |

---

## Current State

### MkDocs Build
| Check | Status | Notes |
|-------|--------|-------|
| Non-strict build | PASSES | Fully functional site |
| Strict build (`--strict`) | FAILS | 22+ warnings remain |
| Navigation | Working | All 43 pages accessible |
| Images | Working | 14/14 displayed |
| Search | Working | lunr.js index generated (1 MB) |
| Code highlighting | Working | Robot Framework lexer active |
| Light/dark mode | Working | Material theme toggle |
| Mobile responsive | Working | |
| Build time | 6.43s | Target was 2s |

### DocDiff Comparison Results (Latest Run)

```
Old HTML Sections: 804
New MD Sections:   1,784
Matched:           654 (84.2%)
Missing:           123
Extra:             147
Total Findings:    3,938
Performance:       5.48 seconds
```

**Findings Breakdown:**
| Priority | Count | Top Categories |
|----------|-------|----------------|
| P0 (Critical) | 3,060 | broken links (2,891), missing content (126), missing anchors (33), missing images (13) |
| P1 (Major) | 341 | code block changes (311), table changes (30) |
| P2 (Minor) | 537 | link changes (469), content additions (54), content changes (3) |

### Test Suite

- 344 tests passing in 0.67s
- Coverage: 34% overall, core modules 76-96%

---

## Problems Encountered and Fixes Applied

### Problem 1: Section Extraction Granularity Mismatch

**Symptom:** 0% section match rate - zero sections matched between old and new docs.

**Root Cause:** The Markdown extractor returned only 42 file-level sections (one per file), while the HTML extractor returned all 804 headings. No matching was possible.

**Fix (md_extractor.py):** Modified `extract_sections_from_markdown()` to return a flat list of ALL sections (one per heading at any level), using MkDocs-style anchor format for keys. Result: 800 sections extracted.

**File:** `docdiff/docdiff/extractors/md_extractor.py`

### Problem 2: Section Key Normalization Mismatch

**Symptom:** Even similar sections didn't match because keys differed.

**Root Cause:** HTML used anchor IDs (`why-robot-framework`), Markdown used file paths (`getting-started/introduction`).

**Fix (aligners/__init__.py):** Created `normalize_section_key()` that:
- Removes number prefixes (e.g., "2.1.3")
- Converts to lowercase, replaces underscores with hyphens
- Extracts last path component (`getting-started/introduction` -> `introduction`)
- Implemented 5-stage matching: exact number -> exact key -> fuzzy title (>=0.85) -> parent context -> content hash

**File:** `docdiff/docdiff/aligners/__init__.py`

### Problem 3: Validator Parameter Type Errors

**Symptom:** `'list' object has no attribute 'keys'` error when running validators.

**Root Cause:** `check_anchor_drift()` expected dict arguments but received lists.

**Fix:** Built proper dict mappings from sections before calling `check_anchor_drift`. Also renamed import to `validate_link_targets` to avoid shadowing.

**Files:** `docdiff/docdiff/validators/link_validator.py`, `docdiff/docdiff/cli.py`

### Problem 4: Finding Constructor Missing Severity

**Symptom:** `Finding.__init__() missing 1 required positional argument: 'severity'`

**Root Cause:** Validators used `priority=Priority.P0` but the Finding class required `severity=Severity.ERROR`.

**Fix:** Updated all Finding constructors in validators to use `severity` parameter. Also changed from `old_value`/`new_value` to `source_content`/`target_content`.

**Files:** `docdiff/docdiff/validators/link_validator.py`, `docdiff/docdiff/validators/image_validator.py`

### Problem 5: Semantic Comparison Import Errors

**Symptom:** `cannot import name 'compare_section' from 'docdiff.comparators'`

**Root Cause:** `content_comparator.py` used non-existent `ContentBlock` and `ListType` classes. Exports were missing from `comparators/__init__.py`.

**Fix:** Changed `ContentBlock` to `Block`. Added exports for `BLOCK_WEIGHTS`, `compare_blocks`, `compare_section`, `generate_diff_excerpt` to `comparators/__init__.py`.

**Files:** `docdiff/docdiff/comparators/content_comparator.py`, `docdiff/docdiff/comparators/__init__.py`

### Problem 6: NoneType List Items in Comparison

**Symptom:** `TypeError: 'NoneType' object is not iterable` when comparing list blocks.

**Root Cause:** Some `Block` objects had `items=None` instead of an empty list.

**Fix:** Added None guards: `old_list_items = old_list.items if old_list.items is not None else []`

**File:** `docdiff/docdiff/comparators/content_comparator.py` (lines 296 and 327)

### Problem 7: RST Syntax Remnants in Markdown

**Symptom:** Build warnings for unconverted RST syntax.

**Root Cause:** 9 RST-style external API reference links (`running.TestSuite_`) and ~15 RST internal references (`name_` syntax) not converted.

**Status:** Partially fixed. Remaining items documented in FIX-PLAN.md.

### Problem 8: Duplicate CamelCase Directories

**Symptom:** 13 broken image warnings from CamelCase directories.

**Root Cause:** Both lowercase-hyphenated and CamelCase versions of content directories exist. CamelCase versions are not in navigation and have wrong image paths.

**Status:** Documented in FIX-PLAN.md. Fix is to remove the 36 CamelCase duplicate files.

---

## Remaining Work

### High Priority (Must Do)

1. **Remove CamelCase duplicate directories** (5 min)
   - Delete `docs/Appendices/`, `docs/CreatingTestData/`, `docs/ExecutingTestCases/`, `docs/ExtendingRobotFramework/`, `docs/GettingStarted/`, `docs/SupportingTools/`, `docs/RobotFrameworkUserGuide.md`
   - Eliminates 36 duplicate files and 13 image warnings

2. **Convert 9 RST external API links** (30 min)
   - Files: `executing-tests/configuring-execution.md`, `extending/listener-interface.md`, `extending/parser-interface.md`
   - Pattern: `running.TestSuite_` -> `[TestSuite](https://robot-framework.readthedocs.io/en/latest/autodoc/robot.running.html#robot.running.model.TestSuite)`

3. **Fix ~15 RST internal references** (45 min)
   - Pattern: `Translations_` -> `[Translations](../appendices/translations.md)`
   - Files: `appendices/command-line-options.md`, `creating-test-data/variables.md`, `extending/creating-test-libraries.md`, `extending/listener-interface.md`, `extending/parser-interface.md`, `supporting-tools/libdoc.md`

4. **Enable redirects plugin** (2 min)
   - Change `redirect_maps: {}` to `redirect_maps: { 'RobotFrameworkUserGuide.html': 'index.md' }`

### Medium Priority (Should Do)

5. **Fix incomplete admonition conversions** (~5 instances, 20 min)
   - Some admonitions have truncated opening text

6. **Fix anonymous RST link syntax** (30 min)
   - `__ http://...` and `__ [text](#anchor)` patterns in `extending/creating-test-libraries.md`

7. **Address 123 missing sections** from docdiff comparison
   - Sections like `installation-instructions`, `python-installation`, `version-741` exist in old HTML but not in new Markdown
   - Some are intentionally removed (version notes), others may need adding

8. **Improve 2,891 broken link findings**
   - Most are cross-reference links that need updating to new page structure

### Low Priority (Nice to Have)

9. **Optimize build time** (6.43s -> 2s target)
10. **Increase docdiff test coverage** (34% -> 80% target)
11. **Set up CI/CD GitHub Actions workflow**
12. **Add Google Analytics property ID** (currently placeholder `G-XXXXXXXXXX`)

---

## All Created Scripts and Files

### Conversion Scripts (`scripts/`)
| Script | Size | Purpose |
|--------|------|---------|
| `scripts/convert.py` | 36.3 KB | Main RST-to-MkDocs conversion orchestrator |
| `scripts/convert_rst.py` | 9.56 KB | RST-specific conversion utilities |
| `scripts/convert_rst_to_md.py` | 14.8 KB | RST to Markdown format conversion |
| `scripts/fix_admonitions.py` | 17.1 KB | Fix admonition formatting (reST -> MkDocs) |
| `scripts/fix_anchors.py` | 5.18 KB | Fix and validate anchor links |
| `scripts/fix_bullets_simple.py` | 1.35 KB | Simplify bullet formatting |
| `scripts/fix_bullets_spacing.py` | 899 B | Fix bullet list spacing |
| `scripts/fix_code_blocks.py` | 7.08 KB | Fix code block syntax and language identifiers |
| `scripts/fix_cross_file_links.py` | 6.37 KB | Fix links across different files |
| `scripts/fix_links.py` | 8.08 KB | General link fixing utility |
| `scripts/fix_listener_tables.py` | 3.86 KB | Fix listener interface tables |
| `scripts/fix_rst_syntax.py` | 14.9 KB | Clean remaining RST syntax |
| `scripts/fix_tables.py` | 8.59 KB | Fix table formatting |
| `scripts/add_legacy_anchors.py` | 24.9 KB | Add legacy anchor compatibility metadata |
| `scripts/deploy-version.sh` | 892 B | Shell script for mike version deployment |
| `scripts/anchor_map.json` | 2.75 KB | JSON mapping of legacy anchors |

### DocDiff Tool (`docdiff/`)

**Package source (`docdiff/docdiff/`):**
| File | Lines | Purpose |
|------|-------|---------|
| `__init__.py` | 10 | Package metadata (v1.0.0) |
| `__main__.py` | 9 | CLI entry point |
| `cli.py` | 669 | Argparse CLI, pipeline orchestration |
| `models.py` | 470 | BlockType, Severity, Priority, Section, Block, Finding, ComparisonResult |
| `extractors/__init__.py` | 298 | MarkdownExtractor class, common utilities |
| `extractors/html_extractor.py` | 694 | HTMLContentExtractor (stdlib html.parser) |
| `extractors/md_extractor.py` | 724 | Markdown parser, generate_anchor(), extract_from_directory() |
| `normalizers/__init__.py` | 255 | normalize_whitespace(), strip_formatting(), normalize_key() |
| `normalizers/text_normalizer.py` | 565 | normalize_text(), fuzzy_match(), similarity_ratio() |
| `aligners/__init__.py` | 669 | Multi-stage alignment, normalize_section_key() |
| `aligners/section_aligner.py` | 528 | SectionAligner class, AlignmentConfig |
| `comparators/__init__.py` | 451 | BlockComparator, section comparison orchestration |
| `comparators/content_comparator.py` | 885 | BLOCK_WEIGHTS, compare_blocks(), compare_section(), generate_diff_excerpt() |
| `validators/__init__.py` | 355 | LinkValidator, ImageValidator wrapper classes |
| `validators/link_validator.py` | 422 | LinkType, extract_all_links(), check_anchor_drift() |
| `validators/image_validator.py` | 359 | ImageInfo, validate_images(), compare_image_sets() |
| `reporters/__init__.py` | 21 | Module exports |
| `reporters/markdown_reporter.py` | 795 | generate_markdown_report(), generate_json_report() |

**Tests (`docdiff/tests/`):**
| File | Lines | Purpose |
|------|-------|---------|
| `conftest.py` | 424 | Fixtures (HTML/MD samples, expected results) |
| `test_models.py` | 345 | Data model tests |
| `test_extractors.py` | 757 | HTML/Markdown extraction tests |
| `test_normalizers.py` | 404 | Text normalization tests |
| `test_aligners.py` | 505 | Section alignment tests |
| `test_comparators.py` | 791 | Block/section comparison tests |
| `test_validators.py` | 1,073 | Link/image validation tests |
| `test_integration.py` | 622 | End-to-end pipeline tests |

**Benchmarks (`docdiff/benchmarks/`):**
| File | Lines | Purpose |
|------|-------|---------|
| `benchmark.py` | 471 | Performance analysis of all components |

**Documentation (`docdiff/docs/`):**
| File | Lines | Purpose |
|------|-------|---------|
| `USER-GUIDE.md` | 9,058 | End-user documentation |
| `API-REFERENCE.md` | 20,292 | Complete API documentation |
| `ARCHITECTURE.md` | 17,652 | DDD architecture, design principles |
| `CONTRIBUTING.md` | 8,203 | Development setup, contributing |

**Reports (`docdiff/reports/`):**
| File | Size | Purpose |
|------|------|---------|
| `final-comparison-report.md` | 1.9 MB | Latest full comparison (3,938 findings) |
| `validation-report.md` | 3.6 MB | Comprehensive validation results |
| `improved-report.md` | 404 KB | Enhanced report format |
| `comparison-report.md` | 183 KB | Initial comparison findings |
| `IMPLEMENTATION-PLAN.md` | 8.6 KB | 6-phase fix plan for docdiff |
| `IMPLEMENTATION-SUMMARY.md` | 7.3 KB | Implementation metrics and status |
| `benchmark-results.txt` | 2.3 KB | Performance benchmark output |
| `validation-log.txt` | 310 B | Validation execution log |

**Data (`docdiff/data/`):**
| File | Size | Purpose |
|------|------|---------|
| `RobotFrameworkUserGuide.html` | 1.6 MB | Source HTML for comparison |

**Configuration (`docdiff/`):**
| File | Purpose |
|------|---------|
| `pyproject.toml` | Package config (hatchling build, pytest config) |
| `uv.lock` | Dependency lock file |
| `.swarm/state.json` | Swarm coordination state |
| `.claude-flow/` | Claude Flow daemon state and metrics |

### MkDocs Configuration
| File | Purpose |
|------|---------|
| `mkdocs.yml` | MkDocs site configuration |
| `pyproject.toml` | Python dependencies |
| `redirects.yml` | Legacy URL mapping reference (600+ anchors) |

### MkDocs Content (`docs/`)

43 Markdown pages across 6 sections:
| Section | Pages | Key Files |
|---------|-------|-----------|
| Home | 1 | `index.md` |
| Getting Started | 4 | `introduction.md`, `copyright-and-license.md`, `demonstration.md` |
| Creating Test Data | 10 | `test-data-syntax.md`, `creating-test-cases.md`, `variables.md`, `control-structures.md`, `advanced-features.md`, ... |
| Executing Tests | 6 | `basic-usage.md`, `test-execution.md`, `configuring-execution.md`, `output-files.md`, ... |
| Extending RF | 4 | `creating-test-libraries.md`, `remote-library.md`, `listener-interface.md`, `parser-interface.md` |
| Supporting Tools | 4 | `libdoc.md`, `testdoc.md`, `tidy.md`, `other-tools.md` |
| Appendices | 8 | `available-settings.md`, `command-line-options.md`, `translations.md`, ... |

### Static Assets
| File | Purpose |
|------|---------|
| `docs/assets/js/legacy-redirects.js` | Client-side legacy URL redirect (478 lines) |
| `docs/stylesheets/extra.css` | Robot Framework brand colors (229 lines) |
| `docs/overrides/main.html` | Outdated version banner template (15 lines) |
| `includes/abbreviations.md` | Shared abbreviation definitions |

### Project Documentation
| File | Purpose |
|------|---------|
| `MIGRATION.md` | User migration guide (403 lines) |
| `IMPLEMENTATION-SUMMARY.md` | Implementation status and metrics |
| `FIX-PLAN.md` | Remaining fix tasks with instructions |
| `CONTRIBUTING.md` | Contributor guidelines |
| `CHANGELOG.md` | Version history |
| `NAVIGATION_REPORT.md` | Navigation structure analysis |
| `LINK_ANALYSIS_REPORT.md` | Link validation findings |
| `test-report.md` | Test execution results |
| `build-output.txt` | Full build log |

---

## How to Resume Work

### 1. Set Up Environment

```bash
cd /home/many/workspace/robotframework/doc/userguide-mkdocs

# Install MkDocs dependencies
uv sync

# Start dev server to preview docs
uv run mkdocs serve
# -> http://127.0.0.1:8000/
```

### 2. Run DocDiff Comparison

```bash
cd docdiff

# Install docdiff dependencies
uv sync

# Run tests first
uv run python -m pytest tests/ -q

# Run comparison
uv run python -m docdiff.cli \
  --old-html data/RobotFrameworkUserGuide.html \
  --new-md-dir ../docs \
  --out reports/comparison.md

# Run with JSON output for programmatic analysis
uv run python -m docdiff.cli \
  --old-html data/RobotFrameworkUserGuide.html \
  --new-md-dir ../docs \
  --format json \
  --out reports/comparison.json
```

### 3. Address Remaining Issues

Follow the priority order from [Remaining Work](#remaining-work) above. Start with:

```bash
# Task 1: Remove CamelCase duplicates
cd /home/many/workspace/robotframework/doc/userguide-mkdocs/docs
rm -rf Appendices/ CreatingTestData/ ExecutingTestCases/ \
       ExtendingRobotFramework/ GettingStarted/ SupportingTools/ \
       RobotFrameworkUserGuide.md

# Verify reduced warnings
cd ..
uv run mkdocs build 2>&1 | grep -c "WARNING"
```

### 4. Verify After Changes

```bash
# Non-strict build
uv run mkdocs build

# Strict build (target: 0 warnings)
uv run mkdocs build --strict

# Run docdiff comparison again to measure improvement
cd docdiff
uv run python -m docdiff.cli \
  --old-html data/RobotFrameworkUserGuide.html \
  --new-md-dir ../docs \
  --out reports/post-fix-report.md
```

---

## Commands Reference

### MkDocs

```bash
uv run mkdocs serve              # Dev server at :8000
uv run mkdocs build              # Build static site to site/
uv run mkdocs build --strict     # Build with warnings as errors
uv run mike deploy 7.4 latest    # Deploy version
uv run mike list                 # List deployed versions
uv run mike set-default latest   # Set default version
```

### DocDiff

```bash
cd docdiff
uv run python -m pytest tests/ -q              # Run tests
uv run python -m pytest tests/ -v --tb=short   # Verbose tests
uv run python -m docdiff.cli --help             # CLI help
uv run python -m docdiff.cli \
  --old-html data/RobotFrameworkUserGuide.html \
  --new-md-dir ../docs \
  --out reports/report.md                       # Run comparison
uv run python -m docdiff.cli \
  --old-html data/RobotFrameworkUserGuide.html \
  --new-md-dir ../docs \
  --format json --out reports/report.json       # JSON output
uv run python benchmarks/benchmark.py           # Performance benchmark
```

### Rollback

```bash
# Restore original RST documentation
cd /home/many/workspace/robotframework/doc/userguide
python ug2html.py
# Output: RobotFrameworkUserGuide.html
```
