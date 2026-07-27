## 1. Spike + edge-case inventory (before touching the converter)

- [x] 1.1 Spike confirmed against the manual's extension set (attr_list, def_list, tables, pymdownx.inlinehilite, magiclink, saneheaders, superfences): `<em class="setting">`, `<code class="option">`, and def-list-term classing all render correctly
- [x] 1.2 Edge cases verified — punctuation adjacency, roles inside links, roles in table cells, def-list terms, `<name:value>` args, consecutive roles all pass. Only rule: emit `{.role}` immediately adjacent to the closing delimiter (converter controls this). ezglossary `<name:value>` mangling is out of scope (Group 2)

## 2. Converter — placeholder emission (Option A; supersedes direct `{.class}`)

- [x] 2.1 (superseded) Initial direct-`{.class}` emission caused heading demotion + cross-ref/codesc mangling — replaced by the placeholder approach below (D7)
- [x] 2.2 (superseded) — see 2.5
- [x] 2.3 (superseded) — option-list terms now emit placeholders too (2.6)
- [x] 2.4 Define a compact Private-Use-Area placeholder (`<rolechar><content>`, shorter than the original `:role:` markup) and helpers to emit/parse it
- [x] 2.5 `convert_custom_roles` / `convert_postfix_roles` emit placeholders (rolechar s/n/o/f/c; `:opt:`→o). Fix `:codesc:` capture to allow escaped backticks `(?:\\.|[^`])+`
- [x] 2.6 `convert_option_lists` emits the option placeholder for each term
- [x] 2.7 New `render_roles.py` — final fix script (appended LAST in the pipeline `fix_scripts`, before VALIDATE): renders placeholders → `*content*{.setting|.name}` (em) or `` `content`{.option|.file|.codesc} `` (code), widening the backtick fence when content contains backticks

## 3. Styling — port original role CSS

- [x] 3.1 Re-add (reverted by the docs checkout) the "Roles" block into `docs/assets/extra.css` under `.md-typeset`: `.setting` italic+nowrap, `.name` italic, `.file` italic, `.option` nowrap, `.codesc` code — no color
- [x] 3.2 Confirm no per-scheme override needed (no color → light/dark agnostic; Material's code styling adapts)

## 4. Content-integrity gate (`content_check.py`) + wiring

- [x] 4.1 Implement `content_check.py`: (a) heading preservation RST→MD, (b) content-token coverage RST→MD with tolerance, (c) MD forbidden-markup scan (`:role:`, `.. ::`, RST `` `_ `` refs, grid borders, `\|`, `)_`, leftover placeholder chars), (d) HTML forbidden-markup scan (literal `{.role}`, `:role:`, placeholders)
- [x] 4.2 Wire `content_check.py` into the pipeline VALIDATE stage as a gating check with a clear per-failure report

## 5. Regenerate + verify (local, our repo)

- [x] 5.1 Run `python scripts/pipeline.py --skip-fetch`; confirm no new errors and no leftover placeholder chars
- [x] 5.2 Before/after anchor diff — confirm the 6 previously-demoted headings are restored and no anchors changed; confirm role classes present (`{.setting}`/`{.option}`/… in MD; `<em class="setting">`/`<code class="option">` in HTML)
- [x] 5.3 Run `content_check.py` and `uv run mkdocs build --strict` — both green (modulo the known environmental plugin warning)

## 6. MANDATORY review (now gated by the automated check) against the manual's toolchain

- [ ] 6.1 Build with the MANUAL's `properdocs.yml` + full requirements (ezglossary, pymdownx.*, social, mkdocstrings); run `content_check.py` against that HTML too
- [ ] 6.2 Confirm the content-check report is green and spot-check `.setting`/`.name`/`.file`/`.option`/`.codesc` rendering on `syntax/tests`, `syntax/suites`, `syntax/user-keywords`, `syntax/data`, `appendix/cli`, `extend/libdoc`; note ezglossary interaction (Group 2, out of scope)
- [ ] 6.3 Obtain explicit human sign-off (now a report confirmation + spot-check, not a full re-read). Do NOT proceed to delivery without it

## 7. Deliver to pekkaklarck/manual

- [ ] 7.1 Prepare the delivery: regenerated Markdown + the ported role CSS in the manual's `doc/manual/docs/assets/extra.css`
- [ ] 7.2 Open a PR from `manykarim` to `pekkaklarck/manual` (or direct push if maintainer access is available) with the reviewed content + CSS; summarize which issue #16 items it resolves (3, 4, 8, 22, 23) and note ezglossary/Group-2 remains separate
