## Why

Two converter bugs corrupt the rendered Robot Framework documentation: RST anonymous reference resolution falsely matches Python dunder attribute names (e.g., `__version__`) producing broken Markdown link syntax, and MkDocs `pymdownx.arithmatex` with `generic: true` interprets Robot Framework variable syntax `${VAR}` as LaTeX math expressions, rendering paths like `${RESOURCES}/login.resource` as `\({RESOURCES}/login.resource`.

## What Changes

- Fix `_resolve_anonymous_references()` in `convert.py` to add a lookbehind assertion on the backtick pattern so it cannot start from a closing code-span backtick
- Remove `pymdownx.arithmatex` from `mkdocs.yml` (RF documentation contains no mathematical notation; the extension conflicts with the ubiquitous `${...}` variable syntax)
- Regenerate affected files via pipeline

## Capabilities

### New Capabilities

- `anonymous-ref-resolution`: Correct resolution of RST anonymous hyperlink references (`text`__ and word__) that doesn't false-match dunder identifiers inside inline code spans
- `variable-path-rendering`: RF variable syntax (`${VAR}`) in non-code prose renders as literal text without math-mode transformation

### Modified Capabilities

## Impact

- `doc/userguide-mkdocs/scripts/convert.py`: one-line pattern change in `_resolve_anonymous_references`
- `doc/userguide-mkdocs/mkdocs.yml`: remove `pymdownx.arithmatex` block
- Regenerated: `docs/extending/creating-test-libraries.md`, `docs/creating-test-data/resource-files.md`, and any other file containing anonymous refs or `${...}` in prose
