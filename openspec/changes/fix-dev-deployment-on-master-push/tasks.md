## 1. Fix workflow job conditions

- [ ] 1.1 In `doc/userguide-mkdocs/.github/workflows/docs.yml`, update the `build-check` job's `if` condition to also run on `push` to `master` (in addition to PRs, tag pushes, and `workflow_dispatch`)
- [ ] 1.2 In the same file, update the `deploy` job's `if` condition to also run on `push` to `master` (in addition to tag pushes and `workflow_dispatch`)

## 2. Verification

- [ ] 2.1 Review the updated `if` conditions to confirm: (a) `build-check` gates `deploy` via `needs`, (b) the "Determine version" `else` branch correctly produces `VERSION=dev` for master pushes, (c) the `concurrency` group still prevents overlapping deploys
