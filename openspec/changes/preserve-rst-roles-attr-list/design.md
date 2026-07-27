## Context

Issue #16's largest cluster ("no syntax highlighting" on settings/options/names/files) was validated as one defect: `convert.py`'s `ROLE_PATTERNS` lower each semantic role to the nearest plain Markdown primitive and drop the role name, so the original CSS classes have nothing to target. Findings and a rendering spike established the following ground truth:

- `attr_list` is enabled in both `mkdocs.yml:120` and the manual's `properdocs.yml`.
- Spike (python-markdown 3.10 with `attr_list` + `def_list` + `pymdownx.inlinehilite` + `pymdownx.betterem`): `` `Library`{.setting} `` → `<code class="setting">…</code>`, `*Log*{.name}` → `<em class="name">…</em>`, and inside a def-list term `` `--output <file>`{.option} `` → `<dt><code class="option">…</code></dt>`. The class survives `inlinehilite` (the main risk) and lands on the inline carrier.
- Original styling in `doc/userguide/src/userguide.css` ("Roles" block): `.setting` italic+nowrap (no mono); `.name` italic; `.file` mono+bg+italic; `.option` mono+bg+nowrap; `.codesc` mono+bg. The current converter mapping does NOT match this for `setting` (emits mono code) or `file` (emits italic-only em).
- Scale: setting 94, option 281, name 231, file 158, codesc 31 (~795 total).
- `attr_list` limitation: it cannot attribute *implied* elements (`dl`, `table`, `tr`, and the `dt`/`dl` wrappers); only inline elements and `li`/`td`. So role classes attach to the `<code>`/`<em>` inside a term, not to `<dt>` itself.

Pipeline-first principle ([[feedback_pipeline_approach]]): the converter change lives in `convert.py`; generated `.md` is never hand-edited.

## Goals / Non-Goals

**Goals:**
- Every semantic role renders with its original distinct styling, driven by a CSS class that mirrors the role name.
- Option-list definition-list terms carry `.option` (roles preserved on definition lists).
- Restore the original `userguide.css` role styling 1:1 (light + dark), no regressions.
- Mandatory local review of the rendered HTML (manual's full toolchain) before delivering to `pekkaklarck/manual`.

**Non-Goals:**
- Per-role **color-coding** (the original had none) — a separable follow-up.
- The `mkdocs-ezglossary` term-mangling (issue #16 Group 2) — a downstream-config change; adding `.option` does NOT stop ezglossary from splitting `<name:value>`.
- The link/table/codesc/CSS-port fixes from the other #16 groups — separate changes.
- Styling the `<dl>`/`<dt>` wrappers directly (not addressable by `attr_list`).

## Decisions

### D1 — Carrier element per role (match the original CSS)

| Role | Emit | HTML | Ported CSS (under `.md-typeset`) |
|---|---|---|---|
| `:setting:` | `*text*{.setting}` | `<em class="setting">` | `font-style: italic; white-space: nowrap` |
| `:name:` | `*text*{.name}` | `<em class="name">` | `font-style: italic` |
| `:file:` | `` `text`{.file} `` | `<code class="file">` | `font-style: italic` (code base = mono+bg) |
| `:option:` (and `:opt:`) | `` `text`{.option} `` | `<code class="option">` | `white-space: nowrap` |
| `:codesc:` | `` `text`{.codesc} `` | `<code class="codesc">` | code base styling only |

`setting`/`name` use `<em>` (italic, no mono) to match the original; `file`/`option`/`codesc` use `<code>` (mono). This corrects the current `setting`-as-code mismatch.

Alternative considered: keep all roles as `` `code` `` and differentiate purely by CSS. Rejected — `.setting`/`.name` were italic non-mono in the original; forcing a mono box then un-styling it is more fragile than choosing the right carrier.

### D2 — Two emit paths

Role tokens originate in two places: `convert_custom_roles`/`convert_postfix_roles` (inline `:role:` usages) and `convert_option_lists` (option-list def-list terms). Both must attach the class. `KNOWN_ROLES` is the single source of role names; `:opt:` maps to `option`.

### D3 — attr_list adjacency and edge cases (spike-first)

The `{.role}` must be immediately adjacent to the closing backtick/asterisk (no space), else in a table cell a space targets the `<td>`. Edge cases to enumerate on a spike page (`syntax/data`) before rollout: role adjacent to trailing punctuation, roles nested inside links, roles inside table cells, and role tokens that are also cross-reference targets. The converter controls output, so adjacency is enforceable, but the spike must confirm no interaction breaks (betterem, inlinehilite, magiclink).

### D4 — CSS delivery to two files

The role CSS goes into this repo's `docs/assets/extra.css` (for our own build/review) AND the manual's `doc/manual/docs/assets/extra.css` (the deployed site). `publish_to_manual.py` currently syncs only Markdown, so the CSS must be carried too — either by extending the publish step to sync `extra.css` or by including it in the delivery PR. Decision: include the role CSS in the delivery to `pekkaklarck/manual` (and note the sync gap for a future publish-script improvement).

### D5 — Mandatory local review against the MANUAL's toolchain

The review MUST build with the manual's `properdocs.yml` (all plugins: `pymdownx.*`, `mkdocs-ezglossary`, `social`, `mkdocstrings`), not this repo's lighter `mkdocs.yml` — otherwise ezglossary/highlight interactions are invisible. Reviewer inspects rendered HTML for settings/options/names/files across representative pages (`syntax/tests`, `syntax/suites`, `syntax/user-keywords`, `syntax/data`, `appendix/cli`, `extend/libdoc`) and signs off before anything is delivered to `pekkaklarck/manual`. This is a hard gate, per the requester.

### D6 — Delivery to pekkaklarck/manual

Deliver via PR from `manykarim` to `pekkaklarck/manual` (the path used by the merged PR #3; direct push likely needs maintainer rights). If direct push is available it may be used, but the delivery gate (D5 + D8) is mandatory regardless.

### D7 — Placeholder emission + final render (supersedes naive D1/D2 emission)

**Problem found during apply:** emitting `{.class}` attr_list markup directly inside `convert_custom_roles` (converter step 2 of ~16, then ~18 `fix_*.py` passes) is unsafe. The markup (a) *inflates heading text past the RST underline*, so `convert_sections` (`convert.py:636` requires `len(underline) >= len(title)`) silently demotes 6 role-bearing headings to body text; (b) is *mangled by `convert_cross_references`* — the `{`/`.`/`}`/`_` chars get mis-parsed into bogus links; (c) breaks `:codesc:` with backtick content (11 spots).

**Fix:** carry role identity through the pipeline as a compact, markdown-inert **placeholder**, and render it to `attr_list` markup only as the very last pipeline step.

- Emit format (Private Use Area, never matched by any ASCII markup regex, and **shorter** than the original `:role:` markup so heading underlines still cover the title): `<rolechar><content>`, rolechar ∈ {s,n,o,f,c}.
- `convert_custom_roles`, `convert_postfix_roles`, and `convert_option_lists` all emit placeholders (option-list terms included).
- Fix the `:codesc:` capture to allow escaped backticks (`(?:\\.|[^`])+`) so backtick-bearing content is captured whole.
- New final fix script `render_roles.py`, appended LAST in the pipeline `fix_scripts` list (after all link/anchor/table fixers, before VALIDATE), renders each placeholder to its carrier: `s`/`n` → `*content*{.setting|.name}` (em); `o`/`f`/`c` → `` `content`{.option|.file|.codesc} `` (code), choosing a backtick fence wide enough for content that itself contains backticks.

Because no downstream pass ever sees the attr_list markup, cross-ref/heading/codesc regressions cannot occur; heading length is preserved (placeholder < original), so no demotion.

### D8 — Automated content-integrity gate (reduce manual review)

Add a `content_check.py` validation, run in the pipeline VALIDATE stage and gating, that verifies the converted docs preserve the original User Guide content and are artifact-free — so manual review shrinks to a sign-off over an evidence report instead of a full re-read.

Checks (RST source ↔ generated MD ↔ built HTML), each fails loudly with the offending location:
1. **Heading preservation** — every RST section title appears as a heading in the corresponding MD (normalized). Directly catches the demotion class.
2. **Content coverage** — normalized content tokens of the RST (roles→content, directives/comments/target-defs stripped) are a (near-)superset-preserved set in the MD; report dropped spans above a small tolerance. Catches dropped table cells / sentences (e.g. the `${\n}` empty cell).
3. **No leaked source markup in MD** — no unconverted `:role:` / `.. directive::` / RST `` `text`_ `` refs / grid-table borders / stray `\|` / `)_` / leftover placeholder chars.
4. **No leaked markup in HTML** — after build, no literal `{.role}` / `:role:` / placeholder chars; role spans carry their class; no empty cells where the RST had content.

The gate is intentionally strict but scoped to "same content + correct formatting as far as checkable"; it does not attempt to verify semantic correctness of every link target (that stays a targeted, separate concern).

## Risks / Trade-offs

- **ezglossary still mangles option terms** (`<name:value>`): even with `.option`, `appendix/cli`/`libdoc` terms may render wrong on the ezglossary-enabled manual build. The content check (D8) + review (D5) will surface this; it is Group 2's problem, not this change's — flag it, don't try to fix it here.
- **Placeholder must survive every pass** (D7): the Private Use Area chars are inert to all ASCII markup regexes, but a fix script doing structural parsing could in theory reflow around them. Mitigated by `render_roles.py` running last and the content check (D8) verifying zero leftover placeholder chars.
- **Anchor/slug stability**: classing must not change heading slugs or anchors. The placeholder is shorter than the original `:role:` markup so headings are preserved; verify with a before/after anchor diff, the D8 heading-preservation check, and `mkdocs build --strict`.
- **Content-check false positives/negatives** (D8): aggressive normalization may over- or under-match. Tune tolerance conservatively (fail on real drops, allow benign formatting differences); the check augments — does not fully replace — a final human sign-off.
- **CSS drift between the two `extra.css` files**: the publish flow doesn't sync CSS today. Mitigated by including CSS in the delivery and noting a follow-up to teach the publish script to sync it.
- **Dark mode**: original CSS used its own vars; must map to Material's light/dark variables and verify both schemes in review.
