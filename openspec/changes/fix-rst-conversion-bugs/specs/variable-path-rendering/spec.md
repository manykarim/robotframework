## ADDED Requirements

### Requirement: RF variable syntax in prose renders as literal text

The MkDocs build SHALL NOT transform Robot Framework variable syntax (`${VARIABLE}`) in Markdown prose into LaTeX math notation. The `pymdownx.arithmatex` extension SHALL be absent from `mkdocs.yml`.

#### Scenario: Variable path in italic prose renders as literal text

- **WHEN** the generated Markdown contains `*${RESOURCES}/login.resource*` (italic text with RF variable)
- **THEN** the rendered HTML shows `${RESOURCES}/login.resource` as literal text, not `\({RESOURCES}/login.resource`

#### Scenario: Variable reference in plain prose renders as literal text

- **WHEN** the generated Markdown contains `${VARIABLE_NAME}` outside a code span or fence
- **THEN** the rendered HTML shows `${VARIABLE_NAME}` without math-mode transformation

#### Scenario: mkdocs build succeeds after arithmatex removal

- **WHEN** `mkdocs build --strict` is run after `pymdownx.arithmatex` is removed from `mkdocs.yml`
- **THEN** the build exits with code 0
