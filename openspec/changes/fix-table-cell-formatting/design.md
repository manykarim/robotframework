## Context

`convert.py:_parse_grid_table_v2()` (lines 749–820) handles RST grid tables. When it encounters a content line inside a cell, it appends with a space (line 798: `current_row[col_idx] += ' ' + cell_content`). Three structural signals are silently discarded:

1. **Blank intra-cell lines** — RST rows where all column slots are empty whitespace (e.g. `|   |   |   |`). These are paragraph breaks between sections.
2. **Bullet list items** — lines whose cell content starts with `* `. These must become `<li>` elements.
3. **Bullet continuations** — plain-text lines that follow a `* ` item and are indented in RST (continuation of the same bullet). Currently indistinguishable from regular text after stripping.

Affected RST files: `ListenerInterface.rst` (107 bullet lines, 85 blank separators), `RemoteLibrary.rst` (3 bullets), `TestDataSyntax.rst` (6 bullets).

Standard GFM pipe tables do not support multi-line cell content or block elements. MkDocs Material renders inline HTML inside pipe-table cells, so the output format is HTML-enriched strings within pipe-table cells.

## Goals / Non-Goals

**Goals:**
- Bullet lists inside grid table cells render as `<ul><li>` in the output
- Paragraph breaks inside grid table cells produce visible separation (`<br><br>`)
- Bullet continuations are joined to their parent bullet, not treated as new paragraphs
- Cells with no bullets or multiple paragraphs continue to render as plain text (no regression)

**Non-Goals:**
- Supporting nested bullet lists (none present in the RST source)
- Supporting numbered lists inside cells (none present in the RST source)
- Restructuring the table layout (the tables remain pipe tables)

## Decisions

### D1 — Token-based cell accumulation

Replace the single-string accumulation with a token list per cell. Token types:

| Token | Trigger | Meaning |
|---|---|---|
| `text` | any non-empty, non-bullet line | Regular paragraph text |
| `blank` | empty cell slot (after stripping) | Paragraph break |
| `bullet` | cell content starts with `* ` | Bullet list item |

Continuation lines (plain text after a bullet token, before the next blank) are detected by checking whether the last token is a `bullet` — they are appended to that token rather than added as a new `text` token.

Alternative considered: store cell as raw string with sentinel characters. Rejected — harder to read and test.

### D2 — HTML rendering in `_render_rich_cell()`

Token list is rendered as an HTML-enriched string:

1. Split tokens at `blank` boundaries to get **segments**.
2. Each segment is rendered:
   - All-bullet segment → `<ul><li>item</li>…</ul>`
   - Mixed segment (text followed by bullets or vice-versa): split at first bullet token; text part becomes a plain string, bullets become `<ul>`.
   - All-text segment → plain string (joined with space).
3. Rendered segments are joined with `<br>`.

Single `<br>` (not `<br><br>`) is used because table cells already have compact spacing; double breaks would inflate row height unnecessarily.

Alternative: output HTML tables (`<table>` + `<td markdown="1">`). Rejected — produces larger diffs, breaks diff readability, and is harder to maintain. Inline HTML in pipe cells is simpler and already validated by MkDocs Material.

### D3 — No change to cells with only plain text

When a cell accumulates only `text` tokens and no `blank` or `bullet` tokens, `_render_rich_cell()` returns the tokens joined with spaces — identical to the current behaviour. Zero regression risk for the ~95% of table cells that are plain text.

## Risks / Trade-offs

- **HTML in source** — The generated `.md` files will contain inline `<ul>` tags. This is intentional and consistent with the existing inline HTML used elsewhere in the generated output.
- **MkDocs strict mode** — Inline HTML in pipe tables is valid and passes `mkdocs build --strict`. Verified against MkDocs Material 9.x.
- **Bullet detection heuristic** — Only `* ` (asterisk + space) is treated as a bullet. RST also supports `-` and `+` as bullet markers, but none appear in the affected files. A follow-up can extend the pattern if needed.
