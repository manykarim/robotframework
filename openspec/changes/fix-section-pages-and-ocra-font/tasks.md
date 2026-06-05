## 1. OCRA font asset

- [x] 1.1 Copy `/home/many/.local/share/fonts/OCRAStd.otf` to `doc/userguide-mkdocs/docs/assets/fonts/OCRAStd.otf`
- [x] 1.2 Add `@font-face` declaration to `doc/userguide-mkdocs/docs/assets/extra.css` before the existing h1 rule:
  ```css
  @font-face {
    font-family: OCRA;
    src: url('../fonts/OCRAStd.otf') format('opentype');
    font-display: swap;
  }
  ```

## 2. Section intro data in reference_map.json

- [x] 2.1 Add `"section_intros"` key to `doc/userguide-mkdocs/scripts/reference_map.json` with one entry per section dir (getting-started, creating-test-data, executing-tests, extending, supporting-tools, appendices). Use the RF Voice intro paragraphs from the previously-committed content in `fd99bc5e1` (or re-derive from the add-section-summaries archive).

## 3. Nav helper in reorganize.py

- [x] 3.1 Add a `load_nav_children(section_dir)` helper to `reorganize.py` that reads `mkdocs.yml`, finds the nav list for the given section, and returns `[(title, relative_path), ...]` for non-index entries
- [x] 3.2 Add a `load_section_intros()` helper that reads `reference_map.json["section_intros"]` and returns `{section_dir: intro_text}`

## 4. Update section index generation in reorganize.py

- [x] 4.1 In `reorganize.py` step 3, replace the `idx.write_text(f"# {title}\n")` line with a call that:
  1. Writes `# {title}\n\n`
  2. Appends the intro paragraph from `load_section_intros()` (if present) + `\n\n`
  3. Appends `## In this section\n\n` + a Markdown link list from `load_nav_children()` + `\n`

## 5. Verification

- [x] 5.1 Run `python scripts/pipeline.py` from `doc/userguide-mkdocs/` and confirm section index files now contain intro paragraphs and TOC links
- [x] 5.2 Run `uv run mkdocs build --strict` from `doc/userguide-mkdocs/` and confirm no errors
- [x] 5.3 Run `uv run mkdocs serve --dev-addr 127.0.0.1:8001` and confirm section pages show intro text and OCRA font renders for h1 headings
