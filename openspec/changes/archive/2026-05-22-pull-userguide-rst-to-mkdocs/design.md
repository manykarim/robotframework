## Context

The Robot Framework User Guide lives as RST source in `doc/userguide/src/` (relative to the repo root). A comprehensive conversion pipeline in `doc/userguide-mkdocs/scripts/pipeline.py` converts that RST to MkDocs-flavoured Markdown and builds a full static site. The pipeline currently assumes the RST source is already present locally; there is no automated way to refresh it from upstream before running the conversion.

The upstream repository is `https://github.com/robotframework/robotframework`. The RST source is stable in structure (same paths across commits) but its content evolves with each Robot Framework release.

## Goals / Non-Goals

**Goals:**
- Add a Stage 0 (FETCH) to `pipeline.py` that downloads the latest RST source from the upstream GitHub repo before conversion
- Support targeting a specific branch/tag/commit via `--upstream-ref` (default: `master`)
- Preserve full backward compatibility with `--skip-fetch`
- Encapsulate fetch logic in a standalone `fetch_upstream.py` script usable outside the pipeline
- Log the upstream commit SHA that was fetched so the output is reproducible

**Non-Goals:**
- Pushing conversion output back to any remote
- Continuous integration / cron scheduling (out of scope for this change)
- Supporting non-GitHub upstreams (only robotframework/robotframework)
- Modifying any conversion or post-processing fix scripts

## Decisions

### D1: git sparse-checkout over GitHub raw API

**Decision**: Use `git clone --filter=blob:none --sparse --depth=1` to fetch only `doc/userguide/src/` from upstream.

**Rationale**: A raw API approach requires enumerating every file with multiple HTTP requests and is fragile if the directory tree changes. Sparse checkout gives us a full directory tree in one command, is reproducible, and uses standard tooling (git) already required by the project.

**Alternative considered**: `gh` CLI or `requests` against the GitHub REST API. Rejected because it adds a dependency (gh CLI or requests library) and requires authentication for private or high-traffic repos.

### D2: Fetch into a temporary directory, then rsync into place

**Decision**: Clone into a system temp dir, then copy `doc/userguide/src/` to the repo path, then remove the temp clone.

**Rationale**: Avoids polluting the repo with a nested `.git` directory or partial state if the fetch is interrupted.

### D3: Record upstream commit SHA in a lockfile

**Decision**: After fetch, write `.upstream-lock.json` into `doc/userguide-mkdocs/` with `{"ref": "<ref>", "commit": "<sha>", "fetched_at": "<iso8601>"}`.

**Rationale**: Makes conversion output reproducible and aids debugging when conversion breaks after an upstream content change.

### D4: `--skip-fetch` defaults to False (fetch runs by default)

**Decision**: When `pipeline.py` is called without flags, Stage 0 runs and fetches upstream.

**Rationale**: The primary use case for this change is a "one command to get latest docs". Users who want the old no-fetch behavior pass `--skip-fetch` explicitly.

## Risks / Trade-offs

- [Risk] Network unavailable during CI/offline use → Mitigation: `--skip-fetch` bypasses Stage 0; existing RST files are preserved
- [Risk] Upstream RST directory structure changes → Mitigation: fetch script validates expected paths exist after clone; pipeline fails fast with a clear error message
- [Risk] Large clone even with sparse-checkout → Mitigation: `--depth=1 --filter=blob:none` limits download to tip-of-tree blobs only; measured at ~2 MB for this subtree
- [Risk] git not available in some environments → Mitigation: script checks for git before proceeding and prints an actionable error

## Migration Plan

1. Add `fetch_upstream.py` — no existing code is touched
2. Modify `pipeline.py` — add Stage 0 block and two new argparse flags
3. Write `.upstream-lock.json` to `.gitignore` (or add to existing ignore rules)
4. Rollback: remove Stage 0 block from `pipeline.py`; `--skip-fetch` already provides a no-op path during the transition

## Open Questions

- Should `.upstream-lock.json` be committed to the repo to track which upstream version the checked-in Markdown was generated from? (Lean: yes, but needs `.gitignore` exception)
- Should the default `--upstream-ref` be `master` or the latest release tag? (Lean: `master` for now, override for releases)
