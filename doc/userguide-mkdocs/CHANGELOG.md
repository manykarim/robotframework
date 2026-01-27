# Changelog

All notable changes to the Robot Framework User Guide documentation are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] - 2026-01-27

### Added

- **Material for MkDocs documentation system** - Modern static site generator with extensive features
- **Multi-page structure with navigation** - Content organized into 7 sections with 42 pages
- **Full-text search** - Built-in search functionality powered by lunr.js with Robot Framework-aware tokenization
- **Version management** - mike integration for managing multiple documentation versions
- **Dark/light mode toggle** - System preference detection with manual override
- **Code copy buttons** - One-click copying for all code blocks
- **Legacy URL redirect support** - JavaScript-based handler for 334 legacy anchors
- **Navigation tabs** - Sticky header navigation with section tabs
- **Table of contents** - Auto-generated per-page TOC with scroll following
- **Mobile responsive design** - Full functionality on all device sizes
- **Syntax highlighting** - Pygments-based highlighting for Robot Framework, Python, Bash, XML, and more
- **Admonitions** - Collapsible note, warning, tip, and danger blocks
- **Mermaid diagram support** - Fenced code blocks for diagrams

### Changed

- **Migrated from reStructuredText to Markdown** - All 37 RST source files converted to 42 Markdown files
- **Split single HTML file into multi-page structure** - Original monolithic `RobotFrameworkUserGuide.html` (~500KB) now organized into logical sections
- **Updated code highlighting** - Switched from custom Pygments integration to MkDocs native highlighting with robotframeworklexer
- **Modernized build system** - Replaced custom `ug2html.py` with standard MkDocs pipeline
- **Improved navigation** - Fragment identifiers (`#SectionName`) replaced with hierarchical page structure (`/section/page/`)
- **Enhanced search** - Browser find (Ctrl+F) supplemented with dedicated search functionality

### Fixed

- **Code blocks** - All code blocks have proper language identifiers for syntax highlighting
- **Admonitions** - RST directive syntax (`.. note::`) converted to MkDocs syntax (`!!! note`)
- **Tables** - Complex RST tables converted to pipe table syntax
- **Custom roles** - 6 custom RST roles (`:setting:`, `:option:`, `:file:`, `:name:`, `:codesc:`, `:code:`) converted to Markdown equivalents
- **Cross-references** - Internal links updated to new page structure
- **Image paths** - All 14 images relocated with correct relative paths

### Deprecated

- **Single-page HTML format** - Original `RobotFrameworkUserGuide.html` format deprecated in favor of multi-page structure
- **Legacy URL structure** - Old URLs redirected to new structure; legacy anchors preserved via JavaScript handler

### Security

- **Dependency management** - All dependencies pinned via pyproject.toml with regular security audits via Dependabot
- **Content Security Policy ready** - Static HTML output compatible with strict CSP headers
- **No executable content** - Build output is pure static HTML/CSS/JS

## Migration Notes

### For Users

- **Bookmarks**: Existing bookmarks and links will continue to work via automatic redirects
- **Search**: Use the search box in the header instead of browser find for better results
- **Versions**: Use the version dropdown to access documentation for specific Robot Framework releases
- **Offline access**: Download the built site from GitHub releases for offline use

### For Contributors

- **File format**: Edit `.md` files in `docs/` instead of `.rst` files
- **Preview**: Run `uv run mkdocs serve` for live preview at `http://127.0.0.1:8000/`
- **Build**: Run `uv run mkdocs build` to generate static site
- **Style guide**: See [CONTRIBUTING.md](CONTRIBUTING.md) for Markdown conventions

### Breaking Changes

None. All existing URLs redirect to their new locations.

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.0.0 | 2026-01-27 | Initial MkDocs migration release |

## References

- [ADR-001: User Guide Migration Decision](../ADR-001-userguide-migration.md)
- [MIGRATION.md](MIGRATION.md) - Detailed migration guide
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contributor guidelines
- [Material for MkDocs Documentation](https://squidfunk.github.io/mkdocs-material/)
