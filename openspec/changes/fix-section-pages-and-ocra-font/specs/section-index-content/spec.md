## ADDED Requirements

### Requirement: Section index files contain intro paragraph and child-page TOC

`reorganize.py` step 3 SHALL generate each section `index.md` with:
1. A `# Section Title` heading
2. A one-paragraph intro from `reference_map.json["section_intros"][<section_dir>]`
3. A `## In this section` heading followed by a Markdown link list for each child page defined in `mkdocs.yml` nav under that section's tab

The generated content SHALL be deterministic: running the pipeline twice with identical inputs produces identical output.

#### Scenario: Pipeline generates section index with intro and TOC

- **WHEN** `reorganize.py` runs step 3 for a section whose `section_intros` entry exists in `reference_map.json`
- **THEN** the output `index.md` contains the intro paragraph and a link list matching `mkdocs.yml` nav order

#### Scenario: Section intro is missing from reference_map.json

- **WHEN** `reorganize.py` runs step 3 and `reference_map.json` has no `section_intros` entry for that section
- **THEN** only the `# Section Title` heading is written (no intro, no TOC link list), same behaviour as before

### Requirement: OCRA font is self-hosted and renders on CI

`docs/assets/fonts/OCRAStd.otf` SHALL be committed to the repository. `assets/extra.css` SHALL declare a `@font-face` rule that points to `../fonts/OCRAStd.otf` using `font-display: swap`. The existing `font-family: OCRA` rule on `h1` SHALL remain unchanged.

#### Scenario: OCRA font loads on GitHub Pages

- **WHEN** the deployed site is opened in a browser that has no locally-installed OCRA font
- **THEN** headings render in OCRA because the font file is served from `assets/fonts/`

#### Scenario: Font file is absent from assets

- **WHEN** `docs/assets/fonts/OCRAStd.otf` does not exist
- **THEN** `mkdocs build --strict` still succeeds (font is a static file, not a Markdown reference)
- **AND** the heading falls back to the browser default monospace font
