## Why

The MkDocs-based User Guide conversion pipeline exists but currently operates against a locally checked-out RST source. There is no automated way to pull the latest `doc/userguide/src/` content from the upstream robotframework/robotframework repository and run a fresh end-to-end conversion, making it difficult to stay in sync with upstream documentation changes.

## What Changes

- Add a `fetch-upstream` stage to the pipeline that pulls the latest RST source files from the upstream GitHub repository (or the local git worktree) before conversion
- Wire the fetch stage into `pipeline.py` as Stage 0, so a single command (`python pipeline.py`) produces a fully up-to-date MkDocs site from the latest upstream RST
- Provide a `--upstream-ref` CLI flag to target a specific branch, tag, or commit (default: `master`)
- Provide a `--skip-fetch` flag to preserve existing local RST source (current behavior)
- Update validation to verify the fetched RST files match the expected upstream checksum/commit

## Capabilities

### New Capabilities
- `upstream-fetch`: Fetch latest `doc/userguide/src/` RST files from robotframework/robotframework GitHub (via git sparse-checkout or GitHub raw API), making Stage 0 of the pipeline

### Modified Capabilities
- `pipeline-orchestration`: Pipeline gains a Stage 0 (FETCH) before the existing CLEAN → CONVERT → FIX → ASSETS → VALIDATE stages; `--skip-fetch` preserves backward compatibility

## Impact

- `doc/userguide-mkdocs/scripts/pipeline.py` — gains Stage 0 and two new CLI flags
- `doc/userguide-mkdocs/scripts/fetch_upstream.py` — new script for upstream fetch logic
- `doc/userguide/src/` — content is refreshed from upstream (read-only output of Stage 0)
- No changes to conversion fix scripts or MkDocs config
- No breaking changes; `--skip-fetch` restores old behavior exactly
