## ADDED Requirements

### Requirement: Role identity is carried by a markdown-inert placeholder rendered last

The converter SHALL emit each semantic role (and option-list term) as a compact Private-Use-Area placeholder that is inert to all downstream passes and shorter than the original `:role:` markup, and a final pipeline step (`render_roles.py`, last before VALIDATE) SHALL render placeholders to the `attr_list` carrier. No intermediate pass SHALL ever process the `attr_list` markup.

#### Scenario: Role inside a heading is not demoted

- **WHEN** a section title contains a role (e.g. `Using :setting:`[Return]` setting`)
- **THEN** the converted output is still a Markdown heading (`### Using *[Return]*{.setting} setting`), not body text

#### Scenario: Role adjacent to a cross-reference is not mangled

- **WHEN** roles like `:file:`.`` / `:file:`_`` sit next to links or bare-ref-prone text
- **THEN** the rendered output contains clean `<code class="file">` elements and no bogus generated links

#### Scenario: codesc with backtick content is preserved

- **WHEN** the source contains `` :codesc:`\`\`argument\`\`` ``
- **THEN** the output is valid inline code carrying `.codesc` with the backticks intact, not broken markup

#### Scenario: No leftover placeholder characters

- **WHEN** the pipeline completes
- **THEN** no Private-Use-Area placeholder characters remain in any generated `.md` or built `.html`

### Requirement: Content-integrity check verifies content preservation and formatting

The pipeline SHALL run a `content_check.py` validation that gates the build and reports the offending location for every failure.

#### Scenario: Every RST section becomes a heading

- **WHEN** the check compares each RST source file to its generated Markdown
- **THEN** every RST section title is present as a Markdown heading, or the check fails naming the missing heading

#### Scenario: Dropped cell/sentence content is detected

- **WHEN** converted content omits text that exists in the RST source (e.g. an emptied table cell)
- **THEN** the check fails and reports the missing content

#### Scenario: Leaked source markup is detected in Markdown

- **WHEN** generated Markdown contains unconverted `:role:`, `.. directive::`, RST `` `text`_ `` references, grid-table borders, stray `\|`, `)_`, or leftover placeholder chars
- **THEN** the check fails and lists the occurrences

#### Scenario: Leaked markup is detected in HTML

- **WHEN** the built HTML contains literal `{.role}`, `:role:`, or placeholder characters
- **THEN** the check fails and lists the occurrences

### Requirement: Manual review is reduced to a sign-off over the check report

With the content-integrity gate green, the mandatory local review SHALL be reduced to confirming the check report and spot-checking rendering, rather than a full content re-read, while still requiring explicit human sign-off before delivery.

#### Scenario: Green gate enables sign-off

- **WHEN** `content_check.py` and `mkdocs build --strict` both pass
- **THEN** the reviewer confirms the report and spot-checks representative pages, then signs off — no full manual content diff is required
