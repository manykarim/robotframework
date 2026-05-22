# Migrating Robot Framework User Guide to Markdown: Feasibility and implementation plan

The Robot Framework User Guide can successfully migrate from reStructuredText to a Markdown-based static site generator, with **Material for MkDocs emerging as the clear recommendation**. The Robot Framework team is already testing this approach through Pekka Klarck's experimental repository at pekkaklarck.github.io/mkdocs-experiments. Native Robot Framework syntax highlighting, robust versioning via mike, and excellent Python ecosystem integration make MkDocs the optimal choice—though the project's transition to maintenance mode warrants attention.

## Current state analysis reveals specific conversion challenges

The Robot Framework User Guide uses **docutils directly** (not Sphinx), which presents unique conversion considerations. The documentation source lives in `doc/userguide/src/` with `RobotFrameworkUserGuide.rst` as the main file that includes section-specific files. Key technical characteristics that must be preserved include:

- **Custom roles** defined in `roles.rst` (`:setting:`, `:option:`, etc.) for consistent formatting
- **Sourcecode directives** with language specifications for Python and Robot Framework examples
- **Cross-references** using reST's `.. _label:` target and `:ref:` reference pattern
- **Build process** through custom `ug2html.py` script using Pygments for highlighting

A **2019 conversion attempt** documented in the pandoc-discuss mailing list encountered significant challenges, particularly with unresolved cross-references and loss of document structure. This attempt used `pandoc -f rst -t markdown+grid_tables` and produced "a bunch of warnings about unresolved references."

## Platform comparison favors Material for MkDocs

### Material for MkDocs earns the top recommendation

| Requirement | Material for MkDocs (v9.7.1) | Docusaurus (v3.9.2) | VitePress (v1.6.4) |
|-------------|------------------------------|---------------------|---------------------|
| Robot Framework highlighting | ✅ Native (Pygments) | ✅ Native (Prism.js) | ❌ Requires custom grammar |
| Version support | ✅ Native via mike | ✅ Native | ❌ Plugin required |
| Built-in search | ✅ lunr.js + Algolia option | ✅ Algolia DocSearch | ✅ MiniSearch |
| Python ecosystem | ✅ Native Python tooling | ⚠️ JavaScript/React | ⚠️ JavaScript/Vue |
| Build performance | Good (~0.5s typical) | Variable (can hit 26min for large versioned sites) | Excellent (~8-9s) |
| RF team experience | ✅ Active experimentation | Used for docs.robotframework.org guides | None |

**Critical consideration**: Material for MkDocs announced it's entering **maintenance mode** with the team shifting focus to Zensical, a new static site generator. Bug fixes and security patches will continue for at least 12 months, and all previously sponsor-only "Insiders" features are now free.

### Robot Framework syntax highlighting works natively in recommended platforms

Pygments includes a Robot Framework lexer since version 1.6, meaning **no additional configuration** is needed for MkDocs:

```yaml
# mkdocs.yml configuration for code highlighting
markdown_extensions:
  - pymdownx.highlight:
      anchor_linenums: true
  - pymdownx.superfences
```

Usage in Markdown is straightforward with the `robot` or `robotframework` language identifier:

````markdown
```robot
*** Test Cases ***
Valid Login
    Open Browser    ${LOGIN_URL}    chrome
    Input Text    id=username    ${VALID_USER}
    Click Button    id=login-button
    Page Should Contain    Welcome
```
````

Prism.js (used by Docusaurus) also includes native Robot Framework support. However, **Shiki** (used by VitePress) lacks Robot Framework grammar entirely, requiring extraction and adaptation of the TextMate grammar from VS Code extensions like RobotCode.

### Versioning implementation differs substantially across platforms

**MkDocs with mike** provides the most straightforward versioning workflow:

```bash
# Deploy a new version
mike deploy --push --update-aliases 7.0 latest

# Versions stored in gh-pages branch, no regeneration needed
mike list  # Shows: 7.0 [latest], 6.5, 6.4, dev
```

The URL structure becomes `https://robotframework.org/userguide/7.0/getting-started/` with a version dropdown automatically rendered in the header.

**Docusaurus** uses file-based versioning where `npm run docusaurus docs:version 7.0` copies the entire docs folder to `versioned_docs/version-7.0/`. Each version is a full copy, and build time scales linearly—sites with 360+ pages and multiple versions report **26-minute builds**.

**VitePress** has **no native versioning**, requiring third-party plugins like `vitepress-versioning-plugin` or manual deployment of separate sites per version.

## Conversion from reST to Markdown requires a hybrid approach

No single tool handles all reST constructs perfectly. The recommended pipeline combines automated conversion with targeted manual cleanup:

### Phase 1: Automated bulk conversion achieves approximately 80% accuracy

**Pandoc** remains the primary tool for initial conversion, despite known limitations:

```bash
pandoc -f rst -t gfm+grid_tables \
  RobotFrameworkUserGuide.rst \
  -o index.md \
  --extract-media=media \
  --standalone
```

**Known Pandoc limitations** for the Robot Framework User Guide:

| Construct | Pandoc Handling | Required Fix |
|-----------|-----------------|--------------|
| Custom roles (`:setting:`) | Outputs `<span class="setting">` | Post-process to inline code |
| `list-table` directive | Ignored entirely | Manual conversion |
| Cross-references (`.. _label:`) | Anchors lost | Add explicit HTML anchors |
| Include directives | Follows includes | May need restructuring |
| Code block options | Language preserved | Line numbers need attr syntax |

**rst-to-myst** is NOT recommended for MkDocs targets because MyST Markdown syntax (`{directive}` blocks) is designed for Sphinx and won't render correctly in MkDocs.

### Phase 2: Post-processing script handles systematic patterns

A Python script should convert predictable patterns automatically:

```python
import re

def convert_custom_roles(content):
    # :setting:`value` → `value` (inline code)
    content = re.sub(r':setting:`([^`]+)`', r'`\1`', content)
    # :option:`value` → `value`
    content = re.sub(r':option:`([^`]+)`', r'`\1`', content)
    return content

def convert_admonitions(content):
    # .. note:: → !!! note
    content = re.sub(
        r'\.\. note::\s*\n\s+(.+?)(?=\n\n)',
        r'!!! note\n    \1',
        content, flags=re.DOTALL
    )
    return content

def add_legacy_anchors(content, anchor_map):
    # Preserve original anchor names for backward compatibility
    for old_anchor, heading in anchor_map.items():
        content = content.replace(
            f'## {heading}',
            f'<a id="{old_anchor}"></a>\n\n## {heading}'
        )
    return content
```

### Phase 3: LLM-assisted cleanup handles complex constructs

For complex tables, nested structures, and ambiguous conversions, Claude or GPT-4 can process sections with context:

```
Convert this partially-converted reST to MkDocs-compatible Markdown:
- Convert list-table directives to pipe tables
- Ensure proper indentation in nested admonitions
- Preserve all code block language specifications
```

This hybrid approach addresses the **80/20 rule** observed in migrations: automated tools handle 80% of content, while the remaining 20% requires intelligent intervention.

## Implementation challenges require specific solutions

### Preserving URL compatibility for existing documentation links

The current User Guide at `robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html` is a **single HTML file** with fragment identifiers for sections. Migration to a multi-page structure requires:

1. **Redirect mapping** from old anchors to new pages using `mkdocs-redirects`:

```yaml
plugins:
  - redirects:
      redirect_maps:
        'RobotFrameworkUserGuide.html': 'index.md'
```

2. **Anchor aliasing** to preserve deep links—critical because many external resources link to specific sections:

```html
<!-- In new getting-started/index.md -->
<a id="Installation"></a>

## Installing Robot Framework
```

3. **Canonical URL strategy** publishing redirects at the old paths pointing to new canonical locations.

### Chapter splitting should follow existing section structure

The current User Guide source already uses includes, suggesting a natural split:

```yaml
# Proposed mkdocs.yml navigation structure
nav:
  - Home: index.md
  - Getting Started:
    - Introduction: getting-started/introduction.md
    - Installation: getting-started/installation.md
    - Demo: getting-started/demo.md
  - Creating Test Data:
    - Test Data Syntax: creating-test-data/syntax.md
    - Test Cases: creating-test-data/test-cases.md
    - Tasks: creating-test-data/tasks.md
  - Executing Tests:
    - Basic Usage: executing/basic-usage.md
    - Configuring Execution: executing/configuration.md
  # ... additional sections
```

Using `navigation.prune` in Material for MkDocs reduces HTML size by **33%+** for large sites, improving load times.

### CI/CD integration follows established patterns

The Robot Framework mkdocs-experiments repository demonstrates a working GitHub Actions workflow:

```yaml
name: Deploy Documentation
on:
  push:
    branches: [main]
    tags: ['v*']

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Needed for mike
      
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: pip install mkdocs-material mike robotframeworklexer
      
      - name: Configure git
        run: |
          git config user.name github-actions[bot]
          git config user.email github-actions[bot]@users.noreply.github.com
      
      - name: Deploy versioned docs
        run: |
          VERSION=${GITHUB_REF#refs/tags/v}
          mike deploy --push --update-aliases $VERSION latest
```

## Real-world migrations provide validated patterns

### Projects with successful Sphinx-to-MkDocs transitions

**pyjanitor** migrated in 2021, using `mkdocstrings` for API reference generation. Key lesson: they later proposed switching to Google-style docstrings because mkdocstrings handles them better than Sphinx-style (`:param:`, `:returns:`).

**EasyBuild** migrated from Sphinx/ReadTheDocs to MkDocs/GitHub Pages, successfully using `mkdocs-redirects` to preserve all existing URLs from the Sphinx structure.

**FastAPI** and **Pydantic** demonstrate Material for MkDocs at scale with multi-language support, extensive tutorials, and version management via mike. Their configurations at `github.com/fastapi/fastapi/blob/master/docs/en/mkdocs.yml` and `github.com/pydantic/pydantic/blob/main/mkdocs.yml` serve as reference implementations.

### Conversion tool success rates from migration reports

The `jodygarnett/translate` (`mkdocs_translate`) tool specifically designed for Sphinx-to-MkDocs migrations reports that **Pandoc gets ~90%** of content converted correctly. Remaining manual fixes typically involve:

- `{eval-rst}` blocks that need conversion to native Markdown
- Incorrect nested list indentation
- Sphinx-specific directives (`:guilabel:`, `:menuselection:`)

## Recommended implementation roadmap

### Phase 1: Foundation and analysis (Weeks 1-2)

**Week 1**: Inventory and preparation
- Audit all custom roles in `roles.rst` and create mapping table
- Catalog all directive types used (code-block, note, warning, include, etc.)
- Map all internal cross-reference targets and their usage frequency
- Set up MkDocs project structure mirroring existing section organization
- Create development environment with Material for MkDocs, mike, and robotframeworklexer

**Week 2**: Conversion pipeline development
- Build post-processing script for systematic pattern conversion
- Test Pandoc conversion on isolated sections
- Establish automated testing comparing rendered output to original HTML
- Document edge cases requiring manual intervention

### Phase 2: Content migration (Weeks 3-5)

**Week 3**: Core content conversion
- Convert main sections through automated pipeline
- Process Getting Started and Creating Test Data sections
- Verify Robot Framework code block rendering
- Test internal linking between converted pages

**Week 4**: Complex section handling
- Convert sections with heavy table usage (API documentation, option references)
- Handle sections with extensive cross-references
- Apply LLM-assisted cleanup for problematic constructs
- Preserve legacy anchors for backward compatibility

**Week 5**: Completion and version setup
- Convert remaining sections (Supporting Tools, Extending Robot Framework)
- Configure mike for version management
- Set up version dropdown and warning banners for outdated versions
- Create redirect mappings from old URL structure

### Phase 3: Validation and deployment (Weeks 6-7)

**Week 6**: Testing and quality assurance
- Run comprehensive link checker (internal and external)
- Visual comparison against original documentation
- Test all code examples for correct highlighting
- Verify search functionality covers all content
- User acceptance testing with Robot Framework community members

**Week 7**: Deployment and monitoring
- Deploy to staging environment for final review
- Configure GitHub Actions for automated deployment
- Set up version 7.0 (or current) as initial release
- Publish redirects from old documentation URLs
- Monitor for 404 errors from external links
- Create contribution guidelines for Markdown workflow

### Rollback considerations

Maintain the existing reST build process in parallel for at least **two release cycles**. The `ug2html.py` script and source files should remain functional as a fallback. If critical issues emerge:

1. Continue publishing from reST source at the primary URL
2. Make MkDocs version available at an alternate path (e.g., `/userguide-beta/`)
3. Collect feedback and iterate before full transition

## Key risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Material for MkDocs maintenance mode | Medium | Medium | 12+ months of support; migration to Zensical possible if needed; core MkDocs remains active |
| Cross-reference breakage | High | High | Automated anchor mapping; preserve all legacy IDs; comprehensive link testing |
| Community disruption | Medium | Medium | Beta period with parallel systems; clear communication; contribution documentation |
| Complex table conversion | High | Low | LLM-assisted conversion; manual review of data-heavy sections |
| Build time regression | Low | Low | MkDocs build times typically excellent; navigation.prune for optimization |

## Conclusion: Migration is feasible with Material for MkDocs as the optimal choice

The combination of **native Robot Framework syntax highlighting**, **robust versioning via mike**, **Python ecosystem integration**, and the **existing experimentation by the Robot Framework team** makes Material for MkDocs the clear recommendation. The maintenance mode announcement is a consideration but not a blocker—12+ months of support provides adequate runway, and the broader MkDocs ecosystem remains healthy.

Estimated total effort for production-ready migration: **6-8 weeks** with a small team (2-3 contributors), or **10-12 weeks** for a single developer working part-time. The largest variable is the manual cleanup of complex constructs—the automated pipeline handles approximately 80% of content, but the remaining 20% requires careful human review to maintain the User Guide's reputation for accuracy and clarity.