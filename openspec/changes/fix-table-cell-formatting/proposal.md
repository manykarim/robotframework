## Why

RST grid table cells that contain multiple paragraphs and/or bullet lists are collapsed into a single run-on line in the converted Markdown. The converter's `_parse_grid_table_v2()` joins every continuation cell line with a single space, stripping paragraph breaks and bullet list markers. The result is dense, unreadable cells — most visibly in `extending/listener-interface.md` where the `start_keyword` description loses dozens of `* attribute:` bullets and all section headers.

Reference comparison:
- Broken: https://manykarim.github.io/robotframework/dev/extending/listener-interface
- Expected: https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#listener-interface-versions

## What Changes

- `convert.py` `_parse_grid_table_v2()` accumulates cell lines as structured tokens (text / blank / bullet) instead of joining them with spaces
- New `_render_rich_cell()` helper on the converter class converts the token list to an HTML-enriched string: `<br><br>` between paragraphs, `<ul><li>…</li></ul>` for bullet groups
- Pipeline re-run regenerates the three affected Markdown files: `extending/listener-interface.md`, `extending/remote-library.md`, `creating-test-data/test-data-syntax.md`

## Capabilities

### New Capabilities

- `rich-table-cell-rendering`: Grid table cells with multi-paragraph content and RST bullet lists are faithfully rendered in the output Markdown

### Modified Capabilities

(none)

## Impact

- `doc/userguide-mkdocs/scripts/convert.py` — `_parse_grid_table_v2()` and new `_render_rich_cell()` method
- Three generated Markdown files (regenerated via pipeline, not hand-edited)
- No API, dependency, or navigation changes
