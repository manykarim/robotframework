# ADR-002: Documentation Comparison Tool Architecture

## Status

**Proposed** | Draft Date: 2026-01-28

## Context

### Problem Statement

The Robot Framework project has migrated its User Guide from reStructuredText/docutils to MkDocs Markdown (ADR-001). This migration involves:

- Converting 37 RST source files to 42 Markdown files
- Transforming a single 500KB+ HTML output into a multi-page static site
- Preserving 334 legacy anchor mappings for URL compatibility
- Maintaining semantic equivalence across format boundaries

A systematic comparison tool is required to:

1. **Validate migration completeness**: Ensure no content was lost during conversion
2. **Detect content drift**: Identify divergence if both formats are maintained in parallel
3. **Support regression testing**: Enable CI integration to catch accidental regressions
4. **Audit structural fidelity**: Verify headings, code blocks, tables, and admonitions match

### Forces at Play

| Force | Impact | Direction |
|-------|--------|-----------|
| Format heterogeneity | High | Comparing single-page HTML vs. multi-page Markdown requires abstraction |
| Semantic vs. syntactic | High | Visual equivalence may differ from source equivalence |
| CI/CD integration | Medium | Tool must produce machine-readable output with exit codes |
| No external dependencies | High | Robot Framework project policy requires stdlib-only Python |
| Performance | Medium | Full comparison should complete in seconds, not minutes |
| Maintainability | Medium | Tool should be understandable by volunteer contributors |
| Extensibility | Low | Future documentation formats (e.g., AsciiDoc) are unlikely but possible |

### Existing Infrastructure

The migration project already has:

- `scripts/convert.py` - RST to Markdown conversion pipeline
- `scripts/anchor_map.json` - Legacy anchor to new path mappings
- `scripts/fix_*.py` - Post-processing scripts for various fixes
- `redirects.yml` - 334 redirect mappings for legacy URLs

## Decision Drivers

1. **Zero external dependencies**: The comparison tool must use only Python standard library modules to maintain the project's dependency-minimal philosophy

2. **High accuracy for content equivalence**: False positives (reporting differences that don't matter) waste reviewer time; false negatives (missing real differences) defeat the tool's purpose

3. **Machine-readable output**: CI/CD integration requires structured output (JSON, exit codes) alongside human-readable reports

4. **Bidirectional comparison**: Support comparing RST source to Markdown source, AND comparing rendered HTML outputs

5. **Granular difference reporting**: Identify specific sections, paragraphs, or blocks that differ, not just "files are different"

6. **Claude-flow integration**: Leverage memory patterns for learned comparison heuristics and agent coordination for parallel processing

## Considered Options

### Option A: Rendered HTML Comparison

**Approach**: Build both documentation formats to HTML, then compare the rendered DOM structures.

```
RST Source --> ug2html.py --> HTML Output A
                                    |
                                    v
                              DOM Comparison <-- Difference Report
                                    ^
                                    |
MD Source --> mkdocs build --> HTML Output B
```

**Implementation**:
- Use `html.parser` (stdlib) to parse both HTML outputs
- Normalize DOM trees (remove whitespace, sort attributes)
- Compare element-by-element with configurable ignore rules
- Generate visual diff report

**Pros**:
- Compares what users actually see
- Catches rendering issues (CSS, JavaScript, theme)
- Format-agnostic at comparison layer

**Cons**:
- Heavy build step required for each comparison
- Slow (full build of both formats: ~10+ seconds)
- Theme differences create noise (Material vs. docutils CSS)
- Doesn't identify source-level issues for contributors to fix
- Single-page vs. multi-page structure complicates alignment

**Estimated Accuracy**: 85% (theme differences create false positives)
**Estimated Speed**: 15-30 seconds per full comparison

### Option B: Source-Level Semantic Comparison

**Approach**: Parse both RST and Markdown into a common Intermediate Representation (IR), then compare normalized semantic blocks.

```
RST Source --> RST Parser --> IR Document A
                                    |
                                    v
                              IR Comparison <-- Difference Report
                                    ^
                                    |
MD Source --> MD Parser --> IR Document B
```

**Implementation**:
- Define a document IR schema (headings, paragraphs, code blocks, tables, admonitions, links)
- Implement RST parser using `docutils` (already available in project) or regex patterns
- Implement Markdown parser using regex patterns (stdlib only)
- Normalize both to IR, then compare block-by-block
- Use sequence alignment algorithms for section matching

**Pros**:
- Fast (no build step, parsing only)
- Identifies exact source locations for fixes
- Format-agnostic IR enables future format support
- Catches semantic issues invisible in rendered output

**Cons**:
- Complex parsing logic, especially for edge cases
- May miss rendering-specific issues
- Requires maintaining parsers for both formats
- RST custom roles require special handling

**Estimated Accuracy**: 92% (parsing edge cases reduce accuracy)
**Estimated Speed**: 1-3 seconds per full comparison

### Option C: Hybrid Approach (Recommended)

**Approach**: Primary comparison at source/IR level with selective rendered HTML validation for high-value sections.

```
                    +---> RST Parser ---> IR A ---+
RST Source ---------+                             |
                    +---> ug2html.py --> HTML A --+---> Comparison Engine
                                                  |         |
MD Source ----------+                             |         v
                    +---> MD Parser ---> IR B ----+    Unified Report
                    +---> mkdocs build -> HTML B -+
```

**Implementation**:
- **Layer 1 (Primary)**: Source-level semantic comparison via IR
- **Layer 2 (Validation)**: Rendered HTML spot-checks for critical sections
- **Layer 3 (Link Audit)**: Cross-reference and anchor validation
- Configurable profiles: `--fast` (Layer 1 only), `--full` (all layers)

**Pros**:
- Best of both worlds: speed and accuracy
- Fast feedback for contributors (Layer 1)
- Thorough validation for releases (all layers)
- Extensible architecture for additional checks

**Cons**:
- Most complex to implement
- Multiple code paths to maintain
- Configuration complexity

**Estimated Accuracy**: 97% (layered approach catches most issues)
**Estimated Speed**: 2-5 seconds (fast mode), 20-40 seconds (full mode)

## Decision

**We will implement Option C: Hybrid Approach** with the following architecture.

### Rationale

1. **Speed matters for contributor workflow**: Developers need fast feedback when editing documentation. Source-level comparison (Layer 1) provides sub-3-second results.

2. **Accuracy matters for releases**: Before publishing, we need high confidence that no content was lost. Rendered comparison (Layer 2) catches rendering-specific issues.

3. **Link integrity is critical**: ADR-001 identified 334 legacy anchors that must remain functional. A dedicated link audit layer ensures this.

4. **Extensibility for claude-flow**: The layered architecture maps naturally to agent specialization (parser agents, comparison agents, link auditor agents).

5. **Stdlib-only constraint is satisfied**: All parsing can be done with `html.parser`, `re`, and `json` modules.

## Technical Approach

### Document Intermediate Representation (IR) Schema

```python
@dataclass
class DocumentIR:
    """Intermediate Representation for documentation content."""
    source_path: str
    source_format: Literal["rst", "markdown", "html"]
    title: str
    blocks: List[Block]
    metadata: Dict[str, Any]

@dataclass
class Block:
    """Base class for document blocks."""
    block_type: str
    content: str
    line_number: int
    attributes: Dict[str, Any]
    children: List["Block"]

# Block Types
class HeadingBlock(Block):
    block_type = "heading"
    level: int  # 1-6
    anchor_id: Optional[str]

class ParagraphBlock(Block):
    block_type = "paragraph"

class CodeBlock(Block):
    block_type = "code"
    language: str
    line_numbers: bool

class TableBlock(Block):
    block_type = "table"
    headers: List[str]
    rows: List[List[str]]

class AdmonitionBlock(Block):
    block_type = "admonition"
    admonition_type: str  # note, warning, tip, etc.
    title: Optional[str]

class ListBlock(Block):
    block_type = "list"
    ordered: bool
    items: List[str]

class LinkBlock(Block):
    block_type = "link"
    url: str
    text: str
    is_internal: bool
```

### Extraction Strategies

#### RST Extraction

```python
class RstExtractor:
    """Extract IR from reStructuredText source files."""

    HEADING_PATTERNS = [
        (r'^(.+)\n={3,}$', 1),   # Title (=)
        (r'^(.+)\n-{3,}$', 2),   # Section (-)
        (r'^(.+)\n~{3,}$', 3),   # Subsection (~)
    ]

    DIRECTIVE_PATTERN = r'^\.\. (\w+)::\s*(.*?)$'

    def extract(self, source: str, path: str) -> DocumentIR:
        blocks = []
        # Parse headings, directives, code blocks, etc.
        # Handle custom roles: :setting:, :option:, :file:, :name:, :codesc:
        return DocumentIR(
            source_path=path,
            source_format="rst",
            title=self._extract_title(source),
            blocks=blocks,
            metadata={}
        )
```

#### Markdown Extraction

```python
class MarkdownExtractor:
    """Extract IR from Markdown source files."""

    HEADING_PATTERN = r'^(#{1,6})\s+(.+)$'
    CODE_FENCE_PATTERN = r'^```(\w*)\n(.*?)^```'
    ADMONITION_PATTERN = r'^!!!\s+(\w+)(?:\s+"([^"]+)")?\n((?:\s{4}.+\n)+)'

    def extract(self, source: str, path: str) -> DocumentIR:
        blocks = []
        # Parse ATX headings, fenced code, admonitions, tables
        # Handle MkDocs-specific syntax
        return DocumentIR(
            source_path=path,
            source_format="markdown",
            title=self._extract_title(source),
            blocks=blocks,
            metadata={}
        )
```

#### HTML Extraction

```python
class HtmlExtractor:
    """Extract IR from rendered HTML output."""

    def extract(self, html_content: str, path: str) -> DocumentIR:
        parser = HTMLContentParser()
        parser.feed(html_content)
        # Convert parsed elements to IR blocks
        return DocumentIR(
            source_path=path,
            source_format="html",
            title=parser.title,
            blocks=parser.blocks,
            metadata={"anchors": parser.anchors}
        )
```

### Alignment Algorithm

The comparison engine uses a modified Longest Common Subsequence (LCS) algorithm optimized for document blocks:

```python
class BlockAligner:
    """Align blocks between two documents for comparison."""

    def align(self, doc_a: DocumentIR, doc_b: DocumentIR) -> List[AlignedPair]:
        """
        Returns aligned block pairs with match status.

        Uses heading structure as primary alignment anchors,
        then aligns content blocks within each section.
        """
        # Phase 1: Align by heading structure
        heading_alignment = self._align_headings(doc_a, doc_b)

        # Phase 2: Align content within sections
        aligned_pairs = []
        for section_a, section_b in heading_alignment:
            section_pairs = self._align_section_content(section_a, section_b)
            aligned_pairs.extend(section_pairs)

        return aligned_pairs

    def _similarity_score(self, block_a: Block, block_b: Block) -> float:
        """
        Calculate similarity between two blocks.

        - Same type: +0.3
        - Content similarity (normalized Levenshtein): +0.7 * ratio
        - Same attributes: +0.1 bonus
        """
        if block_a.block_type != block_b.block_type:
            return 0.0

        type_score = 0.3
        content_score = 0.7 * self._text_similarity(
            block_a.content, block_b.content
        )
        attr_score = 0.1 if block_a.attributes == block_b.attributes else 0.0

        return type_score + content_score + attr_score
```

### Scoring Methodology

#### Block-Level Scoring

| Match Type | Score | Description |
|------------|-------|-------------|
| Exact Match | 1.0 | Identical block type and content |
| Near Match | 0.8-0.99 | Minor whitespace or formatting differences |
| Partial Match | 0.5-0.79 | Same structure, different content |
| Type Mismatch | 0.2-0.49 | Different block types with similar content |
| Missing | 0.0 | Block exists in one document only |

#### Document-Level Scoring

```python
@dataclass
class ComparisonScore:
    """Overall comparison score with breakdown."""
    overall: float  # 0.0 - 1.0
    structure_score: float  # Heading hierarchy match
    content_score: float  # Block content match
    link_score: float  # Internal/external link match

    matched_blocks: int
    partial_blocks: int
    missing_blocks: int
    extra_blocks: int

    critical_issues: List[Issue]  # Must fix
    warnings: List[Issue]  # Should review
    info: List[Issue]  # Informational
```

#### Scoring Thresholds

| Threshold | Interpretation | CI Action |
|-----------|----------------|-----------|
| >= 0.98 | Excellent match | Pass |
| 0.95 - 0.97 | Good match, minor issues | Pass with warnings |
| 0.90 - 0.94 | Acceptable, review recommended | Pass with warnings |
| 0.80 - 0.89 | Significant differences | Fail |
| < 0.80 | Major divergence | Fail |

### Output Formats

#### Human-Readable Report

```
=== Documentation Comparison Report ===
Generated: 2026-01-28T10:30:00Z

Source A: doc/userguide/src/ (RST, 37 files)
Source B: doc/userguide-mkdocs/docs/ (Markdown, 42 files)

Overall Score: 0.96 (PASS)
  Structure: 0.98
  Content:   0.95
  Links:     0.97

=== Summary ===
  Matched Blocks:  1,247 (94%)
  Partial Matches:    52 (4%)
  Missing in B:       18 (1%)
  Extra in B:         12 (1%)

=== Critical Issues (0) ===
  None

=== Warnings (7) ===
  [CONTENT] creating-test-cases.md:142
    Table formatting differs from RST source
    RST: | Column 1 | Column 2 |
    MD:  | Column 1 | Column 2 |

  [LINK] variables.md:89
    Internal reference target changed
    RST: `scalar variables`_
    MD:  [scalar variables](#scalar-variables)

=== Info (23) ===
  [WHITESPACE] 15 blocks have trailing whitespace differences
  [FORMAT] 8 code blocks have different language identifiers
```

#### Machine-Readable JSON

```json
{
  "version": "1.0.0",
  "timestamp": "2026-01-28T10:30:00Z",
  "sources": {
    "a": {"path": "doc/userguide/src/", "format": "rst", "files": 37},
    "b": {"path": "doc/userguide-mkdocs/docs/", "format": "markdown", "files": 42}
  },
  "scores": {
    "overall": 0.96,
    "structure": 0.98,
    "content": 0.95,
    "links": 0.97
  },
  "summary": {
    "matched_blocks": 1247,
    "partial_matches": 52,
    "missing_in_b": 18,
    "extra_in_b": 12
  },
  "issues": [
    {
      "severity": "warning",
      "category": "content",
      "file": "creating-test-cases.md",
      "line": 142,
      "message": "Table formatting differs from RST source",
      "details": {...}
    }
  ],
  "exit_code": 0
}
```

### CLI Interface

```bash
# Basic comparison
python -m doc_compare doc/userguide/src doc/userguide-mkdocs/docs

# Fast mode (source-level only)
python -m doc_compare --fast doc/userguide/src doc/userguide-mkdocs/docs

# Full mode (all layers including rendered HTML)
python -m doc_compare --full doc/userguide/src doc/userguide-mkdocs/docs

# JSON output for CI
python -m doc_compare --format json --output report.json doc/userguide/src doc/userguide-mkdocs/docs

# Specific file comparison
python -m doc_compare --file Variables.rst --file variables.md

# Link audit only
python -m doc_compare --links-only doc/userguide-mkdocs/docs

# With custom threshold
python -m doc_compare --threshold 0.95 doc/userguide/src doc/userguide-mkdocs/docs
```

### Claude-Flow Integration Points

#### Memory Integration

```bash
# Before comparison: Load learned patterns
npx @claude-flow/cli@latest memory search --query "comparison patterns" --namespace doc-compare

# After comparison: Store successful heuristics
npx @claude-flow/cli@latest memory store \
  --namespace doc-compare \
  --key "table-alignment-strategy" \
  --value "Use cell count as primary alignment signal for tables"
```

#### Agent Coordination

```python
# Swarm topology for large documentation comparison
COMPARISON_AGENTS = {
    "coordinator": "Orchestrate comparison phases, synthesize results",
    "rst-parser": "Parse RST files to IR",
    "md-parser": "Parse Markdown files to IR",
    "html-extractor": "Extract content from rendered HTML",
    "block-aligner": "Align blocks between documents",
    "link-auditor": "Validate internal and external links",
    "report-generator": "Generate human and machine-readable reports"
}
```

#### Hooks Integration

```bash
# Pre-task: Get agent routing for comparison task
npx @claude-flow/cli@latest hooks pre-task \
  --description "Compare RST and Markdown documentation"

# Post-task: Record comparison results for learning
npx @claude-flow/cli@latest hooks post-task \
  --task-id "doc-compare-001" \
  --success true \
  --store-results true
```

## Security Considerations

### Input Validation

| Risk | Mitigation |
|------|------------|
| Path traversal in file paths | Validate paths are within project directory |
| Malicious content in source files | Source files are from trusted repository |
| HTML injection in reports | Escape all user-provided content in HTML output |
| Denial of service via large files | Limit file size to 10MB per file |

### Execution Safety

```python
# Path validation
def validate_path(path: str, base_dir: str) -> bool:
    """Ensure path is within allowed directory."""
    resolved = Path(path).resolve()
    base = Path(base_dir).resolve()
    return resolved.is_relative_to(base)

# Content size limits
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_TOTAL_SIZE = 100 * 1024 * 1024  # 100 MB
```

### No Code Execution

The comparison tool:
- Does NOT execute any code from source files
- Does NOT evaluate embedded expressions
- Does NOT run JavaScript from HTML files
- Uses passive parsing only

## Performance Requirements

### Speed Targets

| Mode | Target | Measured |
|------|--------|----------|
| Fast (source-only) | < 3 seconds | TBD |
| Full (with HTML) | < 45 seconds | TBD |
| Link audit only | < 5 seconds | TBD |
| Single file | < 500ms | TBD |

### Memory Targets

| Metric | Target |
|--------|--------|
| Peak memory (fast mode) | < 100 MB |
| Peak memory (full mode) | < 500 MB |
| Per-file memory | < 5 MB |

### Scalability

| Scale | Requirement |
|-------|-------------|
| 50 source files | < 5 seconds (fast) |
| 100 source files | < 10 seconds (fast) |
| 500 source files | < 30 seconds (fast) |

## Compliance

### Project Standards

- **Python Version**: 3.10+ (matches project requirement)
- **Dependencies**: Standard library only (no pip packages)
- **Code Style**: PEP 8, type hints required
- **Testing**: pytest with 90% coverage target
- **Documentation**: Docstrings for all public APIs

### Output Standards

- **JSON Schema**: JSON Schema Draft 2020-12 for report validation
- **Exit Codes**:
  - 0: Pass (score >= threshold)
  - 1: Fail (score < threshold)
  - 2: Error (invalid input, crash)

## Consequences

### Positive

1. **Migration validation**: Automated verification that no content was lost during RST to Markdown conversion

2. **Regression prevention**: CI integration catches accidental content changes before merge

3. **Contributor confidence**: Fast feedback loop enables confident documentation edits

4. **Parallel maintenance support**: Supports the 6-12 month parallel operation period defined in ADR-001

5. **Reusable architecture**: IR-based design enables future format comparisons

6. **Claude-flow synergy**: Memory and agent patterns accelerate comparison development

### Negative

1. **Implementation effort**: Estimated 2-3 weeks of development time

2. **Parsing complexity**: RST and Markdown parsers must handle edge cases correctly

3. **Maintenance burden**: Two parsers to maintain as formats evolve

4. **False positive risk**: Complex constructs may trigger spurious warnings

### Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Parser edge cases | High | Medium | Extensive test suite with real-world examples |
| Performance regression | Low | Low | Benchmark suite with CI gates |
| False positive fatigue | Medium | High | Configurable ignore rules, severity levels |
| Format evolution | Low | Medium | Modular parser design, version detection |

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1)

- [ ] Define IR dataclasses with type hints
- [ ] Implement MarkdownExtractor (simpler format first)
- [ ] Implement basic BlockAligner with heading anchors
- [ ] Create CLI skeleton with argument parsing
- [ ] Unit tests for extractors

### Phase 2: RST Support (Week 2)

- [ ] Implement RstExtractor
- [ ] Handle custom roles (`:setting:`, `:option:`, etc.)
- [ ] Handle reST directives (code-block, note, warning)
- [ ] Implement file mapping (RST sections to MD files)
- [ ] Integration tests with real User Guide files

### Phase 3: Comparison Engine (Week 3)

- [ ] Implement scoring algorithms
- [ ] Implement difference detection
- [ ] Create human-readable report generator
- [ ] Create JSON report generator
- [ ] Performance optimization

### Phase 4: Integration (Week 4)

- [ ] HTML comparison layer (optional full mode)
- [ ] Link audit layer
- [ ] CI/CD integration (GitHub Actions)
- [ ] Claude-flow hooks integration
- [ ] Documentation and examples

## Appendix A: File Mapping Strategy

The comparison tool must handle the structural difference between single-file RST and multi-file Markdown:

### Section Mapping

| RST Section | Markdown File(s) |
|-------------|------------------|
| `GettingStarted/` | `docs/getting-started/*.md` |
| `CreatingTestData/` | `docs/creating-test-data/*.md` |
| `ExecutingTestCases/` | `docs/executing-tests/*.md` |
| `ExtendingRobotFramework/` | `docs/extending/*.md` |
| `SupportingTools/` | `docs/supporting-tools/*.md` |
| `Appendices/` | `docs/appendices/*.md` |

### Heading Anchor Normalization

```python
def normalize_anchor(text: str) -> str:
    """Normalize heading text to anchor ID."""
    # Remove special characters, lowercase, hyphenate
    anchor = re.sub(r'[^\w\s-]', '', text.lower())
    anchor = re.sub(r'[\s_]+', '-', anchor)
    return anchor.strip('-')

# Examples:
# "Creating Test Cases" -> "creating-test-cases"
# "2.1.3 Variables" -> "213-variables"
# "IF/ELSE" -> "ifelse"
```

## Appendix B: Ignore Rules Configuration

```yaml
# .doc-compare.yml
version: 1

# Global ignore patterns
ignore:
  - pattern: "trailing_whitespace"
    reason: "Whitespace normalization differs between formats"

  - pattern: "heading_anchor_format"
    reason: "MkDocs auto-generates different anchor IDs"

# Per-file overrides
files:
  "variables.md":
    ignore:
      - pattern: "table_alignment"
        reason: "Known table reformatting in this file"

# Severity adjustments
severity:
  missing_code_block: warning  # Default: error
  link_target_changed: info    # Default: warning
```

## Appendix C: Decision Record Metadata

| Field | Value |
|-------|-------|
| ADR Number | ADR-002 |
| Title | Documentation Comparison Tool Architecture |
| Status | Proposed |
| Context | Documentation migration validation |
| Decision Date | 2026-01-28 |
| Supersedes | None |
| Related | ADR-001 (User Guide Migration) |
| Decision Makers | Robot Framework Core Team |
| Consulted | Documentation contributors |
| Informed | All contributors |

---

*This ADR follows the format recommended by Michael Nygard and incorporates Domain-Driven Design principles for comparison tool architecture.*
