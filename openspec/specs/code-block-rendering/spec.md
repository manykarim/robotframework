## Requirements

### Requirement: Code blocks do not display an auto-generated language title bar
The MkDocs site SHALL render fenced code blocks without an automatically generated title bar showing the language name (e.g., "Robot Framework", "Bash", "Text Only"). The `auto_title` setting in `pymdownx.highlight` SHALL be `false`.

#### Scenario: Code block with a named language renders without a title bar
- **WHEN** a page containing a ` ```robotframework ` code block is rendered
- **THEN** no "Robot Framework" title bar appears above the code block

#### Scenario: Code block without a language renders without a title bar
- **WHEN** a page containing a bare ` ``` ` code block is rendered
- **THEN** no "Text Only" title bar appears above the code block
