## Context

`pekkaklarck/manual` uses a minimal CSS approach: ~30 lines of `extra.css` (OCRA font for `h1`, `#00c0b5` primary colour, search-shortcut visual) plus two pre-generated highlight CSS files. Our `extra.css` grew to 240 lines with manual overrides for colours, headers, navigation, tables and more — none of which are in the manual and most of which duplicate what Material theme already provides.

The manual's `properdocs.yml` also differs from our `mkdocs.yml` in palette structure (3-way toggle vs 2-way), navigation feature flags, highlight settings, logo/favicon, and social links.

The PR preview will use `mike deploy pr-{number}` to publish a versioned copy of the site on the existing `gh-pages` branch, exactly like the `dev` and tagged-release deployments already work.

## Goals / Non-Goals

**Goals:**
- Visual parity with `pekkaklarck/manual`: same logo, same heading font (OCRA), same brand colour treatment, same highlight CSS.
- Preserve our one custom addition: `dl dt/dd` spacing rules.
- Align `mkdocs.yml` feature flags, palette, and highlight settings with the manual.
- Live preview URL for every PR touching `doc/userguide-mkdocs/**`, posted as a PR comment.
- Automatic cleanup of the preview version when the PR closes.

**Non-Goals:**
- Adopting the manual's nav structure or section names (ours differ intentionally).
- Copying manual-specific plugins (`gen-files`, `mkdocstrings`, `literate-nav`, `ezglossary`) — all depend on the manual's Python source.
- Changing content or page structure.

## Decisions

**Replace `extra.css` entirely, not patch it**

The manual's 30-line CSS is the authoritative style. Our 240-line version adds nothing useful on top and would drift further over time. The only thing worth preserving is the `dl` spacing block (12 lines). Result: ~42 lines total, no dead code.

**Copy highlight CSS files verbatim from the manual**

`highlight-light.css` and `highlight-dark.css` are pre-generated from Pygments and live in `doc/manual/docs/assets/`. Copying them means our syntax highlighting matches the manual exactly. They go into `docs/assets/` (no new directory needed).

**Logo from GitHub raw URLs, downloaded at apply time**

Both PNG files are binary. Downloading them via `curl` during implementation is cleaner than describing binary content. Source URLs:
- `https://raw.githubusercontent.com/pekkaklarck/manual/main/doc/manual/docs/assets/logo-white.png`
- `https://raw.githubusercontent.com/pekkaklarck/manual/main/doc/manual/docs/assets/logo.png`

**`extra_css` order in `mkdocs.yml`**

```yaml
extra_css:
  - assets/highlight-light.css
  - assets/highlight-dark.css
  - assets/extra.css
```

Mirrors the manual's exact order. Our `extra.css` (now at `assets/extra.css`, moved from `stylesheets/`) is last so our `dl` rules win over any upstream overrides.

**`mkdocs.yml` feature flag changes**

Remove (not in manual): `navigation.tabs.sticky`, `navigation.prune`, `navigation.path`, `toc.follow`, `navigation.tracking`, `navigation.instant.prefetch`, `search.share`, `content.action.view`.  
Add (manual has, we don't): `navigation.instant.progress`.  
Remove explicit `font` block — Material defaults to Roboto/Roboto Mono anyway.

**Highlight settings align with manual**

```yaml
pymdownx.highlight:
  default_lang: python
  linenums: true
  anchor_linenums: true
  line_anchors: example
  line_spans: line
```

`auto_title: false` stays (we set it intentionally in a previous change).

**PR preview: `pr-{number}` mike version, comment on PR, delete on close**

Three additions to `docs.yml`:
1. In `build-check` job: no change needed (already runs on PRs).
2. New `pr-preview` job: needs `build-check`, runs on `pull_request` event (open/sync), deploys with `mike deploy --push pr-${{ github.event.number }}`, then posts a comment via `gh pr comment`.
3. New `pr-cleanup` job: runs on `pull_request` closed event, deletes the mike version with `mike delete --push pr-${{ github.event.number }}`.

Preview URL pattern: `https://manykarim.github.io/robotframework/pr-{number}/`

## Risks / Trade-offs

- **OCRA font**: The manual serves OCRA from its `overrides/` directory. We don't have that. If OCRA isn't loaded, `h1` falls back to the browser's monospace font — still readable, just not the brand font. We can live with this until we add the font file.
- **`stylesheets/` → `assets/` move**: `extra.css` moves path. Any external reference to the old URL breaks, but that's only relevant if someone linked directly to the CSS — acceptable.
- **Mike version accumulation**: Abandoned PRs (never closed via GitHub UI) will leave orphan preview versions. Low risk given commit cadence; can be cleaned up manually with `mike delete`.
- **`gh pr comment` token**: The `docs.yml` `pull_request` event uses the default `GITHUB_TOKEN`, which has write access to PR comments on the same repo — no additional secret needed.
