## Why

Definition lists in the converted MkDocs docs have a blank line between consecutive term–definition pairs. Python-Markdown's `def_list` extension treats blank-separated items as "loose" lists and wraps each definition in a `<p>` tag, producing unwanted vertical space between entries. The result is that attribute tables like the test-case settings list feel double-spaced and hard to scan. Removing those inter-item blank lines produces compact ("tight") rendering with no `<p>` wrappers, matching the intent of the original RST source.

## What Changes

- `doc/userguide-mkdocs/scripts/fix_definition_lists.py` gains a new post-processing pass that removes blank lines between consecutive definition list items (sequences of `term → : definition` pairs separated only by a blank line).
- The fix is applied to all Markdown files under `docs/` via the existing pipeline.
- Approximately 54 affected items across the converted docs.

## Capabilities

### New Capabilities

<!-- None — this is a pipeline/rendering fix, no new user-facing capability. -->

### Modified Capabilities

- `pipeline-orchestration`: The definition-list fix script gains a new compaction pass; the pipeline already calls this script.

## Impact

- `doc/userguide-mkdocs/scripts/fix_definition_lists.py` — new function added.
- All `docs/**/*.md` files that contain loose definition lists are regenerated/fixed.
- No changes to `mkdocs.yml`, RST source, or any other script.
