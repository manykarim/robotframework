## ADDED Requirements

### Requirement: Updated content is committed to the fork's main branch

The publish workflow SHALL copy the rewritten content into a checkout of `manykarim/manual` and commit the updated `.md` (and required assets) to the `main` branch.

#### Scenario: Content committed to fork main

- **WHEN** the push script runs against `manykarim/manual`
- **THEN** the mapped `.md` files under `doc/manual/docs/` are updated and committed to `main`

#### Scenario: No changes exits cleanly

- **WHEN** the publish produces no content differences
- **THEN** the script exits without creating an empty commit or deploy

### Requirement: Fork properdocs.yml points at the fork

The fork's `properdocs.yml` SHALL set `site_url` to `https://manykarim.github.io/manual/` and `edit_uri` to the fork's blob path, committed to the fork's `main`.

#### Scenario: site_url updated

- **WHEN** the fork's `properdocs.yml` is inspected after publish
- **THEN** `site_url` is `https://manykarim.github.io/manual/`

### Requirement: Site is deployed to the fork's GitHub Pages via mike

The workflow SHALL deploy the built site to the fork's `gh-pages` branch under the `dev` version using `mike`, leaving released versions (`latest`/`0.3`) intact.

#### Scenario: dev version deployed

- **WHEN** the deploy step runs (`mike deploy -F properdocs.yml --push dev`, or the fork's `dev-docs.yml` triggered by the push to `main`)
- **THEN** the `dev` version on `gh-pages` reflects the updated content and `latest` still maps to the released version

#### Scenario: Live site reachable

- **WHEN** deployment completes
- **THEN** https://manykarim.github.io/manual/dev/ serves the updated content

### Requirement: Local build verification before/with deploy

The workflow SHALL run a local `properdocs build` against the fork checkout to confirm the build succeeds (exit 0) before relying on the published result.

#### Scenario: Local build succeeds

- **WHEN** `properdocs build -f properdocs.yml` runs against the fork checkout with rewritten content
- **THEN** it exits 0
