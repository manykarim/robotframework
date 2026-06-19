## ADDED Requirements

### Requirement: RST option lists convert to def_list definition lists

The converter SHALL detect RST option-list blocks and render each entry as a MkDocs `def_list` definition: the option spec as the term (inline code) and the description as the definition.

#### Scenario: Same-line description

- **WHEN** the RST contains `  -F, --extension <value>  Parse only these files when executing a directory.`
- **THEN** the converted Markdown contains a term `` `-F, --extension <value>` `` followed by a `:   Parse only these files when executing a directory.` definition line

#### Scenario: Next-line description (Libdoc style)

- **WHEN** an option line has no same-line description and the description begins on the following indented line(s)
- **THEN** the option spec becomes the term and the following indented lines become its definition

#### Scenario: Multi-line description is joined

- **WHEN** a description wraps across multiple indented continuation lines
- **THEN** the continuation lines are joined into a single definition for that option

#### Scenario: Consecutive entries form one list

- **WHEN** a block contains multiple consecutive option entries
- **THEN** each becomes a term/definition pair rendered together as one definition list

### Requirement: Option args with pipes and colons are preserved

The converter SHALL preserve `<arg>` syntax containing `|` or `:` (e.g. `--removekeywords <all|passed|name:pattern|tag:pattern|for|while|wuks>`) verbatim in the term.

#### Scenario: Pipe-containing option arg

- **WHEN** an option spec contains `<all|passed|name:pattern>`
- **THEN** the term contains that arg unchanged and does not break the list structure

### Requirement: Code-fence content is never converted

The converter SHALL NOT convert option-like lines that appear inside fenced code blocks (command-line examples).

#### Scenario: Command example inside a code block is untouched

- **WHEN** a fenced code block contains lines like `--variable HOST:10.0.0.2:1234` or `--test Example*  # comment`
- **THEN** those lines are left unchanged inside the code block

### Requirement: Existing definition lists and bullet lists are unaffected

The converter SHALL leave the env-vars definition list and ordinary bullet lists unchanged.

#### Scenario: Env-vars def list preserved

- **WHEN** the CLI page's environment-variables section (already a `def_list`) is converted
- **THEN** it remains a correct definition list with no double conversion

#### Scenario: Bullet list preserved

- **WHEN** a bullet item like `- some text` is present
- **THEN** it is not converted into an option-list definition

### Requirement: Affected pages build and render after regeneration

After the converter change, running the pipeline SHALL regenerate the option-list pages and `mkdocs build --strict` SHALL exit 0.

#### Scenario: CLI page renders as a definition list

- **WHEN** the pipeline regenerates `appendices/command-line-options.md`
- **THEN** the option lists appear as term/definition pairs (not a collapsed paragraph) and the build exits 0
