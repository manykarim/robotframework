# Navigation and Cross-Reference Verification Report

## Executive Summary

This report documents the cross-reference and navigation issues found when comparing the local MkDocs documentation with the original Robot Framework User Guide.

**Overall Status: NEEDS ATTENTION**
- Legacy redirect handling: Good coverage (334 anchors mapped)
- Internal navigation: Working but with warnings
- RST conversion: Incomplete - significant remnants remain
- Image references: Multiple missing files

---

## 1. Duplicate Directory Structure (CRITICAL)

Both PascalCase and kebab-case directory versions exist in `/docs/`:

| PascalCase | kebab-case |
|------------|------------|
| Appendices/ | appendices/ |
| CreatingTestData/ | creating-test-data/ |
| ExecutingTestCases/ | executing-tests/ |
| ExtendingRobotFramework/ | extending/ |
| GettingStarted/ | getting-started/ |
| SupportingTools/ | supporting-tools/ |

**Impact**:
- MkDocs build reports 37 files "not included in nav"
- Confusion about which is canonical
- Image references point to wrong paths

**Recommendation**: Remove the PascalCase directories after verifying kebab-case versions are complete.

---

## 2. Missing Image Files

The following images are referenced but not found:

| File | Missing Image |
|------|---------------|
| ExecutingTestCases/OutputFiles.md | log_passed.png, log_failed.png, log_skipped.png |
| ExecutingTestCases/OutputFiles.md | report_passed.png, report_failed.png |
| ExecutingTestCases/OutputFiles.md | visible_log_level.png, tagstatcombine.png, tagstatlink.png |
| ExtendingRobotFramework/RemoteLibrary.md | remote.png |
| GettingStarted/Introduction.md | architecture.png, testdata_screenshots.png, screenshots.png |
| SupportingTools/Libdoc.md | ExampleLibrary.png |

**Total**: 13 missing image files

---

## 3. Legacy Anchor Redirect Coverage

### anchor_map.json
- **Entries**: ~66 major section anchors
- **Coverage**: Major sections only (Introduction, Variables, etc.)
- **Location**: `/scripts/anchor_map.json`

### legacy-redirects.js
- **Entries**: ~334 anchor mappings
- **Coverage**: Comprehensive, includes subsections
- **Location**: `/docs/assets/js/legacy-redirects.js`
- **Status**: Well-structured with comments, handles version paths

### Original Site Anchors
- **Estimated**: 250-300 unique anchors
- **Categories**: Getting Started (~15), Test Data (~80), Execution (~50), Extending (~40), Tools (~25), Appendices (~60)

**Assessment**: The JS redirect file provides good coverage. The anchor_map.json appears to be for reference only.

---

## 4. Unconverted RST Syntax (MAJOR ISSUE)

### RST Reference Patterns Still Present

**Double underscore links (`__`)**:
- Count: ~1141 instances
- Example: `Python C API`__, `ctypes`__
- Location: Primarily in `/docs/extending/creating-test-libraries.md`

**RST link targets**:
```rst
.. _varargs-library:
.. _kwargs-library:
.. _function annotations: https://www.python.org/dev/peps/pep-3107/
```

**Hybrid broken syntax**:
```markdown
[TestSuite](running.TestSuite_)_
[test cases](running.TestCase_)
```

### Files Most Affected

1. `/docs/extending/creating-test-libraries.md` - Extensive RST remnants
2. `/docs/extending/listener-interface.md` - Model object references
3. `/docs/extending/parser-interface.md` - Model object references
4. `/docs/executing-tests/configuring-execution.md` - API references
5. `/docs/appendices/command-line-options.md` - Reference links

---

## 5. Broken Links to API Documentation

The following references to Robot Framework API objects are broken:

| Pattern | Files Affected |
|---------|----------------|
| `running.TestSuite_` | listener-interface.md, parser-interface.md, configuring-execution.md |
| `running.TestCase_` | listener-interface.md, configuring-execution.md |
| `running.Keyword_` | listener-interface.md, configuring-execution.md |
| `running.TestLibrary_` | listener-interface.md |
| `running.ResourceFile_` | listener-interface.md |
| `running.Import_` | listener-interface.md |
| `result.TestSuite_` | listener-interface.md |
| `result.TestCase_` | listener-interface.md |

**Recommendation**: Convert to proper external links to Robot Framework API documentation.

---

## 6. MkDocs Build Output Analysis

### Warnings
- 13 missing image file warnings
- 11 broken link warnings (running.*, result.*)
- Multiple "unrecognized relative link" info messages

### Info Messages (Unconverted Links)
- `Translations_`
- `Automatically logging assigned variable value_`
- `Stopping when first test case fails_`
- `Console links_`
- `merging outputs_`
- `Secret_`
- `Simple patterns_`
- `dt-mod_`
- `ListenerV2_`, `ListenerV3_`
- `inline styles_`
- `pathlib_`

---

## 7. Navigation Structure Verification

### mkdocs.yml Nav Status: WORKING

```yaml
nav:
  - Home: index.md
  - Getting Started: (4 pages)
  - Creating Test Data: (11 pages)
  - Executing Tests: (7 pages)
  - Extending Robot Framework: (5 pages)
  - Supporting Tools: (5 pages)
  - Appendices: (9 pages)
```

### Index Files: CORRECT
All section index files properly link to child pages using relative paths.

---

## 8. Recommended Fixes

### Priority 1 (Critical)
1. **Remove duplicate PascalCase directories** after verifying content is in kebab-case versions
2. **Add or relocate missing image files** to correct paths

### Priority 2 (High)
3. **Convert RST link syntax** in affected files:
   - Replace `text`__ with proper Markdown links
   - Convert `.. _target:` definitions to anchor tags or remove
   - Fix `[text](running.*)_` hybrid patterns

### Priority 3 (Medium)
4. **Add links to Robot Framework API docs** for model object references
5. **Review and update anchor_map.json** if used programmatically

---

## Appendix: File Locations

| Resource | Path |
|----------|------|
| MkDocs config | `/home/many/workspace/robotframework/doc/userguide-mkdocs/mkdocs.yml` |
| Legacy redirects | `/home/many/workspace/robotframework/doc/userguide-mkdocs/docs/assets/js/legacy-redirects.js` |
| Anchor map | `/home/many/workspace/robotframework/doc/userguide-mkdocs/scripts/anchor_map.json` |
| Docs source | `/home/many/workspace/robotframework/doc/userguide-mkdocs/docs/` |

---

*Report generated: 2026-01-27*
*Tester Agent: Cross-Reference and Navigation Verification*
