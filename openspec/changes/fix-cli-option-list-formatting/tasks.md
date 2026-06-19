## 1. Implement option-list conversion in convert.py

- [x] 1.1 Add `convert_option_lists(self, content: str) -> str`: line-based, fence-aware (robust CommonMark fence tracking) pass that detects option-list blocks (≥2 option entries) and emits `def_list` term/definition pairs
- [x] 1.2 Option-line regex: consistent block indent + comma-separated `-{1,2}[A-Za-z][\w-]*` tokens + optional ` <[^>]+>` arg, then either `\s{2,}` + description (same-line) or end-of-line (next-line style); continuation = lines indented deeper than option indent
- [x] 1.3 For each entry, join same-line + continuation description into one definition; render `` `<spec>` `` then `:   <description>` at column 0, with blank-line separation
- [x] 1.4 Call `convert_option_lists()` in `convert_file()` after `convert_literal_blocks()` and before `convert_cross_references()`

## 2. Regenerate and verify locally

- [x] 2.1 Run `python scripts/pipeline.py --skip-fetch` from `doc/userguide-mkdocs/`; confirm it completes without new errors
- [x] 2.2 Inspect `docs/appendices/command-line-options.md`: both option blocks are term/definition pairs; env-vars def list unchanged; no option-like lines left as raw indented text
- [x] 2.3 Inspect `docs/supporting-tools/libdoc.md`: next-line-style options converted correctly
- [x] 2.4 Confirm command examples in code blocks (e.g. BasicUsage `--test Example*`, Variables `--variable HOST:...`) are NOT converted
- [x] 2.5 Run `uv run mkdocs build --strict`; confirm exit 0; serve locally and visually confirm `appendix/cli` renders as a definition list

## 3. Republish to the fork and verify live

- [x] 3.1 Run `bash doc/userguide-mkdocs/scripts/push_to_manual.sh --skip-pipeline --deploy` (or push + deploy) to publish the regenerated content to `manykarim/manual`
- [x] 3.2 Confirm https://manykarim.github.io/manual/dev/appendix/cli/ renders the options as a proper definition list and https://manykarim.github.io/manual/dev/extend/libdoc/ likewise
