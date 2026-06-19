## Context

The RST→Markdown converter (`convert.py`) resolves RST anonymous hyperlink references (`` `text`__ `` and `word__`) in `_resolve_anonymous_references()`. The backtick pattern `r'`([^`]+)`__'` finds all occurrences of a backtick-delimited span immediately followed by `__`. In the RST source, Python dunder attribute names like `` `__version__` `` appear as single-backtick interpreted text. After earlier conversion steps run (which leave single-backtick spans intact), the pattern can match the CLOSING backtick of one code span followed by intervening prose and the OPENING backtick of `` `__version__` `` — because that opening backtick is immediately followed by `__`. This creates multi-line false matches that produce garbled Markdown link syntax (e.g., `[does not exist...](http://url)version__`).

Separately, `mkdocs.yml` enables `pymdownx.arithmatex` with `generic: true`. This extension intercepts `${...}` in Markdown prose and converts it to LaTeX math notation (`\(...\)`). Robot Framework's ubiquitous variable syntax `${VARIABLE_NAME}` is indistinguishable from generic LaTeX math delimiters, so any RF variable appearing in italic or plain prose (not inside a code fence) gets mangled.

## Goals / Non-Goals

**Goals:**
- Fix false anonymous reference matches caused by dunder names in single-backtick spans
- Prevent arithmatex from mangling RF variable syntax in prose
- Both fixes go in the source scripts (pipeline-first; no direct edits to generated `.md` files)

**Non-Goals:**
- Handling nested bullet lists or numbered lists in RST (no such content present)
- Adding math rendering capability to the RF docs (no mathematical notation used)
- Fixing other potential false-positive anonymous ref patterns beyond the dunder case

## Decisions

### D1 — Lookbehind on backtick anonymous reference pattern

The backtick pattern in `_resolve_anonymous_references` changes from:
```python
backtick_pattern = r'`([^`]+)`__'
```
to:
```python
backtick_pattern = r'(?<![`\w])`([^`]+)`__'
```

The lookbehind `(?<![`\w])` asserts that the opening backtick is NOT preceded by a backtick or word character. A backtick preceded by a word character is a CLOSING backtick (e.g., the `` ` `` at the end of `ROBOT_LIBRARY_VERSION\``), never an opening one. This precisely excludes all false matches while preserving all legitimate anonymous references, which always begin at a word boundary (after whitespace or punctuation).

Alternative considered: Require the captured text not to start with whitespace (to exclude ` does not exist...`). Rejected — a whitespace check is a symptom test; the lookbehind is the true structural fix.

Alternative considered: Protect `` `__name__` `` spans before anonymous ref resolution. Rejected — more invasive and requires a second pass to restore protected spans.

### D2 — Remove arithmatex from mkdocs.yml

Delete the `pymdownx.arithmatex` block from `mkdocs.yml`. The Robot Framework user guide contains no mathematical expressions; the extension provides no value and actively corrupts RF variable syntax. Removing it is zero-risk for this documentation site.

Alternative considered: Configure arithmatex to use only `\(...\)` / `\[...\]` delimiters (no `$` sign). This would require confirming the arithmatex `block_start_re` / `inline_start_re` config options and still leaves the generic `${` pattern exposed. Simpler to remove entirely.

Alternative considered: Escape `${` to `\${` in `convert.py` for non-code prose. Rejected — requires a new regex pass over the content, adds complexity, and the root cause is an unnecessary extension rather than a converter gap.

## Risks / Trade-offs

- **Lookbehind correctness**: The `(?<![`\w])` lookbehind uses a character class that must be verified against Python's `re` module (which supports fixed-width lookbehinds). Both `` ` `` and `\w` are single characters, so the lookbehind is valid.
- **Removing arithmatex**: If future docs content needs math, arithmatex would need to be re-added with safe delimiters (`\(...\)` only). The change is easily reversible.
- **Pipeline regeneration**: Multiple files will change after the fix; all need to be verified for correctness (no new broken links, correct `${...}` rendering).
