## Why

RST **option lists** (e.g. `  -F, --extension <value>  Parse only these files...`) are passed through the converter verbatim. With only 2-space indentation they are neither a code block nor a recognized structure, so MkDocs renders them as one collapsed run-on paragraph instead of the two-column option list the original renders (https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#command-line-options vs the broken https://manykarim.github.io/manual/dev/appendix/cli/). The converter has no option-list handling.

## What Changes

- Add a `convert_option_lists()` pass to `convert.py` that detects RST option-list blocks and converts each entry to MkDocs `def_list` syntax (option spec as the term, description as the definition), so they render as proper option/description lists.
- Handle both option-list styles: description on the **same line** as the option, and description starting on the **following indented line(s)** (as in Libdoc). Multi-line descriptions are joined into one definition.
- Run the pass **after** code/literal-block conversion and **skip fenced regions**, so command-line examples inside code blocks (e.g. `--variable HOST:...`, `--test Example*`) are not mis-detected as option lists. Run it **before** cross-reference conversion so links inside descriptions still resolve.
- Regenerate via the pipeline, verify the affected pages build and render, and republish to the fork so the live `appendix/cli/` page is correctly formatted.

## Capabilities

### New Capabilities

- `rst-option-list-conversion`: Convert RST option-list blocks to MkDocs `def_list` definition lists, supporting same-line and next-line descriptions, multi-line wrapping, comma-separated options, and `<arg>` syntax containing `|`/`:`; code-fence content is never converted.

### Modified Capabilities

## Impact

- `doc/userguide-mkdocs/scripts/convert.py` — new `convert_option_lists()` method + call in `convert_file`
- Regenerated pages with option lists: `appendices/command-line-options.md`, `supporting-tools/libdoc.md`, and others using option lists (testdoc, result-files, etc.)
- Republish to `manykarim/manual` so the live `appendix/cli/` and `extend/libdoc/` pages render correctly
- `def_list` is already enabled in both our `mkdocs.yml` and the fork's `properdocs.yml`
