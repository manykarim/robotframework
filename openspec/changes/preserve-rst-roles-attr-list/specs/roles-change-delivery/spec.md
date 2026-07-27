## ADDED Requirements

### Requirement: Mandatory local review of rendered HTML before delivery

The regenerated content and role CSS SHALL be reviewed locally by building the site with the manual's own toolchain (its `properdocs.yml` and full plugin set, including `mkdocs-ezglossary`, `pymdownx.*`, `social`, `mkdocstrings`) and inspecting the RENDERED HTML for representative pages before any delivery to `pekkaklarck/manual`. Delivery SHALL NOT proceed without an explicit human sign-off.

#### Scenario: Review uses the manual's full toolchain

- **WHEN** the local review build is produced
- **THEN** it is built from the manual's `properdocs.yml` (not this repo's lighter `mkdocs.yml`), so ezglossary/highlight interactions are visible

#### Scenario: Representative pages inspected

- **WHEN** the reviewer inspects the rendered HTML
- **THEN** settings/options/names/files styling is verified on at least `syntax/tests`, `syntax/suites`, `syntax/user-keywords`, `syntax/data`, `appendix/cli`, and `extend/libdoc`

#### Scenario: Sign-off gates delivery

- **WHEN** the local review has not been explicitly approved
- **THEN** no push or PR to `pekkaklarck/manual` is made

### Requirement: Delivery targets pekkaklarck/manual with role CSS included

The change SHALL be delivered to `pekkaklarck/manual` (via PR from `manykarim`, consistent with the merged PR #3), and the delivery SHALL include the ported role CSS in the manual's `doc/manual/docs/assets/extra.css`, not only the regenerated Markdown.

#### Scenario: CSS accompanies the content

- **WHEN** the delivery is prepared
- **THEN** the manual's `extra.css` contains the ported `.setting`/`.name`/`.file`/`.option`/`.codesc` rules alongside the updated Markdown

#### Scenario: Delivery destination

- **WHEN** the reviewed change is delivered
- **THEN** its destination is `pekkaklarck/manual` (not only the `manykarim/manual` fork)
