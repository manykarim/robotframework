### Requirement: Section index pages have an introductory summary paragraph
Each of the 6 section index pages in the MkDocs user guide SHALL have a short introductory paragraph (2–4 sentences) placed above the table-of-contents list. The paragraph SHALL describe the section's scope, be written in the Robot Framework Voice (direct, minimalist, technically grounded, no corporate fluff), and contain inline Markdown links to 1–3 of the most important sub-pages in the section.

#### Scenario: Reader lands on a section index page and sees context before the TOC
- **WHEN** a user opens any of the 6 section index pages (`getting-started`, `creating-test-data`, `executing-tests`, `extending`, `supporting-tools`, `appendices`)
- **THEN** the page displays a short introductory paragraph above the TOC list
- **THEN** the paragraph is 2–4 sentences in the Robot Framework Voice
- **THEN** the paragraph contains inline links to 1–3 of the most important sub-pages

#### Scenario: Introductory paragraph uses Robot Framework Voice
- **WHEN** the introductory paragraph is reviewed
- **THEN** it is direct and minimalist (no filler phrases like "In this section you will learn...")
- **THEN** it uses technically grounded language appropriate for test engineers
- **THEN** it has a 70/30 professional/casual balance (occasional dry humor is acceptable, corporate jargon is not)

#### Scenario: Links in summary paragraph resolve to existing sub-pages
- **WHEN** a link within the introductory paragraph is followed
- **THEN** it resolves to a page that exists within the same section
- **THEN** `mkdocs build --strict` completes without link errors for any of the 6 index pages
