## ADDED Requirements

### Requirement: Internal cross-file links are rewritten to the manual's naming

When publishing converted content into the manual, the publish step SHALL rewrite internal Markdown links whose targets are `.md` files from our section/file naming to the manual's section/file naming, using the file map. Link anchors (`#fragment`) SHALL be preserved verbatim.

#### Scenario: Cross-section relative link is rewritten

- **WHEN** a copied file contains a link to `../creating-test-data/test-data-syntax.md#localization`
- **THEN** the published file contains a link to `../syntax/data.md#localization`

#### Scenario: Same-section bare filename link is rewritten

- **WHEN** `appendix/index.md` (from `appendices/index.md`) contains a link to `command-line-options.md`
- **THEN** the published file contains a link to `cli.md`

#### Scenario: External and anchor-only links are untouched

- **WHEN** a copied file contains an `http(s)://` link, a `mailto:` link, or a pure `#anchor` link
- **THEN** that link is left unchanged

#### Scenario: Code fence content is not rewritten

- **WHEN** a fenced code block contains text resembling a Markdown link
- **THEN** the code block content is left unchanged

### Requirement: Unmappable links are reported, not silently dropped

The publish step SHALL report any internal `.md` link target that has no entry in the file map (e.g. links to `getting-started/` or `supporting-tools/index.md`) and SHALL leave such links unchanged.

#### Scenario: Link to a section with no manual home is reported

- **WHEN** a copied file links to `../getting-started/introduction.md`
- **THEN** the link is left unchanged and the target is listed in the publish summary as unmapped

### Requirement: File map includes section-dir mapping and required extra entries

The `manual_file_map.json` SHALL contain a `section_dirs` mapping (our section directory → manual section directory) and entries for files required by the fork build, including `supporting-tools/libdoc.md` → `extend/libdoc.md` and `extending/ExampleLibrary.png` → `extend/ExampleLibrary.png`.

#### Scenario: Section-dir mapping present

- **WHEN** the file map is loaded
- **THEN** it provides `creating-test-data`→`syntax`, `executing-tests`→`execution`, `extending`→`extend`, `appendices`→`appendix`, and `supporting-tools`→`extend`

### Requirement: Mapped-section build is free of cross-file broken-link warnings

After publishing with link rewriting, a `properdocs build` of the manual SHALL produce no "target not found among documentation files" warnings for links between mapped sections.

#### Scenario: Build warnings for mapped links eliminated

- **WHEN** `properdocs build -f properdocs.yml` runs after publish+rewrite
- **THEN** there are no broken-link warnings for targets within `syntax/`, `execution/`, `extend/`, or `appendix/` that correspond to mapped files
