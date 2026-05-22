## 1. Configuration change

- [x] 1.1 In `doc/userguide-mkdocs/mkdocs.yml`, set `auto_title: true` → `auto_title: false` under `pymdownx.highlight`

## 2. Verification

- [x] 2.1 Run `mkdocs build --strict` from `doc/userguide-mkdocs/` and confirm no errors
- [x] 2.2 Spot-check a rendered page (e.g., `creating-test-data/test-data-syntax/`) and confirm code blocks no longer show a language title bar
