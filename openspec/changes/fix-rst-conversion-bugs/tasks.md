## 1. Fix anonymous reference backtick pattern in convert.py

- [x] 1.1 In `_resolve_anonymous_references()`, change `backtick_pattern` from `r'`([^`]+)`__'` to `r'(?<![`\w])`([^`]+)`__'` to add a lookbehind that prevents matching from a closing code-span backtick

## 2. Remove arithmatex from mkdocs.yml

- [x] 2.1 Delete the `pymdownx.arithmatex` block (2 lines: the key and `generic: true` indented value) from `doc/userguide-mkdocs/mkdocs.yml`

## 3. Pipeline regeneration and verification

- [x] 3.1 Run `python scripts/pipeline.py --skip-fetch` from `doc/userguide-mkdocs/` and confirm it completes without new errors
- [x] 3.2 Inspect `docs/extending/creating-test-libraries.md` around the "Library version" section — confirm `__version__` appears as plain text with no `](http://...)version__` artifacts
- [x] 3.3 Inspect `docs/creating-test-data/resource-files.md` line ~27 — confirm `${RESOURCES}/login.resource` is still present as-is (not mangled by converter)
- [x] 3.4 Run `uv run mkdocs build --strict` and confirm exit code 0
