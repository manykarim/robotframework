# DocDiff Architecture

## Overview

DocDiff is designed following Domain-Driven Design (DDD) principles with a hexagonal (ports and adapters) architecture. The tool is implemented as a pure Python stdlib application with zero runtime dependencies.

## Design Principles

### 1. Pure Python stdlib

All functionality uses only Python 3.10+ standard library:
- `html.parser` for HTML parsing
- `re` for Markdown parsing
- `difflib` for text comparison
- `dataclasses` for data models
- `argparse` for CLI
- `json` for serialization

### 2. DDD Bounded Contexts

Each module represents a bounded context with clear responsibilities:
- **Extractors**: Document parsing domain
- **Normalizers**: Text processing domain
- **Aligners**: Section matching domain
- **Comparators**: Content comparison domain
- **Validators**: Link/image validation domain
- **Reporters**: Report generation domain

### 3. Hexagonal Architecture

```
                    ┌─────────────────────────────────┐
                    │            CLI Port             │
                    │         (docdiff.cli)           │
                    └─────────────────────────────────┘
                                    │
                                    ▼
    ┌───────────────────────────────────────────────────────────────┐
    │                         Core Domain                           │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐│
    │  │  Extractors │──│  Aligners   │──│      Comparators        ││
    │  └─────────────┘  └─────────────┘  └─────────────────────────┘│
    │         │                │                     │              │
    │         ▼                ▼                     ▼              │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐│
    │  │ Normalizers │  │ Validators  │  │       Reporters         ││
    │  └─────────────┘  └─────────────┘  └─────────────────────────┘│
    └───────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
    ┌───────────────────────────┐   ┌───────────────────────────┐
    │      File System          │   │      Standard Output      │
    │   (HTML/Markdown files)   │   │    (Reports/JSON)         │
    └───────────────────────────┘   └───────────────────────────┘
```

### 4. Dependency Inversion

- Core domain depends on abstract models only
- Concrete implementations in leaf modules
- No circular dependencies between modules

## Module Structure

```
docdiff/
├── __init__.py              # Package metadata and version
├── __main__.py              # Entry point: python -m docdiff
├── cli.py                   # Command-line interface
├── models.py                # Core data classes
├── extractors/
│   ├── __init__.py          # Public API and convenience functions
│   ├── html_extractor.py    # HTML parsing (HTMLParser)
│   └── md_extractor.py      # Markdown parsing (regex-based)
├── normalizers/
│   ├── __init__.py          # Public API
│   └── text_normalizer.py   # Text normalization utilities
├── aligners/
│   ├── __init__.py          # Section alignment algorithms
│   └── section_aligner.py   # Multi-stage matching
├── comparators/
│   ├── __init__.py          # Block comparison
│   └── content_comparator.py # Type-specific comparators
├── validators/
│   ├── __init__.py          # Public API and utility classes
│   ├── link_validator.py    # Link validation
│   └── image_validator.py   # Image validation
└── reporters/
    ├── __init__.py          # Public API
    └── markdown_reporter.py # Report generation
```

## Data Flow

The comparison process follows a pipeline architecture:

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. EXTRACTION                                                       │
│                                                                     │
│    HTML File ──► HTMLContentExtractor ──► List[Section]             │
│    MD Directory ──► MarkdownExtractor ──► Dict[Path, List[Section]] │
│                           │                                         │
│                           ▼                                         │
│              Flatten to List[Section] for each source               │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 2. ALIGNMENT                                                        │
│                                                                     │
│    Old Sections ──┐                                                 │
│                   ├──► align_sections() ──► AlignmentResult         │
│    New Sections ──┘                                                 │
│                                                                     │
│    AlignmentResult contains:                                        │
│    - matched: List[Tuple[Section, Section]]                         │
│    - source_only: List[Section] (missing)                           │
│    - target_only: List[Section] (extra)                             │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 3. COMPARISON                                                       │
│                                                                     │
│    For each matched pair:                                           │
│    (Old Section, New Section) ──► BlockComparator ──► List[Finding] │
│                                                                     │
│    For source_only (missing):                                       │
│    Section ──► Finding(category=CONTENT_MISSING, priority=P0)       │
│                                                                     │
│    For target_only (extra):                                         │
│    Section ──► Finding(category=CONTENT_ADDED, priority=P2)         │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 4. VALIDATION                                                       │
│                                                                     │
│    Links:                                                           │
│    - Extract all links from sections                                │
│    - Build anchor map from new sections                             │
│    - Check anchor drift between old and new                         │
│    - Validate internal links exist                                  │
│                                                                     │
│    Images:                                                          │
│    - Extract all images from sections                               │
│    - Compare image sets                                             │
│    - Validate image files exist                                     │
│    - Check alt text compliance                                      │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 5. REPORTING                                                        │
│                                                                     │
│    ComparisonResult ──► generate_markdown_report() ──► Markdown     │
│                    └──► generate_json_report() ──► JSON             │
└─────────────────────────────────────────────────────────────────────┘
```

## Key Components

### Models (`models.py`)

The core data model is the heart of the system:

```
ComparisonResult
├── source_file: str
├── target_file: str
├── findings: List[Finding]
├── alignment: AlignmentResult
│   ├── matched: List[Tuple[Section, Section]]
│   ├── source_only: List[Section]
│   └── target_only: List[Section]
├── matches: List[SectionMatch]
├── missing_sections: List[Section]
└── extra_sections: List[Section]

Section
├── title: str
├── key: str (normalized)
├── level: int (1-6)
├── number: str (e.g., "2.1.3")
├── blocks: List[Block]
└── subsections: List[Section]

Block
├── block_type: BlockType
├── content: str
└── metadata: Dict[str, Any]

Finding
├── category: str
├── severity: Severity
├── priority: Priority
├── message: str
├── source_location: str
└── suggestion: str
```

### Extractors

#### HTML Extractor

Uses `html.parser.HTMLParser` to parse HTML:
- Detects headings (h1-h6) for section structure
- Extracts paragraphs, code blocks, tables, lists
- Handles MkDocs minified HTML output
- Detects admonition patterns (note, warning, tip)

#### Markdown Extractor

Uses regex-based parsing:
- ATX headings (`# `, `## `, etc.)
- Fenced code blocks with language tags
- Pipe tables with escaped pipes
- Material for MkDocs admonitions (`!!!`, `???`)
- Nested lists with varying indentation

### Aligners

Multi-stage matching algorithm:

1. **Exact number match**: "2.1.3" == "2.1.3"
2. **Exact key match**: normalized title comparison
3. **Fuzzy match**: SequenceMatcher with threshold >= 0.8
4. **Parent context match**: fallback for nested sections

Configuration:
```python
AlignmentConfig(
    fuzzy_threshold=0.8,
    number_weight=0.3,
    key_weight=0.4,
    title_weight=0.3,
    allow_reordering=True
)
```

### Comparators

Block-type-specific comparison with weighted scoring:
| Block Type | Weight | Comparison Method |
|------------|--------|-------------------|
| Paragraph | 35% | Normalized text similarity |
| Code | 20% | Exact or fuzzy with unified diff |
| Table | 15% | Cell-by-cell comparison |
| List | 15% | Set comparison (missing/extra items) |
| Admonition | 10% | Type and content comparison |
| Link/Image | 5% | URL/path comparison |

### Validators

#### Link Validation

```
Link Types:
├── Internal anchor (#section-name)
├── Relative file (../page.md)
├── External (https://...)
└── Email (mailto:...)

Checks:
├── Anchor exists in document
├── File exists on filesystem
├── Anchor drift (old vs new)
└── Cross-reference validity
```

#### Image Validation

```
Checks:
├── Image file exists
├── Alt text present (accessibility)
├── Image set comparison (missing/extra)
└── Path resolution
```

### Reporters

Two output formats:

1. **Markdown Report**
   - Executive summary
   - Prioritized findings (P0, P1, P2)
   - Section-by-section analysis
   - Missing/extra sections
   - Detailed diffs

2. **JSON Report**
   - Machine-readable format
   - Same data structure as internal models
   - Suitable for CI/CD integration

## Key Decisions

### ADR-001: Pure Python stdlib

**Context**: The tool should be easy to install and use.

**Decision**: Use only Python standard library.

**Consequences**:
- No external dependencies to manage
- Simple installation (no `pip install`)
- Limited to stdlib capabilities for parsing

### ADR-002: Three-Layer Comparison

**Context**: RST and Markdown have different features.

**Decision**: Use three comparison layers:
1. Source-level IR (Section/Block model)
2. Rendered HTML spot-checks
3. Link/image audit

**Consequences**:
- Robust comparison across formats
- Can detect both structural and rendering issues
- More complex implementation

### ADR-003: Weighted Similarity Scoring

**Context**: Not all content types are equally important.

**Decision**: Use weighted scoring per block type.

**Consequences**:
- Code blocks get appropriate attention
- Cosmetic changes don't dominate findings
- Configurable thresholds

### ADR-004: Priority-Based Findings

**Context**: CI/CD needs clear pass/fail criteria.

**Decision**: Three priority levels with exit codes.

**Consequences**:
- P0/P1 = exit code 2 (failure)
- P2 = exit code 1 (warning)
- No findings = exit code 0 (success)
- Strict mode for zero-tolerance

### ADR-005: Lazy Module Loading

**Context**: CLI `--help` should be fast.

**Decision**: Lazy import of heavy modules in CLI.

**Consequences**:
- Fast startup for help/version
- Slightly more complex import structure
- No impact on comparison performance

## Performance Considerations

### Current Performance
| Operation | Time | Throughput |
|-----------|------|------------|
| Markdown extraction (42 files) | ~1.8s | 23.6 files/sec |
| Tests (246 tests) | 0.4s | 615 tests/sec |

### Optimization Opportunities

1. **Parallel extraction**: Process multiple files concurrently
2. **Caching**: Cache normalized text for repeated comparisons
3. **Streaming**: Process large files in chunks
4. **Compiled regex**: Pre-compile all regex patterns

## Testing Strategy

```
tests/
├── test_models.py          # Model unit tests
├── test_extractors.py      # Extraction tests
├── test_normalizers.py     # Normalization tests
├── test_aligners.py        # Alignment tests
├── test_comparators.py     # Comparison tests
├── test_validators.py      # Validation tests
└── test_reporters.py       # Reporter tests
```

Test coverage targets:
- Core modules: 80%+
- Edge cases: All identified
- Integration: End-to-end comparison

## Extension Points

### Adding New Block Types

1. Add to `BlockType` enum in `models.py`
2. Add extraction logic in extractors
3. Add comparison method in `BlockComparator`
4. Update reporter formatting

### Adding New Validators

1. Create validator class in `validators/`
2. Add extraction function for resource type
3. Add validation logic
4. Export from `validators/__init__.py`

### Adding New Report Formats

1. Add generation function in `reporters/`
2. Add format option to CLI
3. Export from `reporters/__init__.py`

## Future Roadmap

1. **Integration tests**: Real Robot Framework documentation
2. **Performance**: Parallel processing for large documentation sets
3. **Caching**: Incremental comparison for unchanged files
4. **Extensions**: Support for more Markdown extensions
5. **Interactive viewer**: HTML diff visualization
