## 1. Converter — token accumulation

- [x] 1.1 In `_parse_grid_table_v2()`, replace the `current_row` list of strings with a list of token lists: `current_row = [[] for _ in range(len(col_positions) - 1)]`
- [x] 1.2 Replace the cell-content append block (lines ~796–800) with token-aware logic:
  - Empty `cell_content` → append `('blank', '')` if the cell already has content
  - `cell_content` starting with `* ` → append `('bullet', cell_content[2:].strip())`
  - Otherwise: if last token is `bullet` → extend that bullet's text (continuation); if last token is `text` → extend that text; else → append `('text', cell_content)`

## 2. Converter — rich cell renderer

- [x] 2.1 Add `_render_rich_cell(self, tokens: list) -> str` method to the converter class:
  - If `tokens` contains no `blank` or `bullet` tokens → return plain text (join `text` tokens with space, same as current behaviour)
  - Otherwise: split token list at `blank` boundaries into segments; for each segment render all-bullet → `<ul><li>…</li></ul>`, mixed/text → plain string; join rendered segments with `<br>`
- [x] 2.2 In `_parse_grid_table_v2()`, call `_render_rich_cell(cell_tokens)` when building each row's cells instead of using `cell.strip()` directly

## 3. Pipeline regeneration

- [x] 3.1 Run `python scripts/pipeline.py --skip-fetch` from `doc/userguide-mkdocs/` and confirm it completes without new errors
- [x] 3.2 Inspect `docs/extending/listener-interface.md` — the `start_keyword` cell should contain `<ul><li>` elements for "Shared attributes" and each per-type section
- [x] 3.3 Run `uv run mkdocs build --strict` and confirm exit code 0

## 4. Verification

- [x] 4.1 Serve locally (`uv run mkdocs serve --dev-addr 127.0.0.1:8001`) and open `http://127.0.0.1:8001/robotframework/latest/extending/listener-interface/` — confirm bullet lists render as visual lists and paragraph breaks appear between sections
- [x] 4.2 Compare rendered output against reference at `https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#listener-interface-versions` to confirm structural parity
