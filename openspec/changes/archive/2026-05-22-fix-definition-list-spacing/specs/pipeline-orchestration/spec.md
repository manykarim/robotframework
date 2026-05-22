## MODIFIED Requirements

### Requirement: Pipeline executes stages in order including fetch
The pipeline (`pipeline.py`) SHALL execute stages in the order: FETCH (Stage 0) → CLEAN → CONVERT → FIX → ASSETS → VALIDATE, where Stage 0 fetches the latest RST source from upstream before any other processing.

#### Scenario: Default run fetches upstream then converts
- **WHEN** `python pipeline.py` is run without flags
- **THEN** Stage 0 (FETCH) runs first, calling `fetch_upstream.py` with the default ref
- **THEN** on successful fetch, the pipeline continues with CLEAN → CONVERT → FIX → ASSETS → VALIDATE
- **THEN** the final site reflects the fetched upstream content

#### Scenario: Skip fetch preserves existing RST
- **WHEN** `python pipeline.py --skip-fetch` is run
- **THEN** Stage 0 is skipped entirely
- **THEN** the pipeline proceeds directly with CLEAN → CONVERT → FIX → ASSETS → VALIDATE using local RST files
- **THEN** behavior is identical to the pre-change pipeline

#### Scenario: Fetch stage failure aborts pipeline
- **WHEN** Stage 0 (FETCH) fails (non-zero exit from `fetch_upstream.py`)
- **THEN** the pipeline prints the fetch error
- **THEN** the pipeline exits without running CLEAN, CONVERT, or any subsequent stages

### Requirement: Pipeline accepts upstream-ref flag
The pipeline SHALL accept an `--upstream-ref` flag that is forwarded to `fetch_upstream.py`.

#### Scenario: Specific ref passed through
- **WHEN** `python pipeline.py --upstream-ref v7.2.1` is run
- **THEN** Stage 0 calls `fetch_upstream.py --ref v7.2.1`
- **THEN** conversion proceeds against the RST content from that ref

#### Scenario: upstream-ref ignored when skip-fetch is set
- **WHEN** `python pipeline.py --skip-fetch --upstream-ref v7.2.1` is run
- **THEN** Stage 0 is skipped; `--upstream-ref` has no effect

### Requirement: Definition list items render with compact visual spacing
The MkDocs site SHALL render definition list items with reduced vertical spacing so that each term and its definition read as a tight unit. This SHALL be implemented via CSS overrides in `stylesheets/extra.css` targeting `.md-typeset dl dt` and `.md-typeset dl dd`, reducing the Material theme's default 1em margins. Blank lines between def-list items in Markdown source SHALL be preserved (they are required by Python-Markdown's `def_list` extension grammar).

#### Scenario: Definition list renders without large gaps between items
- **WHEN** a page containing a definition list is rendered
- **THEN** each term is visually adjacent to its own definition (no large gap between `<dt>` and `<dd>`)
- **THEN** consecutive items are separated by a small but visible margin

#### Scenario: Markdown source blank lines are preserved
- **WHEN** `fix_definition_lists.py` processes a file with blank-line-separated def-list items
- **THEN** the blank lines between items are NOT removed
- **THEN** `mkdocs build` renders a flat `<dl>` with sibling `<dt>`/`<dd>` elements (no nesting)
