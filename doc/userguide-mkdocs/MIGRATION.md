# Robot Framework User Guide Migration

## Overview

This document describes the migration of the Robot Framework User Guide from reStructuredText (docutils) to Material for MkDocs. The migration modernizes the documentation platform while preserving content accuracy and maintaining backward compatibility with existing URLs.

## Migration Summary

| Aspect | Before | After |
|--------|--------|-------|
| Source Format | reStructuredText (.rst) | Markdown (.md) |
| Build System | Custom `ug2html.py` with docutils | MkDocs with Material theme |
| Output | Single monolithic HTML file (~500KB) | Multi-page static site |
| Navigation | Fragment identifiers (#section) | Hierarchical page structure |
| Search | Browser find (Ctrl+F) | Built-in lunr.js search |
| Versioning | Manual file management | Automated via mike |
| Mobile Support | Limited | Fully responsive |
| Dark Mode | CSS-based toggle | Native Material theme support |

## What Changed

### Documentation Structure

The single `RobotFrameworkUserGuide.html` file has been split into a logical multi-page structure:

```
docs/
  index.md                      # Home page
  getting-started/
    index.md                    # Section overview
    introduction.md             # Introduction to Robot Framework
    copyright-and-license.md    # License information
    installation.md             # Installation instructions
    demonstration.md            # Quick start demo
  creating-test-data/
    index.md
    test-data-syntax.md
    creating-test-cases.md
    creating-tasks.md
    creating-test-suites.md
    using-test-libraries.md
    variables.md
    creating-user-keywords.md
    resource-and-variable-files.md
    control-structures.md
    advanced-features.md
  executing-tests/
    index.md
    basic-usage.md
    test-execution.md
    task-execution.md
    post-processing.md
    configuring-execution.md
    output-files.md
  extending/
    index.md
    creating-test-libraries.md
    remote-library.md
    listener-interface.md
    parser-interface.md
  supporting-tools/
    index.md
    libdoc.md
    testdoc.md
    tidy.md
    other-tools.md
  appendices/
    index.md
    available-settings.md
    command-line-options.md
    documentation-formatting.md
    time-format.md
    boolean-arguments.md
    evaluating-expressions.md
    translations.md
    registrations.md
```

### Syntax Changes

#### Custom Roles to Markdown

The original documentation used custom reST roles defined in `roles.rst`. These have been converted to standard Markdown formatting:

| Original reST | Markdown Equivalent | Usage |
|---------------|---------------------|-------|
| `:setting:\`Library\`` | `*Library*` | Setting names |
| `:option:\`--output\`` | `` `--output` `` | Command line options |
| `:file:\`path/to/file\`` | `*path/to/file*` | File and directory paths |
| `:name:\`My Test\`` | `*My Test*` | Test/keyword/library names |
| `:codesc:\`value\`` | `` `value` `` | Code with escape support |
| Default `:code:` | `` `value` `` | Inline code |

#### Admonitions

reST admonitions have been converted to MkDocs format:

**Before (reST):**
```rst
.. note::
   This is important information.
```

**After (MkDocs Markdown):**
```markdown
!!! note
    This is important information.
```

Supported admonition types: `note`, `warning`, `tip`, `important`, `caution`, `danger`

#### Code Blocks

Code blocks now use fenced syntax with language identifiers:

**Before (reST):**
```rst
.. sourcecode:: robotframework

   *** Test Cases ***
   Example Test
       Log    Hello World
```

**After (Markdown):**
````markdown
```robot
*** Test Cases ***
Example Test
    Log    Hello World
```
````

Supported language identifiers: `robot`, `robotframework`, `python`, `bash`, `yaml`, `json`

## URL Mapping

### Legacy URL Preservation

All existing fragment identifiers from the original documentation have been preserved as HTML anchor aliases. This ensures external links continue to work.

**Example:**
- Old: `RobotFrameworkUserGuide.html#Installation`
- New: `getting-started/installation/` (also accessible via `#Installation` anchor)

### Redirect Configuration

The `mkdocs-redirects` plugin handles the primary redirect from the old URL:

```yaml
plugins:
  - redirects:
      redirect_maps:
        'RobotFrameworkUserGuide.html': 'index.md'
```

### High-Value Anchors Preserved

The following commonly-linked anchors have explicit aliases in the new documentation:

| Legacy Anchor | New Location |
|---------------|--------------|
| `#Installation` | `getting-started/installation.md` |
| `#TestDataSyntax` | `creating-test-data/test-data-syntax.md` |
| `#Variables` | `creating-test-data/variables.md` |
| `#CreatingTestLibraries` | `extending/creating-test-libraries.md` |
| `#ListenerInterface` | `extending/listener-interface.md` |
| `#CommandLineOptions` | `appendices/command-line-options.md` |
| `#AvailableSettings` | `appendices/available-settings.md` |

## Versioning

The documentation now supports multiple versions via the `mike` tool.

### Version URL Structure

```
https://robotframework.org/userguide/latest/          # Current stable
https://robotframework.org/userguide/7.0/             # Specific version
https://robotframework.org/userguide/dev/             # Development
```

### Version Dropdown

A version selector appears in the header navigation, allowing users to switch between:
- `latest` - Current stable release (alias)
- `X.Y` - Specific version numbers
- `dev` - Development documentation

### Version Banners

Outdated versions display a warning banner:

```
You are viewing documentation for Robot Framework version X.Y.
The latest version is Y.Z.
```

## For Contributors

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed instructions on:
- Setting up the development environment
- Writing and formatting documentation
- Building and previewing changes locally
- Submitting pull requests

## Technical Details

### Build System

The documentation is built using:
- **MkDocs** (1.5+) - Static site generator
- **Material for MkDocs** (9.5+) - Theme with extensive features
- **mike** (2.0+) - Version management
- **Pygments** (2.17+) - Syntax highlighting with Robot Framework lexer

### Configuration Files

| File | Purpose |
|------|---------|
| `mkdocs.yml` | MkDocs configuration and navigation |
| `pyproject.toml` | Python dependencies and project metadata |
| `docs/` | Markdown source files |
| `scripts/` | Conversion and build utilities |

### CI/CD Pipeline

Documentation is automatically built and deployed via GitHub Actions:
- Pull requests trigger build validation
- Merges to `main` deploy to `dev` version
- Git tags (`v*`) deploy versioned documentation

## Migration Timeline

| Phase | Duration | Status |
|-------|----------|--------|
| Analysis and Planning | 2 weeks | Complete |
| Infrastructure Setup | 1 week | Complete |
| Content Conversion | 3 weeks | Complete |
| Validation and Testing | 1 week | Complete |
| Deployment | 1 week | Complete |
| Parallel Operation | 6-12 months | Active |

## URL Redirect Reference

### Complete Anchor Mapping

The following table lists major legacy anchors and their new locations:

| Legacy Anchor | New Path |
|---------------|----------|
| `#Introduction` | `getting-started/introduction/` |
| `#Installation` | `getting-started/installation/` |
| `#Demonstration` | `getting-started/demonstration/` |
| `#TestDataSyntax` | `creating-test-data/test-data-syntax/` |
| `#CreatingTestCases` | `creating-test-data/creating-test-cases/` |
| `#CreatingTasks` | `creating-test-data/creating-tasks/` |
| `#CreatingTestSuites` | `creating-test-data/creating-test-suites/` |
| `#UsingTestLibraries` | `creating-test-data/using-test-libraries/` |
| `#Variables` | `creating-test-data/variables/` |
| `#CreatingUserKeywords` | `creating-test-data/creating-user-keywords/` |
| `#ResourceAndVariableFiles` | `creating-test-data/resource-and-variable-files/` |
| `#ControlStructures` | `creating-test-data/control-structures/` |
| `#AdvancedFeatures` | `creating-test-data/advanced-features/` |
| `#BasicUsage` | `executing-tests/basic-usage/` |
| `#TestExecution` | `executing-tests/test-execution/` |
| `#TaskExecution` | `executing-tests/task-execution/` |
| `#PostProcessing` | `executing-tests/post-processing/` |
| `#ConfiguringExecution` | `executing-tests/configuring-execution/` |
| `#OutputFiles` | `executing-tests/output-files/` |
| `#CreatingTestLibraries` | `extending/creating-test-libraries/` |
| `#RemoteLibrary` | `extending/remote-library/` |
| `#ListenerInterface` | `extending/listener-interface/` |
| `#ParserInterface` | `extending/parser-interface/` |
| `#Libdoc` | `supporting-tools/libdoc/` |
| `#Testdoc` | `supporting-tools/testdoc/` |
| `#Tidy` | `supporting-tools/tidy/` |
| `#AvailableSettings` | `appendices/available-settings/` |
| `#CommandLineOptions` | `appendices/command-line-options/` |
| `#DocumentationFormatting` | `appendices/documentation-formatting/` |
| `#TimeFormat` | `appendices/time-format/` |
| `#BooleanArguments` | `appendices/boolean-arguments/` |
| `#EvaluatingExpressions` | `appendices/evaluating-expressions/` |
| `#Translations` | `appendices/translations/` |

For the complete mapping of 334 anchors, see `docs/assets/js/legacy-redirects.js`.

## Known Limitations

### Current Limitations

1. **External API Links**: Some links to Robot Framework API documentation use legacy RST syntax and may not render as clickable links. The referenced content is correct but may require manual navigation to the API docs.

2. **Build Warnings**: Running `mkdocs build --strict` produces 9 warnings related to unconverted RST external reference syntax. These do not affect functionality but prevent strict mode from passing.

3. **Cross-Reference Anchors**: Some internal cross-references between sections may show INFO-level warnings. Navigation still works correctly.

### Browser Compatibility

The documentation is tested and works in:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

Internet Explorer is not supported.

### Accessibility

The Material for MkDocs theme provides:
- Keyboard navigation
- Screen reader compatibility
- High contrast mode (via dark theme)
- Reduced motion support

## Troubleshooting Guide

### Common Issues

#### Search Not Working

**Symptom**: Search returns no results or incomplete results.

**Solutions**:
1. Ensure JavaScript is enabled in your browser
2. Clear browser cache and reload
3. Wait for the page to fully load before searching

#### Code Blocks Not Highlighting

**Symptom**: Code appears as plain text without syntax colors.

**Solutions**:
1. Verify the code block has a language identifier (e.g., ` ```robot `)
2. Clear browser cache
3. Check if a browser extension is blocking JavaScript

#### Dark Mode Not Switching

**Symptom**: Theme toggle button does not change colors.

**Solutions**:
1. Check system color scheme preference settings
2. Clear browser cache
3. Try a different browser to isolate the issue

#### Broken Links from Old URLs

**Symptom**: Clicking an old bookmark shows a 404 or unexpected page.

**Solutions**:
1. The redirect system handles most cases automatically
2. If a specific anchor is not redirecting, report it via GitHub Issues
3. Use the search function to find the content

#### Build Errors (Contributors)

**Symptom**: `mkdocs build` fails with errors.

**Solutions**:
1. Ensure all dependencies are installed: `uv sync`
2. Check for syntax errors in Markdown files
3. Verify all referenced files exist
4. Run `mkdocs build` without `--strict` to see warnings vs errors

### Getting Help

If you encounter issues not covered here:

1. **Check existing issues**: [GitHub Issues](https://github.com/robotframework/robotframework/issues)
2. **Search discussions**: [GitHub Discussions](https://github.com/robotframework/robotframework/discussions)
3. **Report new issues**: Include browser, OS, and steps to reproduce

## Rollback Procedure

The original reST documentation remains available as a fallback:

1. Source files preserved in `doc/userguide/src/`
2. Build script `ug2html.py` remains functional
3. CI workflow for reST build can be re-enabled

To rollback:
```bash
# Build original documentation
cd doc/userguide
python ug2html.py
```

## Support

- **Issues**: Report problems via [GitHub Issues](https://github.com/robotframework/robotframework/issues)
- **Discussions**: Ask questions in [GitHub Discussions](https://github.com/robotframework/robotframework/discussions)
- **Slack**: Join the Robot Framework community on Slack

## References

- [ADR-001: User Guide Migration Decision](../ADR-001-userguide-migration.md)
- [CHANGELOG.md](CHANGELOG.md) - Version history
- [IMPLEMENTATION-SUMMARY.md](IMPLEMENTATION-SUMMARY.md) - Implementation details
- [Material for MkDocs Documentation](https://squidfunk.github.io/mkdocs-material/)
- [mike Version Manager](https://github.com/jimporter/mike)
- [Original User Guide Research](../guides_move_research.md)
