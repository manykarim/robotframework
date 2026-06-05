## ADDED Requirements

### Requirement: Pipeline output is automatically published to pekkaklarck/manual via PR
A GitHub Actions workflow in the `manykarim/robotframework` repository SHALL run the generation pipeline and open a pull request against `pekkaklarck/manual` containing the mapped `.md` and image files whenever a commit touching `doc/userguide-mkdocs/**` is pushed to `master`, or when the workflow is triggered manually.

#### Scenario: Master push triggers pipeline and opens a PR in pekkaklarck/manual
- **WHEN** a commit touching `doc/userguide-mkdocs/**` is pushed to `master`
- **THEN** the `publish-to-manual` workflow runs the pipeline (via `pipeline.py --skip-fetch` using already-committed content)
- **THEN** the workflow checks out `pekkaklarck/manual` using `GH_MANUAL_TOKEN`
- **THEN** the publish script copies mapped files into the manual checkout
- **THEN** a PR is opened against `pekkaklarck/manual` main branch with the updated files

#### Scenario: Manual workflow_dispatch also triggers publish
- **WHEN** the workflow is triggered via `workflow_dispatch`
- **THEN** the same pipeline-then-publish sequence runs as for a master push

#### Scenario: Pipeline failure prevents PR creation
- **WHEN** `pipeline.py` exits with a non-zero code
- **THEN** the publish step does NOT run
- **THEN** no PR is opened in `pekkaklarck/manual`

### Requirement: File mapping renames sections and files to match pekkaklarck/manual conventions
A static JSON mapping file SHALL define the exact source-to-destination path for every `.md` and image file that is published. The mapping SHALL cover the four sections: `creating-test-data` → `syntax`, `executing-tests` → `execution`, `extending` → `extend`, `appendices` → `appendix`, along with all per-file renames within each section.

#### Scenario: Mapped file is written to the correct target path
- **WHEN** the publish script processes a mapped file (e.g. `creating-test-data/test-data-syntax.md`)
- **THEN** it is written to the target path in the manual checkout (e.g. `doc/manual/docs/syntax/data.md`)

#### Scenario: Unmapped file is not published
- **WHEN** a file exists in our docs but has no entry in the mapping config (e.g. a new page not yet mapped)
- **THEN** the publish script skips it and logs a warning
- **THEN** no corresponding file is created or modified in the manual checkout

#### Scenario: Manual-only files are not deleted
- **WHEN** the publish script runs
- **THEN** files that exist in `pekkaklarck/manual` but have no source counterpart (e.g. `extend/models.md`, `extend/json.md`) are left unchanged

### Requirement: GH_MANUAL_TOKEN secret is used for cross-repo access
The workflow SHALL authenticate to `pekkaklarck/manual` using a repository secret named `GH_MANUAL_TOKEN`. This token SHALL have `repo` scope on the `pekkaklarck/manual` repository. The default `GITHUB_TOKEN` SHALL NOT be used for cross-repo operations.

#### Scenario: Missing secret causes workflow to fail with a clear error
- **WHEN** `GH_MANUAL_TOKEN` is not set or is expired
- **THEN** the checkout or push step fails with an authentication error
- **THEN** no partial changes are committed to the manual repo
