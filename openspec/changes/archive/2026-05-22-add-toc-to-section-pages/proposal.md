## Why

The main section index pages (e.g., Creating Test Data, Executing Tests, Extending) currently contain only a heading with no content, leaving users with no overview of what that section covers or how to navigate to sub-pages. Adding a Table of Contents to each section index page lets users orient themselves and jump directly to the topic they need.

## What Changes

- Each section `index.md` page gains a TOC listing all pages in that section with a one-line description of each page's content.
- The TOC uses standard Markdown links, compatible with MkDocs' Material theme rendering.
- Affected section pages: `getting-started`, `creating-test-data`, `executing-tests`, `extending`, `supporting-tools`, `appendices`.

## Capabilities

### New Capabilities

- `section-toc`: Table of Contents blocks on section index pages, providing descriptive links to every page within the section.

### Modified Capabilities

<!-- No existing spec-level requirements are changing -->

## Impact

- `doc/userguide-mkdocs/docs/*/index.md` — all 6 section index files are updated.
- No changes to MkDocs configuration, navigation structure, or source RST files.
- No breaking changes; purely additive content.
