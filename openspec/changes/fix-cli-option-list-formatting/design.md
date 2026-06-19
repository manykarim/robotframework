## Context

`convert.py:convert_file()` applies conversion steps in order (lines 1403–1417). RST option lists appear in `CommandLineOptions.rst` (107 entries in two blocks), `Libdoc.rst`, `Testdoc.rst`, and a few execution pages. docutils renders an option list as a two-column table (option | description). Our converter has no handler, so the 2-space-indented block falls through to MkDocs as plain text and collapses.

Two RST option-list styles exist in the sources:

1. **Same-line description** (CommandLineOptions):
   ```
     -F, --extension <value>  Parse only these files when executing a directory.
     -N, --name <name>       Sets the name of the top-level test suite.
   ```
2. **Next-line description** (Libdoc), often mixed with style 1 in the same block:
   ```
     -f, --format <html|xml|json|libspec>
                              Specifies whether to generate an HTML output...
     -N, --name <newname>     Sets the name of the documented library or resource.
   ```

Descriptions wrap across multiple indented continuation lines. Option args frequently contain `|` and `:` (e.g. `<all|passed|name:pattern|...>`).

The env-vars section in the same file is a *different* RST construct (already converted correctly to `def_list` by `fix_definition_lists.py`) and must be left alone.

False positives: command examples like `--variable HOST:10.0.0.2:1234`, `--test Example*  # comment` live inside `::`/`.. sourcecode::` blocks. After `convert_code_blocks`/`convert_literal_blocks` these are fenced; the new pass must skip fenced regions.

`def_list` is enabled in both `mkdocs.yml` and the fork's `properdocs.yml`. Per the pipeline-first principle ([[feedback_pipeline_approach]]), the fix lives in `convert.py`, not in generated `.md`.

## Goals / Non-Goals

**Goals:**
- RST option lists render as structured option/description lists (`def_list`), matching the original's two-column intent.
- Support same-line and next-line descriptions, multi-line wrapping, comma-separated options, and `<arg>` with `|`/`:`.
- Never convert content inside fenced code blocks.
- Links/roles inside descriptions still convert (run before cross-reference conversion).
- No regression to the env-vars definition list or to bullet lists.

**Non-Goals:**
- Reproducing docutils' exact `<table class="option-list">` HTML (a `def_list` is the accepted Markdown equivalent).
- Fixing unrelated link artifacts on the CLI page (e.g. stray `_` from embedded-target refs) — separate concern.
- Supporting nested option lists (none exist).

## Decisions

### D1 — Render option lists as `def_list`

Each option entry becomes:
```
`-F, --extension <value>`
:   Parse only these files when executing a directory.
```
Term = the full option spec wrapped in backticks (inline code). Definition = the description, with continuation lines joined by spaces into a single `:   ` line. Consecutive entries form one `<dl>`.

Rationale over a pipe table: `|` in `<arg>` would break table columns and need escaping; multi-line descriptions need `<br>`. `def_list` handles both natively and reads like the original. The user explicitly accepted a definition list.

### D2 — Detection: a new `convert_option_lists()` run after fences, before cross-refs

Placement in `convert_file`: after `convert_literal_blocks` (so code/literal blocks are fenced) and before `convert_cross_references` (so description links convert).

Algorithm (line-based, fence-aware):
- Track fenced regions (``` / ~~~, robust CommonMark closer rule) and never process lines inside them.
- An **option line** matches, at a consistent block indent: one or more comma-separated option tokens, each `-{1,2}[A-Za-z][\w-]*`, an optional ` <arg>` where arg is `[^>]+`, then either (a) `\s{2,}` + description text (style 1), or (b) end of line (style 2).
- A **continuation/description line** is indented strictly deeper than the option indent and is non-blank.
- A block = a run of ≥2 option lines (plus their continuations). Require ≥2 to avoid false positives. For each option line, gather its same-line description (if any) and all following continuation lines up to the next option line / block end; join into one definition string.
- Emit `` `<spec>` `` then `:   <description>` for each entry, at column 0, with a blank line separating the block from surrounding content.

### D3 — Idempotency and safety

- Skip blocks already in `def_list` form. The pass only triggers on the raw indented RST option pattern, which no longer exists after conversion, so re-running is a no-op.
- Bullet lists (`- item`, single space) never match (option token requires no space between `-` and letter; description requires `\s{2,}` or next-line indent).

## Risks / Trade-offs

- **Mis-detection of a non-option indented block** → Mitigated by the ≥2-entry rule, the strict option-token regex, and fence-skipping. Each affected file is verified by build + visual spot check.
- **Long single-line definitions** after joining wrapped text → Acceptable; Markdown/`def_list` handle long lines fine.
- **A real option list with only one entry** would be skipped → None observed; acceptable, and such a singleton still renders as readable text.
- **Description containing a literal `:`** (e.g. "separated with a colon (:)") → Fine; only the leading `:   ` marker is structural.
