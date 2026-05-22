# Robot Framework User Guide migration audit (HTML → Material for MkDocs)

**Date:** 2026-01-28  
**Compared targets:**
- **Old generated site (single HTML):** Robot Framework User Guide on robotframework.org citeturn2view0  
- **New generated site (MkDocs Material, multi-page):** manykarim GitHub Pages site citeturn1view0  
- **Old source docs (reStructuredText):** `robotframework/robotframework` → `doc/userguide` (reference) citeturn0search21  
- **New source docs (Markdown):** `manykarim/robotframework` → `doc/userguide-mkdocs` (reference)

---

## 1. Executive summary (audit style)

### High-confidence findings
1. **Version mismatch between old and new published docs**
   - Old HTML page indicates **Robot Framework User Guide – Version 7.4.1** citeturn2view0  
   - New MkDocs home page indicates documentation for **Robot Framework version 7.0** citeturn1view0  
   **Impact:** you will see legitimate content differences that are *not* migration regressions, but upstream version drift.

2. **Top-level structure matches, but navigation model differs**
   - Old site is a **single HTML file** with a numbered TOC (1–6) and deep anchors citeturn2view0  
   - New site is **split into section pages** (“Getting Started”, “Creating Test Data”, …) and then further into subpages citeturn1view0turn3view0turn3view1  
   **Impact:** anchor/link comparison must include **URL + fragment rewrite** and cannot be a naïve string diff.

3. **At least for sampled sections, content appears substantially preserved**
   - “Introduction” page in MkDocs includes the same major subsections as old (“Why Robot Framework?”, “High-level architecture”, “Screenshots”, “Getting more information”) citeturn4view0turn2view0

### Main risks to target with automation
- **Internal link & anchor drift** (single-page `#id` anchors → multi-page `/<path>/#id` anchors)
- **Tables**: HTML table semantics vs Markdown tables (alignment/escaping)
- **Admonitions/notes**: reST “Note” blocks vs Material admonitions (syntax + nesting)
- **Code blocks**: language tags (for highlighting), indentation fidelity, and line wrapping
- **Images**: path rewriting, alt text differences, missing assets, and figure captions

---

## 2. Scope and comparison approach used for this audit

This audit focuses on:
- **Structural equivalence**: do both document sets cover the same topics/sections?
- **Semantic equivalence**: is the prose content and meaning preserved?
- **Rendering-sensitive elements**: links/anchors, tables, lists, admonitions, code blocks, images.

Given the size of the User Guide, the practical strategy is:
1. Verify **structure & coverage** via TOC extraction and nav mapping.
2. Run **section-level diff** after normalizing both formats to a comparable representation.
3. Investigate **high-risk constructs** (tables, admonitions, code, images) with targeted checks.

---

## 3. Structure mapping (old single HTML → new multi-page MkDocs)

### 3.1 Old guide: top-level TOC (single page)
The old page’s TOC shows 6 major chapters:
1. Getting started  
2. Creating test data  
3. Executing test cases  
4. Extending Robot Framework  
5. Supporting Tools  
6. Appendices citeturn2view0

### 3.2 New guide: top-level navigation
The MkDocs site exposes the same major categories in top navigation:
- Getting Started  
- Creating Test Data  
- Executing Tests  
- Extending Robot Framework  
- Supporting Tools  
- Appendices citeturn1view0turn3view0turn3view1turn3view2turn3view3turn3view4

### 3.3 Mapping table (top-level)
| Old HTML TOC | New MkDocs section | Status |
|---|---|---|
| 1 Getting started | `/getting-started/` | ✅ Present citeturn3view0 |
| 2 Creating test data | `/creating-test-data/` | ✅ Present citeturn3view1 |
| 3 Executing test cases | `/executing-tests/` | ✅ Present citeturn3view2 |
| 4 Extending Robot Framework | `/extending/` | ✅ Present citeturn3view3 |
| 5 Supporting Tools | `/supporting-tools/` | ✅ Present citeturn3view4 |
| 6 Appendices | `/appendices/` | ✅ Present citeturn1view0 |

---

## 4. Findings by risk area

### 4.1 Links and anchors (highest risk)
**What changes in migration**
- Old: deep linking is primarily `RobotFrameworkUserGuide.html#some-id` within one page.
- New: deep linking becomes `/<section>/<page>/#some-id` and also introduces different heading IDs.

**What to verify**
- **Internal links** within the guide:
  - Do they point to existing targets?
  - Are fragments (`#...`) correct after title/slug rewriting?
- **Cross-document links** (e.g., to libraries docs) still resolve.

**Observed evidence (spot check)**
- MkDocs “Introduction” contains many internal links (e.g. “creating tasks”, “reports”, “logs”, “output files”) and external links. citeturn4view0  
- Old guide TOC and anchors are extensive and highly structured. citeturn2view0  

**Likely drift patterns to catch**
- Title punctuation or casing changes → different generated IDs.
- Numbered headings in old HTML may produce different IDs than MkDocs slugs.
- References that used to be intra-page may now require cross-page URLs.

**Audit recommendation**
- Implement a **link graph check**:
  - Extract all `<a href>` from old HTML and from built MkDocs HTML.
  - Canonicalize URLs and verify targets exist in the new site.
  - Flag: missing page, missing fragment, or fragment that points to the wrong heading.

---

### 4.2 Tables
**Common migration issues**
- Markdown tables don’t support row/col spans (HTML does).
- Whitespace and escaping differs, especially for `|` and code spans.
- ReST tables (grid/simple) may convert imperfectly.

**Audit recommendation**
- Normalize tables into a canonical representation:
  - For HTML: extract table rows/cells as plain text matrix.
  - For Markdown: parse pipe tables + list-table patterns (as best-effort), or compare *rendered HTML tables* after building.

---

### 4.3 Images
**Common migration issues**
- Relative path differences (`..` and asset directories)
- Missing images in repo, or moved assets not copied
- Changed captions/alt text

**Observed evidence (spot check)**
- MkDocs “Introduction” renders images for “architecture.png”, “testdata_screenshots.png”, “screenshots.png”. citeturn4view0  

**Audit recommendation**
- Extract all image sources (`<img src=...>`) from:
  - old HTML (single page)
  - new built HTML pages
- Verify that each referenced image resolves to an HTTP 200 (or exists locally in build output).

---

### 4.4 Lists and bullets
**Common migration issues**
- Nested lists collapse due to indentation mistakes in Markdown.
- Ordered list numbering changes when split across files.

**Audit recommendation**
- In normalization, represent lists as:
  - level + item text (indent depth is part of the key)
- Compare list item sequences with a fuzzy diff (SequenceMatcher) and flag:
  - missing items
  - re-ordered items (usually acceptable if semantically same)

---

### 4.5 Admonitions (Notes, Warnings, Tips)
**Common migration issues**
- reST directive blocks (`.. note::`) don’t map 1:1 unless explicitly converted.
- MkDocs Material requires specific Markdown syntax (e.g., `!!! note`).

**Observed evidence (spot check)**
- MkDocs “Introduction” includes a “Note” block rendered as a distinct admonition. citeturn4view0  

**Audit recommendation**
- Detect admonitions in both sides and compare:
  - type (note/warning/tip)
  - contained text (normalized)

---

### 4.6 Code blocks and syntax highlighting
**Common migration issues**
- Language markers missing (` ```robotframework ` vs plain triple backticks)
- Indentation loss for tabular Robot Framework syntax
- Line wrapping changes in HTML output

**Observed evidence (spot check)**
- MkDocs pages render language-labeled blocks (e.g., “RobotFramework”, “Bash”) citeturn3view0turn3view1  

**Audit recommendation**
- Treat code blocks as *atomic*:
  - compare normalized content (strip trailing spaces, normalize newlines)
  - compare presence of language tag (important for highlighting)

---

## 5. Priority issues to resolve before declaring “content equivalent”

### P0 — Must fix/understand
- **Documentation version mismatch (7.4.1 vs 7.0)**  
  Decide whether you are comparing the same upstream content baseline. citeturn2view0turn1view0

### P1 — Must verify automatically
- **Internal links + fragments** across split pages (broken anchors are common)
- **Image asset completeness** (missing/moved images)
- **Tables fidelity** (row/col content preserved)

### P2 — Good to verify automatically
- Admonition types and text
- Code block language tags + block content

---

## 6. Proposed automated comparison strategy (practical)

### 6.1 Normalize both sides into a common “Doc IR” (intermediate representation)
Instead of comparing raw HTML vs Markdown, convert each section into:

- `section_key`: stable identifier (number + title if available)
- `title`: heading text
- `path`: where it lives (old = fragment id; new = page + fragment)
- `blocks`: ordered list of blocks:
  - paragraph(text)
  - list(level, ordered?, items[])
  - table(matrix)
  - code(lang, text)
  - admonition(kind, text)
  - image(src, alt, caption)
  - link(href, text)

This makes comparisons consistent and allows “smart diffs”.

### 6.2 Align sections: old headings → new pages/headings
Use a multi-stage alignment:
1. **Exact match** on numbered headings (e.g., `2.1 Test data syntax`)
2. **Fuzzy match** on heading titles (casefold + remove punctuation)
3. **Context-aware match** (parent heading + child heading)

### 6.3 Compare blocks and score similarity
- Use `difflib.SequenceMatcher` for:
  - paragraph text
  - list items
  - code block text
- For tables: compare normalized matrix and compute:
  - row/col count deltas
  - cell-level diffs
- Emit:
  - similarity score
  - missing blocks (present in old, absent in new)
  - extra blocks (present in new, absent in old)

---

# Tooling plan: build a no-deps Python CLI for automated comparisons

## 7. Goals and non-goals

### Goals
- Compare **one old HTML file** against a **directory of Markdown files** (new docs).
- Produce a **Markdown audit report**:
  - coverage & mapping summary
  - per-section similarity score
  - prioritized warnings (links/images/tables/code/admonitions)
- No third-party Python dependencies.

### Non-goals (initially)
- Perfect Markdown parsing for every extension (keep best-effort).
- Pixel-perfect HTML rendering diffs (that’s a separate class of problem).

---

## 8. CLI design

### Command
```bash
python -m docdiff \
  --old-html RobotFrameworkUserGuide.html \
  --new-md-dir doc/userguide-mkdocs \
  --out report.md \
  --base-url-new https://manykarim.github.io/robotframework/dev/ \
  --base-url-old https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html
```

### Options
- `--strict` : fail (exit code 2) on P0/P1 findings
- `--min-similarity 0.92` : threshold for “OK”
- `--section` : only diff a subset (regex)
- `--emit-json report.json` : machine-readable summary (optional)

Exit codes:
- `0` OK (no P0/P1)
- `1` warnings (P2+ only)
- `2` errors (P0/P1)

---

## 9. Implementation architecture (pure stdlib)

### Modules
- `fetch.py` (optional): download HTML or resolve absolute paths (`urllib.request`)
- `html_extract.py`: parse old HTML into sections + blocks
- `md_extract.py`: parse Markdown files into sections + blocks (best-effort)
- `normalize.py`: common normalization (whitespace, punctuation, entity decoding)
- `align.py`: section matching heuristics
- `compare.py`: block-by-block compare + scoring
- `report.py`: Markdown report generator
- `cli.py`: argparse entrypoint

### Data classes (stdlib `dataclasses`)
- `Section(title, key, blocks, source_path)`
- `Block(kind, text|matrix|meta...)`
- `Finding(priority, section_key, message, evidence)`

---

## 10. HTML extraction details (stdlib only)

Use `html.parser.HTMLParser` to build a lightweight DOM-ish stream:
- Track when inside:
  - headings `<h1..h6>`
  - `<p>`, `<li>`, `<pre><code>`, `<table>`, `<img>`, `<a>`
- Collect:
  - heading text and `id`/`name` anchors
  - code blocks (preserve newlines exactly)
  - tables (rows/cells)
  - links/images

Split into sections by heading level:
- Treat `h2` (or numbered headings) as section start
- Keep hierarchy (parent pointers) for alignment context

---

## 11. Markdown extraction details (stdlib only)

Given “no third-party libs”, treat Markdown in two layers:

### Layer 1: structural parsing (cheap and robust)
- Headings:
  - `^#{1,6}\s+...`
  - Setext headings (`===` / `---`) if present
- Fenced code blocks:
  - ```lang … ```
- Admonitions (Material):
  - `!!! note`, `!!! warning`, etc.
  - `???` collapsible blocks (if used)
- Tables:
  - Pipe tables (header separator with `---`)
- Lists:
  - `-`, `*`, `+` and `1.`, `2.` with indentation level

### Layer 2: inline normalization (best-effort)
- Convert:
  - links `[text](href)` → link block or inline token
  - images `![alt](src)` → image block token
  - inline code `` `...` ``
- Strip emphasis markers `* _ ** __` (for text comparison)

This will not be perfect Markdown parsing, but it’s good enough to detect:
- missing paragraphs
- list changes
- code drift
- many table errors
- admonition content drift

---

## 12. Section alignment heuristics (no deps)

### Keys
Prefer stable keys in this order:
1. **Explicit numbering** in heading text: `r"^\d+(\.\d+)*\s+"`
2. **Normalized title**: lowercase, remove punctuation, collapse whitespace
3. **(parent, title)** tuple (context)

### Matching algorithm
1. Build index maps for new docs:
   - by number prefix
   - by normalized title
2. For each old section:
   - match by number if available
   - else match by title exact
   - else fuzzy match with `difflib.SequenceMatcher` and require > threshold (e.g., 0.88)
3. Resolve collisions by preferring:
   - same parent match
   - higher similarity
   - shortest path distance in new nav

---

## 13. Comparison algorithm and scoring

### Per-section similarity score
Weighted block similarity:
- paragraphs: 35%
- lists: 15%
- code: 20%
- tables: 15%
- admonitions: 10%
- images/links presence: 5%

Compute each block similarity using `SequenceMatcher.ratio()` on normalized text.
For tables, compute a blended score:
- dimension match (rows/cols)
- per-cell text match

### Findings classification
- **P0**: version drift / mismatched baseline; large missing sections; tool failures
- **P1**: broken links/anchors; missing images; missing major tables/code blocks
- **P2**: small text drift; reordered list items; minor formatting differences

---

## 14. Markdown report format (generated by the tool)

### Header
- Inputs, timestamps, tool version
- Summary of coverage:
  - total old sections
  - matched sections
  - missing sections
- Top P0/P1 findings

### Per-section entries
For each old section:
- Mapped new target (path + heading)
- Similarity score
- Findings list (bulleted)
- Small diff excerpts (max N lines) for:
  - paragraph drift (first mismatch)
  - code drift (first mismatch)
  - table drift (first mismatch)
- Link checks summary:
  - total links, broken count, broken examples

---

## 15. CI integration suggestion (optional, still no Python deps)
- Run the CLI in GitHub Actions:
  - build old HTML (or download it)
  - build mkdocs site
  - run compare
  - upload `report.md` as artifact
- Enforce `--strict` on main branch.

---

## 16. Immediate next steps for your migration project

1. **Freeze baseline**
   - Ensure old and new builds are based on the *same Robot Framework version/tag* (or explicitly accept drift). citeturn2view0turn1view0

2. **Run automated link/image checks first**
   - They catch the most painful regressions and are deterministic.

3. **Do section-level semantic diff**
   - Start with top 20 most linked/visited sections (Getting Started + Syntax + Execution + Libdoc).

4. **Iterate conversion rules**
   - Fix systemic issues (tables/admonitions/code) at the converter level, not by hand.

---

## Appendix A — Evidence snippets referenced
- Old User Guide TOC and version shown at top of single HTML page. citeturn2view0  
- New MkDocs home page showing structure and “Version: 7.0”. citeturn1view0  
- New “Getting Started” and subpages list. citeturn3view0turn4view0  
- New “Creating Test Data” and deep subpages exist. citeturn3view1turn4view3turn4view4turn4view6  
- New “Basic Usage”, “Creating Test Libraries”, “Libdoc” pages exist. citeturn4view7turn4view8turn4view9  