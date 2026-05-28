## Context

The workflow file at `doc/userguide-mkdocs/.github/workflows/docs.yml` has an `on.push` trigger covering `master` and `doc/userguide-mkdocs/**` path filters, but both jobs (`build-check` and `deploy`) guard themselves with `if` expressions that exclude regular master-branch pushes:

- `build-check` only runs for PRs, tag pushes, or `workflow_dispatch`.
- `deploy` only runs for tag pushes or `workflow_dispatch`.

When a master push occurs, the workflow is triggered but skips every job — the "dev" GH Pages version is never updated.

The "Determine version" step already has the correct `else` branch for this case (`VERSION="dev"`, `ALIAS=""`), so the logic for deploying as `dev` is already implemented; it just never gets reached.

## Goals / Non-Goals

**Goals:**
- Master pushes that touch `doc/userguide-mkdocs/**` automatically build and deploy to the `dev` GH Pages version.
- The `build-check` job gates the deploy on master push (same as it does for tags/dispatch), preventing a broken build from reaching GH Pages.

**Non-Goals:**
- Changing the tag-based versioned deployment flow.
- Changing the `dev` version name or alias strategy.
- Modifying the `docdiff-check` job (runs on PRs only; no change needed).

## Decisions

**Add `github.event_name == 'push' && github.ref == 'refs/heads/master'` to both job conditions**

The `build-check` job needs the condition added so it runs (and can gate the deploy). The `deploy` job needs it added so it actually executes on master push. The existing `else` branch of the "Determine version" step already produces `VERSION=dev` for this case — no logic change needed there.

**Keep `needs: [build-check]` on the deploy job**

This preserves the gate: if the strict build fails on a master push, the deploy is blocked. The `build-check` job's new condition must therefore be a superset of the deploy job's new condition.

## Risks / Trade-offs

- **Deploy frequency**: every master push touching docs now triggers a deploy. Given typical commit cadence this is acceptable; GH Pages has generous rate limits.
- **Concurrent deploys**: the existing `concurrency: group: docs-${{ github.ref }}` setting already cancels in-progress runs for the same ref, preventing overlapping deploys.
- **gh-pages branch write access**: the workflow already has `contents: write` permission; no change needed.
