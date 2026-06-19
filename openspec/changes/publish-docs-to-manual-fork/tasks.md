## 1. Extend the file map

- [x] 1.1 Add a `section_dirs` object to `manual_file_map.json`: `creating-test-data`→`syntax`, `executing-tests`→`execution`, `extending`→`extend`, `appendices`→`appendix`, `supporting-tools`→`extend`
- [x] 1.2 Add missing `files` entries: `supporting-tools/libdoc.md`→`extend/libdoc.md`, `supporting-tools/ExampleLibrary.png`→`extend/ExampleLibrary.png` (source path corrected — ExampleLibrary.png lives under supporting-tools/, referenced by libdoc.md)

## 2. Add link rewriting to publish_to_manual.py

- [x] 2.1 After copying, load `files` + `section_dirs`; build a docs-root-relative source→target lookup
- [x] 2.2 For each copied `.md`, rewrite inline Markdown links `](target)` whose target is a `.md`: normalize against the source dir to a docs-root-relative path, map it, recompute relative to the target dir, re-attach `#anchor`; skip `http(s)`, `mailto:`, pure `#anchor`, and links inside fenced code blocks (robust CommonMark fence tracking to handle nested fences)
- [x] 2.3 Collect and print unmapped `.md` link targets in the summary; leave them unchanged
- [x] 2.4 Add a `--no-rewrite` flag to allow copy-only behavior

## 3. Generalize the push script for the fork

- [x] 3.1 Update `push_to_manual.sh` to accept target repo + base branch (env/args), defaulting to `manykarim/manual` and `main`
- [x] 3.2 For the fork, commit rewritten content + updated `properdocs.yml` directly to `main` (no PR); keep no-change-exits-clean (`--pr` flag retains the upstream PR flow)
- [x] 3.3 Add an optional `mike deploy -F properdocs.yml --push dev` step (`--deploy` flag) for immediate publishing

## 4. Update the fork's properdocs.yml

- [x] 4.1 Set `site_url: https://manykarim.github.io/manual/` and `edit_uri` to `https://github.com/manykarim/manual/blob/main/doc/manual/docs` — done idempotently in `push_to_manual.sh` (Step 3.5) derived from `MANUAL_REPO`, so it is committed on every publish

## 5. Verify build and deployment

- [x] 5.1 In a venv with the fork's `requirements.txt`, ran `properdocs build -f properdocs.yml` with rewritten content — exit 0; broken-link warnings dropped 775→3 (the 3 are out-of-scope: bare anchor slugs, removed `tidy.md`, `getting-started/`)
- [x] 5.2 Pushed content + updated `properdocs.yml` to fork `main` (commit 0465d24). The fork's `dev-docs.yml` did not auto-trigger (known fork quirk), so deployed directly via `mike deploy -F properdocs.yml --push dev` (exit 0); released versions `0.3`/`latest`/`0.2`/`0.1` left intact; Pages build succeeded
- [x] 5.3 Confirmed https://manykarim.github.io/manual/dev/ → HTTP 200; `extend/libraries/` version section clean (0 broken-link artifacts), `syntax/resource-files/` shows literal `${RESOURCES}/login.resource`, and `appendix/cli/` cross-links resolve to `../../syntax/data/` etc.
