## Why

The converted MkDocs content must be published to the fork `manykarim/manual` and go live on its GitHub Pages site (https://manykarim.github.io/manual/). Today our `publish_to_manual.py` only copies files into a `pekkaklarck/manual` checkout for a PR, and the copied content keeps **our** section/file names in its internal links (`creating-test-data/test-data-syntax.md`, `command-line-options.md`). A build experiment against the fork produced **775 broken-link warnings** because the manual uses different names (`syntax/data.md`, `cli.md`). Publishing as-is would put a link-broken site live.

## What Changes

- Extend `manual_file_map.json` with a `section_dirs` map (our section → manual section) and the few missing entries needed by the fork (`supporting-tools/libdoc.md` → `extend/libdoc.md`, `extending/ExampleLibrary.png` → `extend/ExampleLibrary.png`).
- Add an internal-link rewriting pass to `publish_to_manual.py` that, after copying, rewrites cross-file Markdown links in the copied files from our naming to the manual's naming (preserving `#anchors`), so the published site has working internal navigation. Links to sections with no manual home (`getting-started/`, `supporting-tools/index.md`) are reported, not silently dropped.
- Generalize the push script to target the fork: new/updated script that clones `manykarim/manual`, runs the publish+rewrite, commits the updated `.md` to `main`, and pushes — the fork's existing `dev-docs.yml` then deploys via `mike deploy --push dev`. The script can also run `mike deploy -F properdocs.yml --push` directly for immediate verification.
- Update the fork's `properdocs.yml` `site_url` and `edit_uri` to point at `manykarim` so canonical URLs and "edit" links resolve on the fork's Pages site.
- Verify a clean local `properdocs build` (mapped-section broken links eliminated) and confirm the live gh-pages deployment.

## Capabilities

### New Capabilities

- `manual-link-rewriting`: Rewrite internal cross-file Markdown links in published content from our section/file naming to the manual's naming, driven by the file map, preserving anchors and reporting unmappable targets.
- `fork-docs-deploy`: Publish converted docs to the `manykarim/manual` fork (committed to `main`) and deploy them to its GitHub Pages site via `mike`.

### Modified Capabilities

## Impact

- `doc/userguide-mkdocs/scripts/manual_file_map.json` — add `section_dirs` + missing file entries
- `doc/userguide-mkdocs/scripts/publish_to_manual.py` — add link-rewriting pass
- `doc/userguide-mkdocs/scripts/push_to_manual.sh` (or a fork variant) — target `manykarim/manual`, push to `main`, optional direct `mike deploy`
- In the fork: `properdocs.yml` `site_url`/`edit_uri` updated; `doc/manual/docs/**` content updated
- Uses authenticated `gh` (account `manykarim`, scopes `repo`+`workflow`); fork Pages already enabled on `gh-pages`
