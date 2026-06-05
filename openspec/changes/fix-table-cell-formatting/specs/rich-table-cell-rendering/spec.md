## ADDED Requirements

### Requirement: Bullet lists in grid table cells render as HTML list elements

The converter SHALL detect RST bullet items (lines starting with `* `) inside grid table cells and render them as `<ul><li>…</li></ul>` in the output Markdown pipe table cell.

#### Scenario: Single bullet group in cell

- **WHEN** a grid table cell contains lines starting with `* `
- **THEN** the converted Markdown cell contains `<ul>` with one `<li>` per bullet item

#### Scenario: Bullet with continuation line

- **WHEN** a bullet item line (`* text`) is followed by a plain-text continuation line before the next blank
- **THEN** the continuation is joined to the bullet item in the same `<li>` element

#### Scenario: Cell with no bullets

- **WHEN** a grid table cell contains only plain text (no `* ` lines)
- **THEN** the converted cell is identical to the current output (plain text, no HTML wrappers)

### Requirement: Paragraph breaks inside grid table cells produce visible separation

The converter SHALL detect blank intra-cell lines (empty cell slots in a row) and render them as `<br>` separators in the output, so that multi-paragraph cell content remains visually distinct.

#### Scenario: Two paragraphs separated by blank line

- **WHEN** a grid table cell has two text blocks separated by a blank intra-cell line
- **THEN** the converted cell contains `<br>` between the two blocks

#### Scenario: Section header followed by bullet list

- **WHEN** a grid table cell has a text line (e.g. `Shared attributes:`) followed by a blank and then bullet items
- **THEN** the output has the header text, `<br>`, and a `<ul>` block

#### Scenario: Multiple bullet groups with section headers

- **WHEN** a cell contains alternating section headers and bullet groups separated by blank lines (as in `start_keyword`)
- **THEN** each section header appears on its own line and each bullet group is a separate `<ul>`, all separated by `<br>`

### Requirement: Pipeline regenerates affected files after converter fix

After the converter is updated, running the pipeline SHALL regenerate `extending/listener-interface.md`, `extending/remote-library.md`, and `creating-test-data/test-data-syntax.md` with the corrected cell content.

#### Scenario: listener-interface.md start_keyword cell

- **WHEN** the pipeline runs after the converter fix
- **THEN** the `start_keyword` row in `listener-interface.md` contains `<ul>` elements for the shared attributes section and each per-type attributes section

#### Scenario: mkdocs build passes after regeneration

- **WHEN** `mkdocs build --strict` is run after pipeline regeneration
- **THEN** the build exits with code 0
