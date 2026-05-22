# Contributing to Robot Framework Documentation

Thank you for your interest in improving the Robot Framework User Guide. This document explains how to contribute to the documentation.

## Prerequisites

Before you begin, ensure you have:

- **Python 3.10+** installed
- **uv** package manager (recommended) or pip
- **Git** for version control
- A text editor with Markdown support (VS Code, PyCharm, etc.)

### Installing uv

If you don't have uv installed:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/robotframework/robotframework.git
cd robotframework/doc/userguide-mkdocs
```

### 2. Install Dependencies

Using uv (recommended):
```bash
uv sync
```

Using pip:
```bash
pip install -e ".[dev]"
```

### 3. Start the Development Server

```bash
uv run mkdocs serve
```

Or with pip:
```bash
mkdocs serve
```

The documentation will be available at `http://127.0.0.1:8000/`. The server automatically reloads when you save changes.

## Project Structure

```
doc/userguide-mkdocs/
  mkdocs.yml              # MkDocs configuration
  pyproject.toml          # Python dependencies
  CONTRIBUTING.md         # This file
  MIGRATION.md            # Migration guide
  docs/                   # Documentation source files
    index.md              # Home page
    getting-started/      # Getting Started section
    creating-test-data/   # Creating Test Data section
    executing-tests/      # Executing Tests section
    extending/            # Extending Robot Framework section
    supporting-tools/     # Supporting Tools section
    appendices/           # Appendices
  scripts/                # Build and conversion utilities
```

## Writing Documentation

### Markdown Syntax

We use GitHub Flavored Markdown with MkDocs extensions. Key elements:

#### Headings

```markdown
# Page Title (H1 - only one per page)

## Major Section (H2)

### Subsection (H3)

#### Minor Subsection (H4)
```

#### Code Blocks

For Robot Framework code:
````markdown
```robot
*** Test Cases ***
Example Test
    Log    Hello World
    Should Be Equal    ${result}    expected
```
````

For Python code:
````markdown
```python
from robot.api import logger

def my_keyword(arg):
    logger.info(f"Argument: {arg}")
```
````

For command line examples:
````markdown
```bash
robot --outputdir results tests/
```
````

#### Inline Code and Formatting
| Element | Syntax | Renders As |
|---------|--------|------------|
| Inline code | `` `robot` `` | `robot` |
| Bold | `**bold**` | **bold** |
| Italic | `*italic*` | *italic* |
| Setting names | `*Library*` | *Library* |
| Command options | `` `--output` `` | `--output` |
| File paths | `*path/to/file*` | *path/to/file* |

#### Admonitions

Use admonitions to highlight important information:

```markdown
!!! note
    This is a note with additional information.

!!! warning
    This is a warning about potential issues.

!!! tip
    This is a helpful tip.

!!! danger
    This is a critical warning.
```

With custom titles:
```markdown
!!! note "Custom Title"
    Content with a custom title.
```

Collapsible admonitions:
```markdown
??? note "Click to expand"
    This content is hidden by default.

???+ note "Expanded by default"
    This content is visible but can be collapsed.
```

#### Tables

```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Cell 1   | Cell 2   | Cell 3   |
| Cell 4   | Cell 5   | Cell 6   |
```

#### Links

Internal links (to other documentation pages):
```markdown
[Installation Guide](getting-started/installation.md)
[Variables section](creating-test-data/variables.md#scalar-variables)
```

External links:
```markdown
[Robot Framework Website](https://robotframework.org)
```

#### Images

```markdown
![Alt text](../images/screenshot.png)
```

### Style Guidelines

1. **Use active voice**: "Robot Framework executes tests" not "Tests are executed by Robot Framework"

2. **Be concise**: Avoid unnecessary words and repetition

3. **Use consistent terminology**:
   - "test case" (not "testcase" or "test-case")
   - "keyword" (not "key word")
   - "test suite" (not "testsuite")
   - "user keyword" (not "user-keyword" or "userkeyword")
   - "test library" (not "testlibrary" or "test-library")
   - "resource file" (not "resourcefile")
   - "variable file" (not "variablefile")

4. **Code examples should be complete and runnable** when possible

5. **Include the `robot` language identifier** for all Robot Framework code blocks

6. **Preserve legacy anchors** when editing existing sections to maintain external link compatibility:
   ```html
   <a id="LegacyAnchorName"></a>

   ## New Section Title
   ```

### Code Block Language Conventions

Always specify a language identifier for code blocks. Use these standard identifiers:
| Language | Identifier | Usage |
|----------|------------|-------|
| Robot Framework | `robot` or `robotframework` | Test cases, keywords, resource files |
| Python | `python` | Library code, API examples |
| Bash/Shell | `bash` or `console` | Command line examples |
| XML | `xml` | Configuration files, output.xml examples |
| HTML | `html` | Report examples, HTML documentation |
| JSON | `json` | Data files, API responses |
| YAML | `yaml` | Configuration examples |
| Plain text | `text` | Generic output, non-code content |

**Examples:**

````markdown
Robot Framework test case:
```robot
*** Test Cases ***
Example Test
    Log    Hello World
    Should Be Equal    ${result}    expected
```

Python library:
```python
from robot.api.deco import keyword

class MyLibrary:
    @keyword
    def my_keyword(self, arg):
        return arg.upper()
```

Command line:
```bash
robot --outputdir results tests/
rebot --merge output1.xml output2.xml
```

Configuration:
```yaml
settings:
  timeout: 30s
  retries: 3
```
````

### Admonition Usage

Use admonitions to highlight important information. Available types:
| Type | Usage | Color |
|------|-------|-------|
| `note` | General information, additional context | Blue |
| `tip` | Helpful suggestions, best practices | Green |
| `warning` | Important cautions, potential issues | Orange |
| `danger` | Critical warnings, destructive actions | Red |
| `info` | Informational content | Cyan |
| `success` | Positive outcomes, confirmations | Green |
| `question` | FAQs, common questions | Green |
| `quote` | Quotations, citations | Gray |

**Basic syntax:**

```markdown
!!! note
    This is a note with important information.
    It can span multiple lines.

!!! warning
    Be careful when using this feature.
```

**With custom title:**

```markdown
!!! note "Important Information"
    Custom title replaces the default "Note" header.
```

**Collapsible admonitions:**

```markdown
??? note "Click to expand"
    This content is hidden by default.
    Users must click to reveal it.

???+ note "Expanded by default"
    This content is visible initially.
    Users can click to collapse it.
```

**Guidelines for admonition use:**

1. **note**: Use for supplementary information that enhances understanding
2. **tip**: Use for suggestions that improve workflow or outcomes
3. **warning**: Use for potential pitfalls or deprecated features
4. **danger**: Use sparingly for actions that could cause data loss or security issues

**Avoid:**
- Nesting admonitions within admonitions
- Using admonitions for content that should be in the main text
- Overusing danger/warning (dilutes their impact)
- Empty or single-word admonitions

### Formatting Reference

**Setting names:**
```markdown
The *Library* setting imports test libraries.
Use *Resource* to import resource files.
```

**Command line options:**
```markdown
Use `--outputdir` to specify the output directory.
The `-i` option includes tags.
```

**File paths:**
```markdown
Edit the file at *tests/example.robot*.
The configuration is in *robot.yaml*.
```

**Keyboard shortcuts:**
```markdown
Press ++ctrl+c++ to copy.
Use ++ctrl+shift+p++ to open the command palette.
```

**Variable syntax:**
```markdown
The variable `${VARIABLE}` contains the value.
List variables use `@{LIST}` syntax.
Dictionary variables use `&{DICT}` syntax.
```

### Navigation Structure

The navigation is defined in `mkdocs.yml`. When adding new pages:

1. Create the Markdown file in the appropriate directory
2. Add the page to the `nav` section in `mkdocs.yml`
3. Ensure consistent naming (lowercase, hyphens for spaces)

Example `mkdocs.yml` navigation entry:
```yaml
nav:
  - Getting Started:
    - getting-started/index.md
    - Introduction: getting-started/introduction.md
    - Installation: getting-started/installation.md
```

## Adding New Content

### Adding a New Page

1. **Create the Markdown file** in the appropriate section directory:
   ```bash
   touch docs/creating-test-data/new-topic.md
   ```

2. **Add frontmatter** (optional but recommended for search):
   ```markdown
   ---
   title: New Topic
   description: Brief description for search results
   ---

   # New Topic

   Content goes here...
   ```

3. **Update navigation** in `mkdocs.yml`:
   ```yaml
   nav:
     - Creating Test Data:
       - creating-test-data/index.md
       - New Topic: creating-test-data/new-topic.md  # Add this line
   ```

4. **Add to section index** (docs/creating-test-data/index.md):
   ```markdown
| [New Topic](new-topic.md) | Description of the new topic |
|---|---|
   ```

5. **Build and verify**:
   ```bash
   uv run mkdocs serve
   # Check the page at http://127.0.0.1:8000/creating-test-data/new-topic/
   ```

### Adding a New Section

1. **Create the section directory**:
   ```bash
   mkdir docs/new-section
   ```

2. **Create the section index**:
   ```bash
   touch docs/new-section/index.md
   ```

3. **Write the index content**:
   ```markdown
   # New Section

   Overview of this section.

   ## Topics
| Topic | Description |
|-------|-------------|
| [First Topic](first-topic.md) | Description |
| [Second Topic](second-topic.md) | Description |
   ```

4. **Create topic pages**:
   ```bash
   touch docs/new-section/first-topic.md
   touch docs/new-section/second-topic.md
   ```

5. **Update navigation** in `mkdocs.yml`:
   ```yaml
   nav:
     - New Section:
       - new-section/index.md
       - First Topic: new-section/first-topic.md
       - Second Topic: new-section/second-topic.md
   ```

### Adding Images

1. **Place images** in the same directory as the Markdown file:
   ```
   docs/executing-tests/
       output-files.md
       log_passed.png    # Image file
       report_failed.png # Image file
   ```

2. **Reference images** with relative paths:
   ```markdown
   ![Log file example](log_passed.png)
   ```

3. **Use descriptive alt text** for accessibility:
   ```markdown
   ![Robot Framework log file showing passed test with green checkmark](log_passed.png)
   ```

4. **Optimize images** before committing:
   - Use PNG for screenshots and diagrams
   - Use WebP for photos (if browser support is acceptable)
   - Keep images under 500KB when possible

### Updating Existing Content

1. **Locate the source file** in `docs/`
2. **Edit the Markdown** directly
3. **Preserve legacy anchors** if the section existed in the original User Guide:
   ```html
   <a id="OriginalSectionName"></a>

   ## Updated Section Title
   ```
4. **Test your changes** with `uv run mkdocs serve`
5. **Verify links** still work after edits

## Testing Your Changes

### Build Validation

Before submitting, verify the build succeeds:

```bash
uv run mkdocs build --strict
```

The `--strict` flag treats warnings as errors.

### Link Checking

Check for broken links:

```bash
# Install linkchecker if not available
pip install linkchecker

# Run against the built site
uv run mkdocs build
linkchecker site/index.html
```

### Visual Inspection

1. Start the development server: `uv run mkdocs serve`
2. Review your changes in a browser
3. Check both light and dark themes
4. Test on mobile viewport sizes
5. Verify code blocks render with proper highlighting

## Submitting Changes

### 1. Create a Branch

```bash
git checkout -b docs/your-feature-name
```

### 2. Make Your Changes

Edit the Markdown files as needed.

### 3. Commit Your Changes

Write clear, descriptive commit messages:

```bash
git add docs/path/to/changed/file.md
git commit -m "docs: Update installation instructions for Python 3.12"
```

Follow the commit message convention:
- `docs:` for documentation changes
- `fix:` for fixing documentation errors
- `feat:` for new documentation features

### 4. Push and Create a Pull Request

```bash
git push origin docs/your-feature-name
```

Then create a pull request on GitHub with:
- Clear title describing the change
- Description of what was changed and why
- Reference to any related issues

### Pull Request Checklist

- [ ] Build passes (`mkdocs build --strict`)
- [ ] Changes render correctly locally
- [ ] Links are not broken
- [ ] Code examples are correct and complete
- [ ] Follows style guidelines
- [ ] Legacy anchors preserved if editing existing content

## Versioning

Documentation versions are managed by `mike`. Contributors typically don't need to worry about versioning - the CI/CD pipeline handles this automatically.

For maintainers deploying new versions:

```bash
# Deploy a new version
mike deploy --push --update-aliases 7.1 latest

# View deployed versions
mike list
```

## Getting Help

If you have questions about contributing:

1. Check existing documentation and this guide
2. Search [GitHub Issues](https://github.com/robotframework/robotframework/issues)
3. Ask in [GitHub Discussions](https://github.com/robotframework/robotframework/discussions)
4. Join the Robot Framework Slack community

## Advanced Topics

### Converting from reST

If you need to convert existing reST content, use the conversion script:

```bash
python scripts/convert_rst.py input.rst output.md
```

The script handles:
- Custom role conversion
- Admonition transformation
- Code block formatting
- Basic cross-reference resolution

Manual review is required for:
- Complex tables
- Nested structures
- Cross-references to other documents

### Running the Full Conversion Pipeline

For bulk conversion of multiple files:

```bash
# Convert all RST files in a directory
python scripts/batch_convert.py ../userguide/src/GettingStarted/ docs/getting-started/

# Post-process for MkDocs compatibility
python scripts/post_process.py docs/getting-started/
```

### Building for Production

```bash
# Build optimized production site
uv run mkdocs build --strict

# Output is in the site/ directory
```

## License

By contributing to the Robot Framework documentation, you agree that your contributions will be licensed under the same license as the Robot Framework project (Apache License 2.0).
