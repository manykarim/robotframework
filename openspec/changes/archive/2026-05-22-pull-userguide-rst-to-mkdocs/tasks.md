## 1. Fetch Script

- [x] 1.1 Create `doc/userguide-mkdocs/scripts/fetch_upstream.py` with git sparse-checkout logic for `doc/userguide/src/`
- [x] 1.2 Add `--ref` CLI flag (default: `master`) to `fetch_upstream.py`
- [x] 1.3 Implement temp-dir clone → copy → cleanup flow (no nested `.git` in repo)
- [x] 1.4 Validate that `doc/userguide/src/` exists in the clone before overwriting local files
- [x] 1.5 Write `.upstream-lock.json` to `doc/userguide-mkdocs/` on success (ref, commit SHA, fetched_at ISO-8601)
- [x] 1.6 Add guard: check git is on PATH, print actionable error and exit non-zero if missing
- [x] 1.7 Verify fetch_upstream.py exits non-zero without modifying local files on any failure

## 2. Pipeline Integration

- [x] 2.1 Add `--skip-fetch` flag to `pipeline.py` argparse (default: False)
- [x] 2.2 Add `--upstream-ref` flag to `pipeline.py` argparse (default: `master`)
- [x] 2.3 Add Stage 0 (FETCH) block in `pipeline.py` that calls `fetch_upstream.py` before the CLEAN stage
- [x] 2.4 Forward `--upstream-ref` value to `fetch_upstream.py` when Stage 0 runs
- [x] 2.5 Skip Stage 0 entirely when `--skip-fetch` is passed; `--upstream-ref` has no effect
- [x] 2.6 Abort pipeline (exit non-zero, skip all subsequent stages) if Stage 0 returns non-zero

## 3. Gitignore & Housekeeping

- [x] 3.1 Add `.upstream-lock.json` to `doc/userguide-mkdocs/.gitignore` (or repo root `.gitignore`) — or confirm it should be committed and document that decision

## 4. Validation

- [x] 4.1 Run `python pipeline.py --skip-fetch` and confirm output is identical to pre-change behavior
- [x] 4.2 Run `python pipeline.py` (with network) and confirm Stage 0 fetches upstream RST and `.upstream-lock.json` is written
- [x] 4.3 Run `python pipeline.py --upstream-ref v7.2` and confirm correct ref is cloned
- [x] 4.4 Simulate git-not-found and confirm error message and non-zero exit without file changes
- [x] 4.5 Confirm full site builds without errors after a fetch + convert run
