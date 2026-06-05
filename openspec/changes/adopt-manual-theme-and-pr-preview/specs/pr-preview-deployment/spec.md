## ADDED Requirements

### Requirement: Pull requests get a live preview deployment
The GitHub Actions workflow SHALL deploy a versioned preview of the MkDocs site for every pull request that touches `doc/userguide-mkdocs/**`. The preview SHALL be accessible at `https://manykarim.github.io/robotframework/pr-{number}/` and a link SHALL be posted as a comment on the PR.

#### Scenario: PR is opened or updated and triggers a preview deployment
- **WHEN** a pull request touching `doc/userguide-mkdocs/**` is opened or synchronised against `master`
- **THEN** the `build-check` job runs first (strict build gate)
- **THEN** on a successful build, the `pr-preview` job deploys the site as mike version `pr-{number}`
- **THEN** a comment is posted on the PR with the URL `https://manykarim.github.io/robotframework/pr-{number}/`

#### Scenario: Failed build does not deploy a preview
- **WHEN** `mkdocs build --strict` fails on a PR
- **THEN** the `pr-preview` job does NOT run
- **THEN** no preview is deployed and no comment is posted

#### Scenario: PR closure triggers preview cleanup
- **WHEN** a pull request is closed (merged or abandoned)
- **THEN** the `pr-cleanup` job runs and deletes the `pr-{number}` mike version from GH Pages
- **THEN** the preview URL returns 404 after cleanup completes
