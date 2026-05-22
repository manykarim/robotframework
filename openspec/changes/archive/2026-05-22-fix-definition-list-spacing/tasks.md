## 1. CSS override

- [x] 1.1 Add `dl dt` and `dl dd` margin overrides to `doc/userguide-mkdocs/stylesheets/extra.css` to reduce spacing between definition list items

## 2. Verification

- [x] 2.1 Run `mkdocs build --strict` from `doc/userguide-mkdocs/` and confirm no errors
- [x] 2.2 Spot-check `creating-test-data/creating-test-cases/` in the rendered HTML and confirm `<dt>` elements have reduced top/bottom margin (no `<p>` nesting, no large gaps between items)
