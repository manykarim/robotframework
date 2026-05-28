## ADDED Requirements

### Requirement: Master branch pushes deploy the dev site automatically
The GitHub Actions workflow SHALL deploy the MkDocs site to the `dev` GH Pages version on every push to `master` that modifies files under `doc/userguide-mkdocs/**`, without requiring a manual trigger or tag.

#### Scenario: CSS or content change pushed to master updates the live dev site
- **WHEN** a commit touching `doc/userguide-mkdocs/**` is pushed to `master`
- **THEN** the `build-check` job runs and builds the site in strict mode
- **THEN** on a successful build, the `deploy` job runs and publishes to the `dev` GH Pages version
- **THEN** `https://manykarim.github.io/robotframework/dev/` reflects the new changes

#### Scenario: Broken build on master does not update GH Pages
- **WHEN** a commit pushed to `master` causes `mkdocs build --strict` to fail
- **THEN** the `build-check` job fails
- **THEN** the `deploy` job does NOT run
- **THEN** the `dev` GH Pages version remains at the last good build

#### Scenario: Tag pushes continue to deploy versioned releases unaffected
- **WHEN** a tag matching `v*` is pushed
- **THEN** the existing tag-based deployment flow runs unchanged
- **THEN** the versioned release is published with the `latest` alias
