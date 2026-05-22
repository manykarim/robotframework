## Context

The MkDocs user guide has 6 top-level section directories, each with an `index.md` that is currently blank except for a single heading. Users who land on a section page see nothing useful and must rely on the sidebar to discover sub-pages. The sidebar is available on desktop but collapsed on mobile and also doesn't give any hint of page contents.

The docs pipeline converts RST source to Markdown; section index pages are generated stubs, so any content must be added either at the script level or as post-conversion static content.

## Goals / Non-Goals

**Goals:**
- Add a descriptive TOC to each of the 6 section `index.md` files.
- Each TOC entry is a Markdown link plus a one-sentence description of the target page.
- Content is hand-authored and accurate (not auto-generated from headings).

**Non-Goals:**
- Auto-generating TOCs from page headings or MkDocs navigation config.
- Changing the MkDocs navigation config (`mkdocs.yml`).
- Modifying RST source files or the conversion pipeline.
- Adding TOCs to non-index pages.

## Decisions

**Hand-authored content over auto-generation**
MkDocs Material's `toc` plugin generates in-page heading anchors, but not cross-page section overviews. Auto-generating from nav config would require a plugin or macro. Hand-authoring keeps the change simple, reviewable, and immediately accurate — the descriptions can capture what the page covers, not just echo the file name.

**Static Markdown links, not macros or shortcodes**
Using plain `[Title](page.md)` links keeps the pages portable and compatible with any MkDocs version or theme variant. Macros (e.g., `mkdocs-macros-plugin`) would add a dependency and complexity with no benefit for this use case.

**Edit index.md files directly**
The section index pages are generated stubs that are already checked in. Editing them directly (rather than regenerating them via the pipeline) is consistent with how other manual post-conversion fixes are applied, and these pages have no upstream RST equivalent.

## Risks / Trade-offs

- **Content drift** — Page descriptions are hand-written and could become stale if sub-pages are renamed or restructured. → Mitigation: keep descriptions generic enough to remain accurate across minor content changes; a future pipeline step could verify link targets.
- **Maintenance overhead** — Each new sub-page added to a section needs a manual TOC entry. → Mitigation: acceptable for the current rate of change; document expectation in a comment in each index file.

