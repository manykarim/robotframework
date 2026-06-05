## 1. Create the file mapping config

- [x] 1.1 Create `doc/userguide-mkdocs/scripts/manual_file_map.json` with the full section and file mapping for all 4 sections (`creating-test-data`→`syntax`, `executing-tests`→`execution`, `extending`→`extend`, `appendices`→`appendix`), including all per-file renames and image files

## 2. Create the publish script

- [x] 2.1 Create `doc/userguide-mkdocs/scripts/publish_to_manual.py` that reads `manual_file_map.json`, accepts a `--manual-dir` argument pointing to a local checkout of `pekkaklarck/manual`, and copies each mapped source file to its target path (creating directories as needed)
- [x] 2.2 The script SHALL log a warning (not error) for source files in the mapping whose source path does not exist
- [x] 2.3 The script SHALL print a summary of files copied and files skipped

## 3. Create the local push script (replaces GH Actions workflow — manual execution from this machine)

- [x] 3.1 Create `doc/userguide-mkdocs/scripts/push_to_manual.sh` — clones manual repo, runs pipeline (optional), runs publish script, creates branch `auto-update-YYYY-MM-DD-<sha>`, commits, pushes, opens PR via `gh pr create`
- [x] 3.2 Pipeline step runs `python pipeline.py --skip-fetch`; skip with `--skip-pipeline` flag
- [x] 3.3 Script detects no-change case and exits cleanly without opening a PR
- [x] 3.4 Script requires `gh` CLI authenticated with repo scope on `pekkaklarck/manual`

## 4. Verification

- [x] 4.1 Run `python publish_to_manual.py --manual-dir /tmp/manual-test` locally against a fresh clone of `pekkaklarck/manual` and confirm the 4 sections are populated with correctly renamed files
- [x] 4.2 Confirm that manual-only files (`extend/models.md`, etc.) are untouched after the script runs
