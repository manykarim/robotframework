## Why

Our MkDocs site looks visually different from `pekkaklarck/manual` — different logo, different heading font, heavier custom CSS — so readers switching between the two notice inconsistency. Adding a PR preview closes the feedback loop: every PR touching docs gets a live URL to review before merging.

## What Changes

- **Logo and favicon**: replace the generic `material/robot` icon with the official RF logo assets (`logo-white.png`, `logo.png`) copied from the manual repo.
- **CSS**: replace our 240-line `extra.css` with the manual's minimal base (OCRA heading font, brand color, search-shortcut hint) plus our existing `dl dt/dd` spacing rules. Add the manual's `highlight-light.css` and `highlight-dark.css` for syntax highlighting.
- **`mkdocs.yml` theme config**: align palette (3-way auto/light/dark toggle), feature flags, highlight settings, plugin list, and social links with the manual. Remove the explicit `font` override (Material defaults are the same).
- **PR preview workflow**: extend `docs.yml` to deploy a `pr-{number}` mike version on every PR open/sync, post the preview URL as a PR comment, and delete the version when the PR closes.

## Capabilities

### New Capabilities

- `pr-preview-deployment`: every pull request touching `doc/userguide-mkdocs/**` gets a live preview at `https://manykarim.github.io/robotframework/pr-{number}/`, with a bot comment on the PR linking to it.

### Modified Capabilities

<!-- No spec-level requirement changes. -->

## Impact

- `doc/userguide-mkdocs/docs/assets/` — add `logo-white.png`, `logo.png`, `highlight-light.css`, `highlight-dark.css`
- `doc/userguide-mkdocs/docs/stylesheets/extra.css` — replaced with manual's base + dl spacing
- `doc/userguide-mkdocs/mkdocs.yml` — logo, palette, features, highlight, extra_css, plugins, social
- `doc/userguide-mkdocs/.github/workflows/docs.yml` — PR preview deploy + cleanup jobs
