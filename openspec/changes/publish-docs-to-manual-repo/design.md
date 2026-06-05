## Context

Our pipeline produces MkDocs content under `doc/userguide-mkdocs/docs/` using section names that differ from `pekkaklarck/manual`'s `doc/manual/docs/` structure. The manual is the canonical Robot Framework reference; our pipeline provides a continuously updated, converted version of the same content. The goal is an automated bridge: run pipeline → map files → open PR in the manual repo.

**Section mapping:**

| Our section | Manual section |
|---|---|
| `creating-test-data/` | `syntax/` |
| `executing-tests/` | `execution/` |
| `extending/` | `extend/` |
| `appendices/` | `appendix/` |

**File mapping (selected key renames):**

`creating-test-data/` → `syntax/`:
- `test-data-syntax.md` → `data.md`
- `creating-test-cases.md` → `tests.md`
- `creating-test-suites.md` → `suites.md`
- `creating-user-keywords.md` → `user-keywords.md`
- `variables.md` → `variables.md`
- `variable-files.md` → `variable-files.md`
- `resource-files.md` → `resource-files.md`
- `control-structures.md` → `control.md`
- `advanced-features.md` → `advanced.md`
- `creating-tasks.md` → `tasks.md`
- `using-test-libraries.md` → `libraries.md`
- `index.md` → `index.md`

`executing-tests/` → `execution/`:
- `basic-usage.md` → `basics.md`
- `configuring-execution.md` → `configuration.md`
- `test-execution.md` → `tests.md`
- `task-execution.md` → `tasks.md`
- `output-files.md` → `output-files.md` *(new file — manual has no equivalent yet)*
- `post-processing.md` → `post-processing.md` *(new file)*
- `result-files.md` → `results.md`
- `index.md` → `index.md`
- `*.png`, `*.html` → same relative path under `execution/`

`extending/` → `extend/`:
- `creating-test-libraries.md` → `libraries.md`
- `dynamic-library-api.md` → `dynamic.md`
- `listener-interface.md` → `listeners.md`
- `parser-interface.md` → `parsing.md`
- `remote-library.md` → `remote.md`
- `remote.png` → `remote.png`
- `index.md` → `index.md`

`appendices/` → `appendix/`:
- `command-line-options.md` → `cli.md`
- `available-settings.md` → `settings.md`
- `evaluating-expressions.md` → `expressions.md`
- `registrations.md` → `registrations.md`
- `boolean-arguments.md` → `boolean-arguments.md` *(new file)*
- `time-format.md` → `time-format.md`
- `translations.md` → `translations.md`
- `documentation-formatting.md` → `doc-format.md`
- `index.md` → `index.md`

## Goals / Non-Goals

**Goals:**
- Fully automate PR creation from our pipeline output into `pekkaklarck/manual`.
- Apply section and file renames via a static JSON mapping (auditable, easy to update).
- Copy images alongside their parent `.md` files to the same target directory.
- Leave manual-only files (`extend/models.md`, `extend/json.md`, `extend/xml.md`, `libraries/`, `install/`, `api/`, `glossary.md`) untouched.

**Non-Goals:**
- Content reconciliation — we copy our content as-is; diff review happens in the PR.
- Updating `properdocs.yml` nav in the manual repo — if new files are added, that is a follow-up manual step.
- Publishing `getting-started/` or `supporting-tools/` (no agreed mapping to the manual structure).

## Decisions

**Static JSON mapping file, not a glob-based section copy**

A glob copy would silently drop files the manual doesn't expect and create naming mismatches. An explicit mapping (`manual_file_map.json`) makes every filename decision visible and version-controlled. New files require a conscious mapping entry.

**Workflow runs pipeline first, then publishes**

The publish step reads from `doc/userguide-mkdocs/docs/` (the pipeline output already committed in the repo). The pipeline is run at the start of the workflow to ensure the content is current with upstream RST. If the pipeline fails the publish step is skipped.

**PR via `gh pr create`, not direct push**

Content in `pekkaklarck/manual` is the canonical reference; changes should be reviewed. A PR also gives a clear audit trail of which pipeline run produced each update.

**`GH_MANUAL_TOKEN` personal access token secret**

The default `GITHUB_TOKEN` scoped to `manykarim/robotframework` cannot write to a different repository. A PAT with `repo` scope on `pekkaklarck/manual` stored as `GH_MANUAL_TOKEN` is required. The workflow uses this token to clone the manual repo and push the PR branch.

**Images are copied to the same target section directory**

The manual doesn't have a separate `/assets/images/` convention for inline images. Placing images alongside their section `.md` files matches the manual's existing asset layout.

## Risks / Trade-offs

- **Nav drift**: If we add new pages that need nav entries in `properdocs.yml`, those won't be added automatically. → Accept; document as a manual follow-up step in the PR description.
- **Merge conflicts**: If pekkaklarck/manual has diverged significantly on a file, the PR will show conflicts. → Accept; the PR review step is the right place to resolve these.
- **Secret rotation**: `GH_MANUAL_TOKEN` expires or is revoked. → The workflow will fail loudly on the push step; standard PAT maintenance.
- **Files only in manual**: Our publish script does not delete files in the target sections that have no counterpart in our mapping (e.g. `extend/models.md`). → Safe default; deletions should be intentional.
