## Why

The MkDocs site renders a language label ("Robot Framework", "Bash", "Text Only", etc.) above every code block because `auto_title: true` is set in the `pymdownx.highlight` configuration. These labels are noisy and redundant — the syntax highlighting already makes the language obvious — and they clutter the visual presentation of every code sample in the guide.

## What Changes

- Remove `auto_title: true` from the `pymdownx.highlight` block in `doc/userguide-mkdocs/mkdocs.yml` (set to `false` or delete the line).

## Capabilities

### New Capabilities

<!-- None — this is a pure visual fix with no new functionality. -->

### Modified Capabilities

<!-- No spec-level requirement changes. -->

## Impact

- `doc/userguide-mkdocs/mkdocs.yml` — one line change.
- All rendered code blocks across the entire MkDocs site will no longer show a language title bar.
- No changes to Markdown source files, the pipeline, or any other configuration.
