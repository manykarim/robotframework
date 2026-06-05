## 1. Download assets from pekkaklarck/manual

- [x] 1.1 Download `logo-white.png` from the manual repo to `doc/userguide-mkdocs/docs/assets/logo-white.png`
- [x] 1.2 Download `logo.png` from the manual repo to `doc/userguide-mkdocs/docs/assets/logo.png`
- [x] 1.3 Download `highlight-light.css` from the manual repo to `doc/userguide-mkdocs/docs/assets/highlight-light.css`
- [x] 1.4 Download `highlight-dark.css` from the manual repo to `doc/userguide-mkdocs/docs/assets/highlight-dark.css`

## 2. Replace extra.css

- [x] 2.1 Replace `doc/userguide-mkdocs/docs/stylesheets/extra.css` with the manual's `extra.css` content (OCRA font for h1, `#00c0b5` brand colour, search-shortcut block) plus the existing `dl dt/dd` spacing rules appended at the end
- [x] 2.2 Delete the old `doc/userguide-mkdocs/docs/stylesheets/` directory (or leave empty — the CSS moves to `assets/extra.css`). Update `mkdocs.yml` to point to `assets/extra.css` instead.

## 3. Update mkdocs.yml

- [x] 3.1 Update logo and favicon: `logo: assets/logo-white.png`, `favicon: assets/logo.png`
- [x] 3.2 Update `extra_css` to: `assets/highlight-light.css`, `assets/highlight-dark.css`, `assets/extra.css` (in that order)
- [x] 3.3 Update palette to 3-way toggle (auto/light/dark) matching the manual
- [x] 3.4 Update `features` list: remove `navigation.tabs.sticky`, `navigation.prune`, `navigation.path`, `toc.follow`, `navigation.tracking`, `navigation.instant.prefetch`, `search.share`, `content.action.view`; add `navigation.instant.progress`
- [x] 3.5 Remove explicit `font` block
- [x] 3.6 Update `pymdownx.highlight` settings: `default_lang: python`, `linenums: true`, `anchor_linenums: true`, `line_anchors: example`, `line_spans: line` (keep `auto_title: false`)
- [x] 3.7 Update social links: replace Twitter with Discourse (`https://forum.robotframework.org`) and add LinkedIn (`https://linkedin.com/company/robot-framework-foundation`)
- [x] 3.8 Add `section-index` plugin to the plugins list (+ add `mkdocs-section-index>=0.3.0` to pyproject.toml)

## 4. Add PR preview to docs.yml workflow

- [x] 4.1 Add `pr-preview` job to `.github/workflows/docs.yml`: triggers on `pull_request` to master, needs `build-check`, runs `mike deploy --push pr-${{ github.event.number }}`, then posts PR comment with preview URL via `gh pr comment`
- [x] 4.2 Add `pr-cleanup` job: triggers on `pull_request` closed event (types: [closed]), runs `mike delete --push pr-${{ github.event.number }}`

## 5. Verification

- [x] 5.1 Run `mkdocs build --strict` from `doc/userguide-mkdocs/` and confirm no errors
- [ ] 5.2 Serve locally (`mkdocs serve`) and confirm logo, OCRA heading font, and syntax highlighting match the manual's visual style
