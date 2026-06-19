## ADDED Requirements

### Requirement: Anonymous reference resolution ignores dunder identifiers in code spans

The converter SHALL NOT treat the opening backtick of a dunder identifier (e.g., `` `__version__` ``) as the closing delimiter of an anonymous reference backtick pattern. The lookbehind on the anonymous reference pattern SHALL ensure the match starts at an opening backtick only.

#### Scenario: Dunder attribute name in prose does not create false anonymous reference

- **WHEN** the RST source contains `` `__version__` `` (single-backtick span with dunder name) in prose near anonymous URL targets
- **THEN** the converted Markdown contains no broken link syntax around the dunder identifier

#### Scenario: Legitimate backtick anonymous reference resolves correctly

- **WHEN** the RST source contains `` `arguments`__ `` linked to an anonymous URL target
- **THEN** the converted Markdown contains `[arguments](url)` where url is the matching anonymous target

#### Scenario: Word-style anonymous reference resolves correctly

- **WHEN** the RST source contains `ctypes__` linked to an anonymous URL target
- **THEN** the converted Markdown contains `[ctypes](url)` where url is the matching anonymous target

#### Scenario: Library version section renders without broken links

- **WHEN** the pipeline converts `CreatingTestLibraries.rst`
- **THEN** the "Library version" section in `creating-test-libraries.md` contains no `](http://...)version__` artifacts and `__version__` appears as plain inline code
