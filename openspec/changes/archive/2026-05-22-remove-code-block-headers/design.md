## Context

The MkDocs Material theme uses the `pymdownx.highlight` extension to render fenced code blocks. When `auto_title: true` is set, the extension automatically inserts a title bar above every code block containing the human-readable name of the language (e.g., "Robot Framework", "Bash", "Text Only" for unlabelled blocks). This option was included in the initial MkDocs setup but makes the docs visually noisier than the upstream HTML guide.

## Goals / Non-Goals

**Goals:**
- Eliminate the auto-generated language title bar from all code blocks.

**Non-Goals:**
- Changing any Markdown source files.
- Disabling syntax highlighting.
- Removing line numbers or anchor links (those are controlled by separate options).
- Adding explicit `title="..."` attributes to individual code blocks.

## Decisions

**Set `auto_title: false` rather than deleting the line**
Explicit `false` documents intent and makes it clear the option was considered, rather than just missing. Both forms are equivalent to MkDocs, but `false` is self-documenting.

## Risks / Trade-offs

- None. This is a single-line config change with no side effects on functionality, navigation, or search.
