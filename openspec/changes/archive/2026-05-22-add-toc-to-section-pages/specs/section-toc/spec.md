## ADDED Requirements

### Requirement: Section index page provides a Table of Contents
Each section `index.md` SHALL contain a Table of Contents (TOC) block immediately below the page heading. The TOC SHALL list every sub-page in that section as a Markdown link accompanied by a one-sentence description of the page's content.

#### Scenario: TOC appears on section index page
- **WHEN** a user opens a section index page (e.g., `creating-test-data/`)
- **THEN** the page displays a list of links to all sub-pages within that section, each with a brief description

#### Scenario: TOC links resolve to existing pages
- **WHEN** a user clicks any link in the TOC
- **THEN** they are navigated to the correct sub-page within the same section

### Requirement: All six section index pages have a TOC
The TOC MUST be added to all six top-level section index pages: `getting-started`, `creating-test-data`, `executing-tests`, `extending`, `supporting-tools`, and `appendices`.

#### Scenario: Complete coverage of sections
- **WHEN** reviewing the six section index pages
- **THEN** every index page contains a non-empty TOC listing its sub-pages

### Requirement: TOC uses plain Markdown links
TOC entries SHALL use standard Markdown link syntax (`[Title](page.md)`) without requiring any MkDocs plugin, macro, or shortcode beyond the default MkDocs Material theme.

#### Scenario: TOC renders without additional plugins
- **WHEN** MkDocs builds the site with the existing `mkdocs.yml` configuration
- **THEN** all TOC links render as clickable HTML links without errors or warnings
