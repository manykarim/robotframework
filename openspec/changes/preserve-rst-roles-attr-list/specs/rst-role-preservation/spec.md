## ADDED Requirements

### Requirement: Semantic RST roles convert to attr_list-classed inline elements

The converter SHALL convert each semantic RST role to an inline element carrying a CSS class equal to the role name, using `attr_list` syntax, with the carrier element chosen to match the original styling: `:setting:` and `:name:` as `<em>` (`*text*{.setting}` / `*text*{.name}`); `:option:`, `:file:`, `:codesc:` as `<code>` (`` `text`{.option} `` etc.). `:opt:` SHALL be treated as an `option` alias. The `{.role}` attribute SHALL be immediately adjacent to the inline element (no intervening space).

#### Scenario: Setting role becomes classed emphasis

- **WHEN** the RST source contains `` :setting:`[Setup]` ``
- **THEN** the converted Markdown is `*[Setup]*{.setting}` and renders as `<em class="setting">[Setup]</em>`

#### Scenario: Option role becomes classed code

- **WHEN** the RST source contains `` :option:`--output` ``
- **THEN** the converted Markdown is `` `--output`{.option} `` and renders as `<code class="option">--output</code>`

#### Scenario: File and name roles keep their original carriers

- **WHEN** the source contains `` :file:`output.xml` `` and `` :name:`Log` ``
- **THEN** the output is `` `output.xml`{.file} `` (code) and `*Log*{.name}` (em) respectively

#### Scenario: opt alias

- **WHEN** the source contains `` :opt:`--loglevel` ``
- **THEN** the converted output carries the `.option` class

### Requirement: Option-list definition-list terms carry the option class

The converter SHALL emit option-list definition-list terms (produced by `convert_option_lists`) with the `.option` class on the term's inline code, so roles are preserved on definition lists.

#### Scenario: CLI option term is classed

- **WHEN** the pipeline converts an option-list entry such as `--output <file>`
- **THEN** the generated definition-list term is `` `--output <file>`{.option} `` and renders as `<dt><code class="option">--output &lt;file&gt;</code></dt>`

### Requirement: Original role styling is restored via ported CSS

`docs/assets/extra.css` SHALL define role styling ported from `doc/userguide/src/userguide.css`, scoped under `.md-typeset`, for both light and dark schemes: `.setting` italic + nowrap; `.name` italic; `.file` italic; `.option` nowrap; `.codesc` code styling. No per-role color SHALL be introduced.

#### Scenario: Setting renders italic and non-wrapping

- **WHEN** a `.setting` element is rendered
- **THEN** it is italic and does not wrap, without a monospace box

#### Scenario: Dark scheme parity

- **WHEN** the site is viewed in the dark colour scheme
- **THEN** role styling remains legible using Material's dark variables

### Requirement: No conversion or build regression

After the change, the pipeline SHALL regenerate without new errors, `mkdocs build --strict` SHALL exit 0 (modulo the pre-existing environmental plugin warning), and heading/anchor slugs SHALL be unchanged relative to before the change.

#### Scenario: Anchors unchanged

- **WHEN** generated anchors are diffed before and after the role change
- **THEN** there are no anchor/slug differences attributable to role classing

#### Scenario: Roles do not appear as literal attr_list text

- **WHEN** any converted page is rendered
- **THEN** no literal `{.setting}`/`{.option}`/etc. text is visible (every attribute list is consumed by `attr_list`)
