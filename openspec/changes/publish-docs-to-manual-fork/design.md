## Context

The fork `manykarim/manual` is a straight fork of `pekkaklarck/manual`:

- MkDocs config is `properdocs.yml` (`properdocs` is a mkdocs-compatible fork; `docs_dir: doc/manual/docs`).
- Versioned deploy via `mike`; gh-pages already holds versions `dev`, `0.1`, `0.2`, `0.3` (`latest` → `0.3`). Pages is enabled (source `gh-pages`, live at https://manykarim.github.io/manual/).
- Existing workflows: `dev-docs.yml` (push to `main` → `mike deploy --push dev`) and `release-docs.yml` (version tags → `mike deploy --push --update-aliases <v> latest`).
- Section layout: `syntax/`, `execution/`, `extend/`, `appendix/`, plus generated `api/`, `install/`, `libraries/`.

Build experiments (in a throwaway venv with the fork's `requirements.txt`):

1. Pristine fork: `properdocs build` → **exit 0** (social cards, mkdocstrings, gen-files all work; ~48s).
2. Fork + our content copied via `publish_to_manual.py`: `properdocs build` → **exit 0 but 775 link warnings**. Root cause: our `.md` files contain internal links using **our** names — same-section bare links (`command-line-options.md`), cross-section relative links (`../creating-test-data/test-data-syntax.md`, `../executing-tests/basic-usage.md`, `../extending/creating-test-libraries.md`). The manual uses `cli.md`, `../syntax/data.md`, `../execution/basics.md`, `../extend/libraries.md`.

`mike deploy` accepts `-F properdocs.yml`, so deploys can be driven explicitly.

Per the project's pipeline-first principle ([[feedback_pipeline_approach]]): never hand-edit generated `.md`. The link rewrite is a publish-time transform over copied files, driven by config — not a manual edit, and not a change to our own site (which must keep our names).

## Goals / Non-Goals

**Goals:**
- Internal links in published content resolve under the manual's naming (mapped sections have ~zero broken-link warnings).
- Updated `.md` committed to the fork's `main`.
- Site deployed and live on the fork's gh-pages.
- Rewrite is config-driven and auditable; unmappable links are reported, not hidden.

**Non-Goals:**
- Publishing `getting-started/` and `supporting-tools/index.md` (no manual home) — links to them stay broken and are reported.
- Editing the manual's `properdocs.yml` `nav` (our file set matches the existing nav; no new nav entries needed).
- Reconciling content differences vs upstream — we publish our converted content as-is.
- Changing our own pipeline output or our site's links.

## Decisions

### D1 — Link rewriting in `publish_to_manual.py`, after copy

The copy step already knows the full source→target file map. After copying, rewrite each copied file's Markdown links using two derived lookups:

1. **Section-dir map** (`section_dirs` in JSON): `creating-test-data`→`syntax`, `executing-tests`→`execution`, `extending`→`extend`, `appendices`→`appendix`, `supporting-tools`→`extend`.
2. **Full path map** (existing `files`): resolves exact filename renames (`test-data-syntax.md`→`data.md`, `command-line-options.md`→`cli.md`, …).

Rewrite algorithm for each Markdown link `[text](target)`:
- Split off any `#anchor`; preserve it verbatim.
- Normalize the link path against the **source** file's directory to a docs-root-relative path (e.g. `../creating-test-data/test-data-syntax.md` from `appendices/cli...` → `creating-test-data/test-data-syntax.md`).
- Look up the docs-root-relative path in the `files` map → manual docs-root-relative target (`syntax/data.md`).
- Recompute the relative link from the **target** file's directory (`appendix/`) to the mapped target (`../syntax/data.md`).
- Re-attach the anchor. If the path is not in the map, leave it unchanged and record it for the report.

Only operate on `.md` link targets (skip `http(s)://`, mailto, pure `#anchor`, and image/asset links that already resolve). Apply to inline links `](...)` and reference-style/definition links if present.

Alternative considered: rewrite in the main pipeline. Rejected — our own site uses our names; rewriting there would break our site. The transform is publish-specific.

Alternative considered: a regex blanket replace of section names. Rejected — misses filename renames and would corrupt unrelated text; the map-driven, path-normalized approach is precise.

### D2 — Deploy via the fork's existing `mike` mechanism

Two complementary outcomes: (a) commit `.md` to `main`; (b) publish to gh-pages.

- Push updated content + `properdocs.yml` to the fork's `main`. The existing `dev-docs.yml` then runs `mike deploy --push dev`, publishing to https://manykarim.github.io/manual/dev/.
- For immediate, verifiable publishing the script can also run `mike deploy -F properdocs.yml --push dev` locally (we have `mike` 2.1.3 + `properdocs` 1.6.7 + auth). Deploying `dev` (not `latest`) avoids overwriting the released `0.3`/`latest` version with in-progress converted content.

Alternative considered: deploy to `latest`. Rejected for now — keeps the canonical released version intact; `dev` is the established channel for in-progress content.

### D3 — Fork-targeted push script (generalize, don't fork the script)

Generalize `push_to_manual.sh` to take the target repo and base branch (env vars or args), defaulting to `manykarim/manual` + `main`. For the fork (owned by us) it commits directly to `main` rather than opening a PR. Keep the no-change-exits-clean behavior.

### D4 — `properdocs.yml` URL updates committed to the fork

Set `site_url: https://manykarim.github.io/manual/` and `edit_uri` to the fork's blob path so canonical tags and edit links are correct on the fork's Pages. These live in the fork and are committed there as part of publishing.

## Risks / Trade-offs

- **Residual broken links to unmapped sections** (`getting-started/`, `supporting-tools/index.md`) → Report them in the publish summary; accept as known (those sections aren't published). Mitigate where cheap (e.g. `supporting-tools/libdoc.md` → `extend/libdoc.md`).
- **Anchor mismatches** (e.g. `#fatal`, `#type-hints`) are a separate pre-existing class (slug differences), independent of file-path rewriting → out of scope here; pipeline anchor handling owns it.
- **Overwriting `dev`** on gh-pages → intended; `dev` is the in-progress channel and `latest`/release versions are untouched.
- **Rewrite false positives** (rewriting a code-fence string that looks like a link) → restrict to Markdown link syntax `](...)`; do not touch code-fence contents.
- **properdocs vs mkdocs config discovery** → always pass `-F properdocs.yml` explicitly to `mike`/`properdocs` to avoid defaulting to a missing `mkdocs.yml`.
