# Robot Framework User Guide Migration - Fix Plan

## Executive Summary

The migration from RST to MkDocs Markdown is approximately 95% complete. The documentation builds successfully in non-strict mode and produces a fully functional 53-page site with search, navigation, and syntax highlighting. However, there are 22+ warnings that need to be addressed for a clean strict-mode build.

**Key Issues Identified:**
- 13 broken image links in CamelCase duplicate files
- 9 unconverted RST external API reference links (`running.TestSuite_`, etc.)
- 36 duplicate files (CamelCase versions not in navigation)
- Multiple RST-style internal reference links not converted (`name_` syntax)
- Missing `assets/images/` directory structure

**Total Estimated Effort:** 2-4 hours for critical/high priority fixes

---

## Issue Categories

### 1. Critical Issues (Must Fix) - 0 Issues

None. The documentation builds and all content is accessible.

### 2. High Priority (Should Fix) - 49 Issues
| Issue Type | Count | Impact |
|------------|-------|--------|
| Broken image links (CamelCase files) | 13 | Images don't display in orphan files |
| External API reference links | 9 | Broken links in strict mode |
| Duplicate CamelCase directories | 36 files | Confusion, maintenance burden |

### 3. Medium Priority (Nice to Fix) - ~20 Issues
| Issue Type | Count | Impact |
|------------|-------|--------|
| RST-style internal references | ~15 | INFO warnings, some broken links |
| Incomplete admonition conversions | ~5 | Formatting issues |

### 4. Low Priority (Future Enhancement) - Ongoing

- Performance optimization (build time: 6.4s vs 2s target)
- Legacy URL redirect coverage expansion
- Additional anchor aliases for backward compatibility

---

## Detailed Fix Tasks

### Task 1: Remove Duplicate CamelCase Directories

**Problem**: The `docs/` folder contains both lowercase-hyphenated and CamelCase versions of all content files. The CamelCase versions are not in the navigation and have incorrect image paths.

**Affected Directories:**
```
/home/many/workspace/robotframework/doc/userguide-mkdocs/docs/
  - Appendices/           (8 files - REMOVE)
  - CreatingTestData/     (10 files - REMOVE)
  - ExecutingTestCases/   (6 files - REMOVE)
  - ExtendingRobotFramework/ (4 files - REMOVE)
  - GettingStarted/       (3 files - REMOVE)
  - SupportingTools/      (4 files - REMOVE)
  - RobotFrameworkUserGuide.md (1 file - REMOVE or FIX)
```

**Solution**: Remove or consolidate the CamelCase directories since they are duplicates not referenced in navigation.

**Commands:**
```bash
cd /home/many/workspace/robotframework/doc/userguide-mkdocs/docs

# Backup first (optional)
tar -czf ../camelcase-backup.tar.gz Appendices/ CreatingTestData/ ExecutingTestCases/ ExtendingRobotFramework/ GettingStarted/ SupportingTools/ RobotFrameworkUserGuide.md

# Remove duplicate directories
rm -rf Appendices/
rm -rf CreatingTestData/
rm -rf ExecutingTestCases/
rm -rf ExtendingRobotFramework/
rm -rf GettingStarted/
rm -rf SupportingTools/
rm -f RobotFrameworkUserGuide.md
```

**Estimated Effort:** Small (5 minutes)

**Verification:**
```bash
mkdocs build 2>&1 | grep -c "WARNING"
# Should reduce warnings by ~13 (the image warnings from CamelCase files)
```

---

### Task 2: Convert External API Reference Links

**Problem**: 9 RST-style external API reference links were not converted to proper Markdown URLs.

**Affected Files and Lines:**
| File | Line | RST Reference | Correct URL |
|------|------|---------------|-------------|
| `executing-tests/configuring-execution.md` | 754-755 | `running.TestSuite_`, `running.TestCase_`, `running.Keyword_` | Robot Framework API docs |
| `extending/listener-interface.md` | 481 | `running.TestSuite_` | API docs |
| `extending/listener-interface.md` | 493 | `running.TestCase_` | API docs |
| `extending/listener-interface.md` | 505 | `running.Keyword_` | API docs |
| `extending/listener-interface.md` | 583 | `running.TestLibrary_` | API docs |
| `extending/listener-interface.md` | 585 | `running.Import_` | API docs |
| `extending/listener-interface.md` | 590 | `running.ResourceFile_` | API docs |
| `extending/listener-interface.md` | 592 | `running.Import_` | API docs |
| `extending/listener-interface.md` | 599 | `running.Import_` | API docs |
| `extending/parser-interface.md` | 60 | `running.TestSuite_` | API docs |
| `extending/parser-interface.md` | 77 | `running.TestSuite_` | API docs |

**Solution**: Replace RST-style links with proper Markdown external links to the Robot Framework API documentation.

**Base API URL:** `https://robot-framework.readthedocs.io/en/latest/autodoc/robot.running.html`

**Replacements:**

```markdown
# Pattern: [text](running.ClassName_) or running.ClassName_
# Replace with proper external links:

running.TestSuite_ -> [TestSuite](https://robot-framework.readthedocs.io/en/latest/autodoc/robot.running.html#robot.running.model.TestSuite)

running.TestCase_ -> [TestCase](https://robot-framework.readthedocs.io/en/latest/autodoc/robot.running.html#robot.running.model.TestCase)

running.Keyword_ -> [Keyword](https://robot-framework.readthedocs.io/en/latest/autodoc/robot.running.html#robot.running.model.Keyword)

running.TestLibrary_ -> [TestLibrary](https://robot-framework.readthedocs.io/en/latest/autodoc/robot.running.html#robot.running.model.TestLibrary)

running.ResourceFile_ -> [ResourceFile](https://robot-framework.readthedocs.io/en/latest/autodoc/robot.running.html#robot.running.model.ResourceFile)

running.Import_ -> [Import](https://robot-framework.readthedocs.io/en/latest/autodoc/robot.running.html#robot.running.model.Import)
```

**Example Edits:**

For `executing-tests/configuring-execution.md` line 754-755:
```markdown
# Before:
<running.TestSuite_>`_, [test cases](running.TestCase_) and `keywords
<running.Keyword_>`_ using it.

# After:
[TestSuite](https://robot-framework.readthedocs.io/en/latest/autodoc/robot.running.html#robot.running.model.TestSuite), [test cases](https://robot-framework.readthedocs.io/en/latest/autodoc/robot.running.html#robot.running.model.TestCase) and [keywords](https://robot-framework.readthedocs.io/en/latest/autodoc/robot.running.html#robot.running.model.Keyword) using it.
```

**Estimated Effort:** Medium (30 minutes)

**Verification:**
```bash
grep -r "running\.\(TestSuite\|TestCase\|Keyword\|TestLibrary\|ResourceFile\|Import\)_" docs/
# Should return no results after fix
```

---

### Task 3: Fix RST-Style Internal Reference Links

**Problem**: Multiple RST-style internal references (`name_` syntax) were not fully converted.

**Affected Files (sample):**
| File | Issue |
|------|-------|
| `appendices/command-line-options.md` | `Translations_`, `merging outputs_`, `Console links_` |
| `creating-test-data/variables.md` | `Secret_` |
| `extending/creating-test-libraries.md` | `dt-mod_`, `Secret_` |
| `extending/listener-interface.md` | `ListenerV2_`, `ListenerV3_` |
| `extending/parser-interface.md` | `pathlib_` |
| `supporting-tools/libdoc.md` | `inline styles_` |

**Solution**: Convert RST-style references to proper Markdown links or plain text.

**Pattern to Search:**
```bash
grep -rE '\b\w+_(?:\s|$|\)|\])' docs/*.md docs/**/*.md
```

**Example Fixes:**

```markdown
# RST style (broken):
See the Translations_ section for details.

# Markdown style (fixed):
See the [Translations](../appendices/translations.md) section for details.

# Or if it's a Python library reference:
pathlib_  ->  [pathlib](https://docs.python.org/3/library/pathlib.html)
```

**Estimated Effort:** Medium (45 minutes)

---

### Task 4: Fix Incomplete Admonition Conversions

**Problem**: Some admonitions were partially converted but have truncated content.

**Example from** `executing-tests/output-files.md` (lowercase version):
```markdown
!!! tip
         does not require processing output files after execution. Disabling
         log_ generation when running tests can thus save memory.
```

This is missing the opening text of the tip.

**Solution**: Review and fix all admonitions with incomplete content.

**Search Pattern:**
```bash
grep -A 2 "^!!!" docs/**/*.md | grep -B 1 "^\s*$"
```

**Estimated Effort:** Small (20 minutes)

---

### Task 5: Verify and Update Image Paths

**Problem**: Images exist in section-specific directories but some files reference incorrect paths.

**Current Image Locations:**
```
docs/executing-tests/*.png (9 images)
docs/getting-started/*.png (3 images)
docs/extending/remote.png (1 image)
docs/supporting-tools/ExampleLibrary.png (1 image)
```

**Files with Correct Image Paths** (lowercase directories):
- These already work correctly since images are co-located with markdown files.

**Solution**: After removing CamelCase directories (Task 1), all image warnings should be resolved.

**Estimated Effort:** None (resolved by Task 1)

---

### Task 6: Enable Redirects Plugin

**Problem**: The redirects plugin is configured but with empty redirect maps.

**Current Config** (mkdocs.yml line 107-108):
```yaml
- redirects:
    redirect_maps: {}
```

**Solution**: Enable the main document redirect:

```yaml
- redirects:
    redirect_maps:
      'RobotFrameworkUserGuide.html': 'index.md'
```

**Estimated Effort:** Small (2 minutes)

---

### Task 7: Update mkdocs.yml Analytics

**Problem**: Google Analytics property ID is placeholder.

**Current** (mkdocs.yml line 89):
```yaml
property: G-XXXXXXXXXX
```

**Solution**: Either remove analytics config or add real property ID:

```yaml
# Option 1: Remove (for now)
# analytics:
#   provider: google
#   property: G-XXXXXXXXXX

# Option 2: Add real ID
analytics:
  provider: google
  property: G-REAL-PROPERTY-ID
```

**Estimated Effort:** Small (2 minutes)

---

### Task 8: Fix Anonymous Link Syntax

**Problem**: RST anonymous links (`__`) not converted to Markdown.

**Example from** `extending/creating-test-libraries.md`:
```markdown
__ http://docs.python.org/library/ctypes.html
__ [Keyword arguments](#Keyword arguments)
```

**Solution**: Convert to standard Markdown links or remove if orphaned.

**Estimated Effort:** Medium (30 minutes)

---

## Implementation Order

### Phase 1: Quick Wins (30 minutes)
1. **Task 1**: Remove CamelCase duplicate directories
2. **Task 6**: Enable redirects plugin
3. **Task 7**: Update analytics placeholder

### Phase 2: Core Fixes (1-2 hours)
4. **Task 2**: Convert external API reference links (critical for strict mode)
5. **Task 3**: Fix RST-style internal references
6. **Task 4**: Fix incomplete admonitions

### Phase 3: Cleanup (30 minutes)
7. **Task 8**: Fix anonymous link syntax
8. Final verification and testing

---

## Verification Steps

### After Each Phase

```bash
cd /home/many/workspace/robotframework/doc/userguide-mkdocs
source .venv/bin/activate

# Count warnings
mkdocs build 2>&1 | grep -c "WARNING"

# List remaining warnings
mkdocs build 2>&1 | grep "WARNING"

# Test strict mode (target: 0 warnings)
mkdocs build --strict
```

### Final Verification Checklist

- [ ] `mkdocs build` passes with 0 warnings
- [ ] `mkdocs build --strict` passes
- [ ] All navigation links work
- [ ] All images display correctly
- [ ] Search returns relevant results
- [ ] Code blocks have syntax highlighting
- [ ] Light/dark mode toggle works
- [ ] Mobile responsive layout works

### Link Verification

```bash
# Install linkchecker if needed
pip install linkchecker

# Start dev server in background
mkdocs serve &

# Check links
linkchecker http://127.0.0.1:8000/
```

---

## Rollback Considerations

### If Fixes Cause Problems

1. **Git Restore**: All changes can be reverted via git:
   ```bash
   git checkout -- docs/
   git checkout -- mkdocs.yml
   ```

2. **Backup Restoration**: CamelCase files were optionally backed up:
   ```bash
   cd /home/many/workspace/robotframework/doc/userguide-mkdocs
   tar -xzf camelcase-backup.tar.gz -C docs/
   ```

3. **Original RST**: The original RST documentation remains available:
   ```bash
   cd /home/many/workspace/robotframework/doc/userguide
   python ug2html.py
   ```

---

## Success Criteria
| Metric | Current | Target |
|--------|---------|--------|
| Build Warnings | 22+ | 0 |
| Strict Build | FAIL | PASS |
| Duplicate Files | 36 | 0 |
| Broken API Links | 9 | 0 |
| Broken Image Links | 13 | 0 |

---

## Appendix: File Locations

### Primary Documentation
```
/home/many/workspace/robotframework/doc/userguide-mkdocs/
  docs/
    index.md                          # Home page
    getting-started/                  # Section: Getting Started
    creating-test-data/               # Section: Creating Test Data
    executing-tests/                  # Section: Executing Tests
    extending/                        # Section: Extending RF
    supporting-tools/                 # Section: Supporting Tools
    appendices/                       # Section: Appendices
    assets/js/legacy-redirects.js     # Legacy URL handler
  mkdocs.yml                          # Main configuration
  redirects.yml                       # URL mapping reference
```

### Original RST Source (Reference)
```
/home/many/workspace/robotframework/doc/userguide/src/
  RobotFrameworkUserGuide.rst         # Main document
  roles.rst                           # Custom RST roles
  GettingStarted/
  CreatingTestData/
  ExecutingTestCases/
  ExtendingRobotFramework/
  SupportingTools/
  Appendices/
```

---

*Generated: 2026-01-27*
*Status: Ready for Implementation*
