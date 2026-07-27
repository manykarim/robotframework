## Why

Readers of the converted manual (pekkaklarck/manual issue #16) repeatedly report that settings, options, keyword/file names have "no syntax highlighting" (items 3, 4, 8, and the architectural asks 22 & 23). The root cause is a single defect: `convert.py` flattens the five semantic RST roles (`:setting:`, `:option:`, `:name:`, `:file:`, `:codesc:` — ~795 occurrences) to class-less `` `code` ``/`*em*`, so the original per-role styling has nothing to target. The `attr_list` Markdown extension is **already enabled** in both `mkdocs.yml` and the manual's `properdocs.yml`, and the original role styling still exists in `doc/userguide/src/userguide.css`. Attaching the role name as a CSS class (via `attr_list`) and porting the original rules restores the visual distinction across the whole manual with one converter change.

## What Changes

- `convert.py` role converters (`convert_custom_roles`, `convert_postfix_roles`) emit `attr_list`-tagged carriers that keep role identity, matching the original styling: `:setting:`/`:name:` → `*text*{.setting}` / `*text*{.name}` (em), `:option:`/`:file:`/`:codesc:` → `` `text`{.option} `` etc. (code). `:opt:` is treated as an `option` alias.
- `convert_option_lists` emits option-list definition-list terms with `{.option}` so `appendix/cli` and `extend/libdoc` terms are role-consistent (and def-list terms carry the class, per the requested "roles on definition lists").
- Port the role block from `doc/userguide/src/userguide.css` into `docs/assets/extra.css` (light + dark) — `.setting` italic+nowrap, `.name` italic, `.file` italic, `.option` nowrap, `.codesc` code — scoped under `.md-typeset`. The same CSS is delivered into the manual's `extra.css`.
- **Restore the original styling 1:1** (italic / monospace / nowrap, no color). Per-role color-coding is explicitly out of scope (a possible follow-up).
- Delivery target is **`pekkaklarck/manual`**, gated by a **mandatory local review of the rendered HTML** built with the manual's own toolchain (properdocs.yml, all plugins) before anything is delivered.

## Capabilities

### New Capabilities

- `rst-role-preservation`: Convert semantic RST roles (and option-list terms) into `attr_list`-classed inline elements and restore the original per-role CSS, so settings/options/names/files render with their intended distinct styling — including inside definition-list terms.
- `roles-change-delivery`: Deliver the regenerated content and CSS to `pekkaklarck/manual` only after a mandatory local review of the rendered HTML (built with the manual's full toolchain).

### Modified Capabilities

## Impact

- `doc/userguide-mkdocs/scripts/convert.py` — role emission + option-term classing
- `doc/userguide-mkdocs/docs/assets/extra.css` — ported role styling (light + dark)
- Regenerated Markdown across the manual (settings/options/names/files now classed)
- Delivery to `pekkaklarck/manual` (PR from `manykarim`, as with the merged PR #3) + the same role CSS added to the manual's `extra.css`
- Resolves issue #16 Group 1 (items 3, 4, 8, 22, 23). Does NOT address the `mkdocs-ezglossary` term-mangling (Group 2) or the link/table fixes (separate changes)
