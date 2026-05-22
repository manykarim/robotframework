# Robot Framework User Guide - Link Analysis Report

## Executive Summary

**Total broken/problematic links identified: 521+ instances**

The MkDocs version of the Robot Framework User Guide has significant link issues
that need to be addressed for proper navigation and cross-referencing.

---

## Issue Categories

### Category 1: Anchor Links with Spaces (259 instances)

**Problem**: Internal anchor links contain spaces instead of hyphens.
MkDocs generates anchors with hyphens, not spaces.

**Pattern**: `](#text with spaces)` should be `](#text-with-spaces)`

**Example locations**:
- `appendices/command-line-options.md` (49 instances)
- `creating-test-data/creating-test-cases.md` (48 instances)
- `extending/creating-test-libraries.md` (78 instances)

**Sample issues**:
```markdown
# Broken:
[Parse only these files](#Parse only these files)
[Sets the name](#Sets the name)
[module search path](#module search path)
[named argument syntax](#named argument syntax)

# Should be:
[Parse only these files](#parse-only-these-files)
[Sets the name](#sets-the-name)
[module search path](#module-search-path)
[named argument syntax](#named-argument-syntax)
```

**Files most affected**:
| File | Count |
|------|-------|
| extending/creating-test-libraries.md | 78 |
| appendices/command-line-options.md | 49 |
| creating-test-data/creating-test-cases.md | 48 |
| creating-test-data/variables.md | 35 |
| creating-test-data/creating-user-keywords.md | 35 |
| executing-tests/configuring-execution.md | 34 |
| creating-test-data/test-data-syntax.md | 32 |
| supporting-tools/libdoc.md | 24 |
| creating-test-data/control-structures.md | 24 |
| executing-tests/test-execution.md | 22 |

---

### Category 2: RST-Style Backtick Underscore References (40+ instances)

**Problem**: reStructuredText reference syntax was not converted to Markdown links.

**Pattern**: `` `reference text`_ `` should be `[reference text](#anchor)` or `[reference text](url)`

**Example locations**:
- `extending/creating-test-libraries.md`
- `appendices/available-settings.md`
- `executing-tests/configuring-execution.md`

**Sample issues**:
```markdown
# Broken RST:
`module search path`_
`suite initialization files`_
`library scope`_
`selecting test cases`_

# Should be converted to:
[module search path](#module-search-path)
[suite initialization files](creating-test-suites.md#suite-initialization-files)
```

---

### Category 3: Word_Underscore RST References (100+ instances)

**Problem**: RST-style references like `Python_`, `Libdoc_`, etc. were not converted
to proper Markdown links.

**Pattern**: `Word_` should be `[Word](url)` or `[Word](#anchor)`

**Files affected**:
- `extending/creating-test-libraries.md` (majority)

**Sample issues**:
```markdown
# Broken:
Robot Framework itself is written with Python_ and naturally test
Libdoc_ also writes this information into the keyword
Process_ library.
Variables_ can contain any kind of objects
Sequence_, MutableSequence_, typing_, int_, float_, Decimal_

# Should be:
Robot Framework itself is written with [Python](https://python.org) and naturally test
[Libdoc](../supporting-tools/libdoc.md) also writes this information into the keyword
[Process](https://robotframework.org/robotframework/latest/libraries/Process.html) library.
```

---

### Category 4: GitHub Issue Links (4 instances)

**Problem**: Issue links use `##NNNN` which is invalid.

**Pattern**: `[#NNNN](##NNNN)` should be `[#NNNN](https://github.com/robotframework/robotframework/issues/NNNN)`

**Locations**:
```
extending/creating-test-libraries.md:1599 - ##5571
creating-test-data/creating-user-keywords.md:959 - ##4462
creating-test-data/creating-test-cases.md:655 - ##5250
creating-test-data/creating-test-cases.md:657 - ##5252
```

---

### Category 5: Cross-File Anchor Links (1 confirmed, likely more)

**Problem**: Links reference anchors that don't exist in the target file.

**Confirmed issue**:
```
appendices/command-line-options.md contains a link
'../executing-tests/output-files.md#console-links',
but 'executing-tests/output-files.md' does not contain an anchor '#console-links'.
```

---

### Category 6: External Links (Generally OK but some concerns)

**HTTP vs HTTPS**: Several links use `http://` which could be updated to `https://`:
- `http://robotframework.org` (multiple occurrences)
- `http://pyyaml.org`

**Note**: Some HTTP URLs are intentional examples (localhost, example.com, etc.)

---

## Priority Recommendations

### High Priority (blocking proper navigation):
1. Fix 259 anchor links with spaces - convert to hyphenated lowercase
2. Fix 4 GitHub issue links

### Medium Priority (affects cross-referencing):
3. Convert RST backtick-underscore references to Markdown links
4. Convert Word_underscore RST references to proper links
5. Fix cross-file anchor references

### Low Priority (cosmetic/best practice):
6. Update HTTP to HTTPS where appropriate

---

## Automated Fix Approach

A script could address many issues:

```python
# Pseudo-code for automated fixes

# 1. Fix anchor links with spaces
re.sub(r'\]\(#([^)]+)\)',
       lambda m: '](#' + m.group(1).lower().replace(' ', '-') + ')',
       content)

# 2. Fix GitHub issue links
re.sub(r'\[#(\d+)\]\(##\1\)',
       r'[#\1](https://github.com/robotframework/robotframework/issues/\1)',
       content)

# 3. RST references need manual mapping to correct URLs
```

---

## Files Requiring Most Work
| Rank | File | Issues |
|------|------|--------|
| 1 | extending/creating-test-libraries.md | ~100+ |
| 2 | appendices/command-line-options.md | ~50 |
| 3 | creating-test-data/creating-test-cases.md | ~50 |
| 4 | creating-test-data/variables.md | ~35 |
| 5 | creating-test-data/creating-user-keywords.md | ~35 |
| 6 | executing-tests/configuring-execution.md | ~34 |
| 7 | creating-test-data/test-data-syntax.md | ~32 |
| 8 | creating-test-data/control-structures.md | ~24 |
| 9 | supporting-tools/libdoc.md | ~24 |
| 10 | executing-tests/test-execution.md | ~22 |

---

## Verification Command

To verify fixes, run:
```bash
cd /home/many/workspace/robotframework/doc/userguide-mkdocs
uv run mkdocs build --strict 2>&1 | grep "contains a link"
```

A successful fix should result in 0 broken link warnings.

---

*Report generated: 2026-01-27*
