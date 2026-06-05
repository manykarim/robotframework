## Why

The converted MkDocs content lives only in this repo and must be manually copied to `pekkaklarck/manual` whenever it changes. Automating a PR from our pipeline output to that repo closes the feedback loop and makes every docs change reviewable before it lands in the canonical manual.

## What Changes

- New script `doc/userguide-mkdocs/scripts/publish_to_manual.py` that reads a static file-mapping config and copies generated `.md` and image files from our section structure to the corresponding paths in a local checkout of `pekkaklarck/manual`.
- New mapping config `doc/userguide-mkdocs/scripts/manual_file_map.json` defining the section-level and file-level renames (e.g. `creating-test-data/test-data-syntax.md` → `syntax/data.md`).
- New GitHub Actions workflow `.github/workflows/publish-to-manual.yml` that runs on master push (docs-touching commits) and `workflow_dispatch`, executes the pipeline, runs the publish script against a checkout of `pekkaklarck/manual`, and opens a PR there with the generated content.
- The 4 sections in scope: `syntax` (from `creating-test-data`), `execution` (from `executing-tests`), `extend` (from `extending`), `appendix` (from `appendices`).

## Capabilities

### New Capabilities

- `cross-repo-docs-publish`: Automated PR creation from our pipeline output into `pekkaklarck/manual`, including section/file name mapping, image copying, and GitHub Actions orchestration.

### Modified Capabilities

<!-- No existing spec-level requirements change. -->

## Impact

- `doc/userguide-mkdocs/scripts/publish_to_manual.py` — new file
- `doc/userguide-mkdocs/scripts/manual_file_map.json` — new file
- `.github/workflows/publish-to-manual.yml` — new workflow
- Requires a `GH_MANUAL_TOKEN` repository secret with write access to `pekkaklarck/manual`
- No changes to the pipeline itself, existing workflows, or the MkDocs site
