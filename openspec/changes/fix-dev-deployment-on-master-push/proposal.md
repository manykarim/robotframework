## Why

CSS and content changes pushed to `master` are not reflected at `https://manykarim.github.io/robotframework/dev/` because the GitHub Actions deployment workflow only runs on tag pushes (`refs/tags/v*`) or manual `workflow_dispatch`. Regular `master` branch pushes trigger the workflow file but all jobs skip themselves due to their `if` conditions, so the "dev" GH Pages version is never updated automatically.

This means every CSS fix, content update, or pipeline improvement merged to `master` remains invisible on the live site until someone manually triggers a workflow run — a significant feedback-loop gap.

## What Changes

- The `deploy` job in `.github/workflows/docs.yml` (inside `doc/userguide-mkdocs/.github/workflows/docs.yml`) gains an additional trigger condition: `push` to `master` with paths under `doc/userguide-mkdocs/**`.
- On a master push, the job deploys as version `dev` with no alias (matching the existing `else` branch of the "Determine version" step).
- The `build-check` job also needs its `if` condition updated so it runs (and gates) on master push, not just tags/PRs/dispatch.

## Capabilities

### New Capabilities

<!-- None — this is a CI/CD fix. -->

### Modified Capabilities

<!-- No spec-level requirement changes to existing capabilities. -->

## Impact

- `doc/userguide-mkdocs/.github/workflows/docs.yml` — job `if` conditions updated.
- Every `master` push touching `doc/userguide-mkdocs/**` will now build and deploy to the `dev` GH Pages version automatically.
- No changes to Markdown source, `mkdocs.yml`, or any Python scripts.
