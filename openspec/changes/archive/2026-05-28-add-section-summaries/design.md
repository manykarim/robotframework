## Context

Each of the 6 section `index.md` pages currently contains only a heading and a TOC list. There is no introductory text to orient a reader who lands on a section page directly (via search, bookmark, or navigation). The pages were created in the `add-toc-to-section-pages` change and follow a consistent pattern: `# Section Title` → blank line → TOC list.

The Robot Framework Voice guidelines require a specific tone: direct, technically grounded, 70/30 professional/casual, dry humor where it fits, no corporate fluff. The paragraph must add genuine value — it surfaces the most important sub-pages via inline links and states the section's scope in plain language.

## Goals / Non-Goals

**Goals:**
- Add a 2–4 sentence introductory paragraph above the TOC on each of the 6 section index pages.
- Every paragraph links to 1–3 of the most important sub-pages in the section.
- Tone follows Robot Framework Voice: minimalist, human, technically grounded.

**Non-Goals:**
- Changing the TOC itself.
- Adding summaries to sub-pages (only the 6 section indexes).
- Rewriting existing page content.
- Adding images, callout boxes, or structural changes beyond the introductory paragraph.

## Decisions

**Placement: above the TOC**

Introductory text belongs before the navigation list, not after. A reader should understand what they're entering before seeing the links. The heading → paragraph → TOC sequence is standard documentation practice.

**Length: 2–4 sentences**

Long introductions defeat the purpose of a landing page. Two to four sentences is enough to orient, voice, and link — then get out of the way.

**Inline links rather than a separate "key links" block**

Embedding 1–3 links within the prose is less visually noisy than a separate callout. It also matches the Robot Framework Voice principle of being direct and to the point.

**No frontmatter or metadata changes**

The paragraphs are plain Markdown prose. No new extensions, plugins, or `mkdocs.yml` changes required.

## Risks / Trade-offs

- **Voice drift**: Writing in a specific brand voice across 6 sections is a judgment call. Sections with more technical material (Extending, Appendices) may feel drier; this is intentional and fits the Finnish-minimalist tone.
- **Link rot**: Inline links to sub-pages are relative Markdown links. If sub-pages are renamed, links break. This is the same risk as the TOC links — acceptable given that page renames are infrequent.
