# Documentation Comparison Tool - Domain-Driven Design Architecture

**Version:** 1.0
**Date:** 2026-01-28
**Author:** System Architect
**Status:** Design Document

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Strategic Design](#strategic-design)
3. [Bounded Contexts](#bounded-contexts)
4. [Context Map](#context-map)
5. [Tactical Design](#tactical-design)
6. [Domain Events](#domain-events)
7. [Anti-Corruption Layers](#anti-corruption-layers)
8. [Hexagonal Architecture](#hexagonal-architecture)
9. [Quality Attributes](#quality-attributes)
10. [Appendices](#appendices)

---

## 1. Executive Summary

### 1.1 Purpose

This document defines the Domain-Driven Design (DDD) architecture for a Documentation Comparison Tool. The tool compares legacy single-page HTML documentation (Robot Framework User Guide) against migrated multi-page MkDocs Markdown documentation to audit migration completeness and accuracy.

### 1.2 Core Problem Domain

The documentation migration from reStructuredText/HTML to Markdown/MkDocs introduces several comparison challenges:

- **Structural divergence**: Single-page with anchors vs. multi-page with URLs
- **Format heterogeneity**: HTML entities vs. Markdown syntax
- **Semantic preservation**: Ensuring meaning survives format translation
- **Link integrity**: Validating that internal/external references remain functional

### 1.3 Strategic Goals
| Goal | Description |
|------|-------------|
| **Accuracy** | Detect content drift with high precision (target: 95%+ recall) |
| **Actionability** | Generate prioritized findings with clear remediation paths |
| **Extensibility** | Support additional documentation formats in future |
| **Zero Dependencies** | Pure Python stdlib implementation |

---

## 2. Strategic Design

### 2.1 Domain Vision Statement

> The Documentation Comparison Tool enables documentation maintainers to confidently validate migration completeness by providing semantic-aware comparison between heterogeneous document formats, surfacing discrepancies as prioritized, actionable findings.

### 2.2 Subdomains Classification
| Subdomain | Type | Rationale |
|-----------|------|-----------|
| **Document Extraction** | Core | Fundamental differentiator - handles format-specific parsing |
| **Content Normalization** | Core | Critical for accurate comparison across formats |
| **Section Alignment** | Core | Key algorithmic intelligence for mapping structures |
| **Comparison Engine** | Core | Primary value delivery - similarity scoring and diff generation |
| **Reporting** | Supporting | Important but follows standard patterns |
| **Link Validation** | Supporting | Specialized but uses well-known HTTP/anchor validation |

### 2.3 Ubiquitous Language
| Term | Definition |
|------|------------|
| **Section** | A hierarchical division of content identified by a heading |
| **Block** | An atomic content unit (paragraph, table, code, list, admonition, image) |
| **Anchor** | A navigational target within a document (HTML id or Markdown heading slug) |
| **Fragment** | The portion of a URL after the `#` symbol that references an anchor |
| **Finding** | A detected discrepancy with assigned priority and evidence |
| **Similarity Score** | A 0.0-1.0 metric indicating semantic equivalence |
| **Alignment** | The mapping between an old section and its new counterpart |
| **Document IR** | Intermediate Representation - format-agnostic document model |
| **Admonition** | A callout block (note, warning, tip, caution) |
| **Heading Slug** | URL-safe identifier generated from heading text |

---

## 3. Bounded Contexts

### 3.1 Document Extraction Context

**Responsibility**: Parse source documents into a normalized intermediate representation.

**Boundaries**:
- Owns all format-specific parsing logic
- Produces format-agnostic Document IR
- Does NOT normalize content semantically (that is Normalization Context's job)

```
+------------------------------------------+
|     DOCUMENT EXTRACTION CONTEXT          |
|------------------------------------------|
|  Aggregates:                             |
|    - DocumentSource (Root)               |
|    - SectionTree                         |
|                                          |
|  Entities:                               |
|    - RawSection                          |
|    - RawBlock                            |
|                                          |
|  Value Objects:                          |
|    - SourcePath                          |
|    - HeadingLevel                        |
|    - BlockType                           |
|    - RawContent                          |
|                                          |
|  Domain Services:                        |
|    - HtmlExtractor                       |
|    - MarkdownExtractor                   |
|    - RstExtractor (future)               |
+------------------------------------------+
```

#### Aggregate: DocumentSource (Root)

```
DocumentSource
├── source_path: SourcePath
├── format: DocumentFormat (html | markdown | rst)
├── metadata: DocumentMetadata
└── section_tree: SectionTree
    └── sections: List[RawSection]
        ├── heading: HeadingInfo
        ├── anchor: AnchorId
        ├── level: HeadingLevel
        ├── children: List[RawSection]
        └── blocks: List[RawBlock]
            ├── block_type: BlockType
            ├── raw_content: RawContent
            └── attributes: Dict[str, Any]
```

#### Invariants

1. Every `RawSection` must have a valid `HeadingLevel` (1-6)
2. `SectionTree` maintains parent-child consistency
3. Block types are exhaustive: paragraph, list, table, code, admonition, image, link

---

### 3.2 Content Normalization Context

**Responsibility**: Transform raw content into comparable normalized form.

**Boundaries**:
- Receives raw blocks from Extraction Context
- Produces normalized, format-agnostic content
- Owns all text normalization rules (whitespace, entities, case, punctuation)

```
+------------------------------------------+
|     CONTENT NORMALIZATION CONTEXT        |
|------------------------------------------|
|  Aggregates:                             |
|    - NormalizedDocument (Root)           |
|                                          |
|  Entities:                               |
|    - NormalizedSection                   |
|    - NormalizedBlock                     |
|                                          |
|  Value Objects:                          |
|    - NormalizedText                      |
|    - NormalizedTable                     |
|    - NormalizedList                      |
|    - NormalizedCode                      |
|    - CanonicalAnchor                     |
|                                          |
|  Domain Services:                        |
|    - TextNormalizer                      |
|    - TableNormalizer                     |
|    - ListNormalizer                      |
|    - CodeBlockNormalizer                 |
|    - EntityDecoder                       |
|    - WhitespaceCollapser                 |
+------------------------------------------+
```

#### Aggregate: NormalizedDocument (Root)

```
NormalizedDocument
├── source_ref: DocumentSourceId
├── sections: List[NormalizedSection]
│   ├── section_key: SectionKey
│   ├── canonical_title: NormalizedText
│   ├── canonical_anchor: CanonicalAnchor
│   ├── path: DocumentPath
│   └── blocks: List[NormalizedBlock]
│       ├── kind: BlockKind
│       ├── content: NormalizedContent (union type)
│       └── fingerprint: ContentFingerprint
└── index: SectionIndex (for fast lookup)
```

#### Value Object: NormalizedText

```
NormalizedText
├── value: str  # Collapsed whitespace, decoded entities
├── original: str  # Preserved for debugging
└── transformations_applied: List[TransformationType]
```

#### Invariants

1. All text undergoes consistent normalization pipeline
2. Original content is preserved for audit trail
3. Normalization is idempotent: `normalize(normalize(x)) == normalize(x)`

---

### 3.3 Section Alignment Context

**Responsibility**: Match sections between old and new documents.

**Boundaries**:
- Receives normalized documents from both sources
- Produces alignment mappings with confidence scores
- Owns matching algorithms and heuristics

```
+------------------------------------------+
|     SECTION ALIGNMENT CONTEXT            |
|------------------------------------------|
|  Aggregates:                             |
|    - AlignmentResult (Root)              |
|                                          |
|  Entities:                               |
|    - SectionAlignment                    |
|    - UnmatchedSection                    |
|                                          |
|  Value Objects:                          |
|    - AlignmentScore                      |
|    - MatchType                           |
|    - MatchEvidence                       |
|    - SectionKey                          |
|                                          |
|  Domain Services:                        |
|    - ExactMatcher                        |
|    - FuzzyMatcher                        |
|    - ContextualMatcher                   |
|    - AlignmentStrategy                   |
+------------------------------------------+
```

#### Aggregate: AlignmentResult (Root)

```
AlignmentResult
├── old_document_ref: NormalizedDocumentId
├── new_document_ref: NormalizedDocumentId
├── alignments: List[SectionAlignment]
│   ├── old_section: SectionRef
│   ├── new_section: SectionRef
│   ├── score: AlignmentScore
│   ├── match_type: MatchType
│   └── evidence: MatchEvidence
├── unmatched_old: List[UnmatchedSection]
├── unmatched_new: List[UnmatchedSection]
└── statistics: AlignmentStatistics
```

#### Value Object: MatchType

```
MatchType (enumeration)
├── EXACT_NUMBER      # Matched by section number (e.g., "2.1")
├── EXACT_TITLE       # Matched by identical normalized title
├── FUZZY_TITLE       # Matched by similar title (threshold > 0.88)
├── CONTEXTUAL        # Matched by parent + child context
└── UNMATCHED         # No suitable match found
```

#### Domain Service: AlignmentStrategy

Multi-pass alignment algorithm:
1. **Pass 1**: Match by explicit section numbering
2. **Pass 2**: Match by exact normalized title
3. **Pass 3**: Match by fuzzy title similarity
4. **Pass 4**: Match by contextual parent-child relationships

---

### 3.4 Comparison Context

**Responsibility**: Compare aligned sections and compute similarity metrics.

**Boundaries**:
- Receives aligned section pairs from Alignment Context
- Produces detailed comparison results with diff information
- Owns similarity algorithms and threshold logic

```
+------------------------------------------+
|         COMPARISON CONTEXT               |
|------------------------------------------|
|  Aggregates:                             |
|    - ComparisonResult (Root)             |
|                                          |
|  Entities:                               |
|    - SectionComparison                   |
|    - BlockComparison                     |
|                                          |
|  Value Objects:                          |
|    - SimilarityScore                     |
|    - DiffHunk                            |
|    - ComparisonVerdict                   |
|    - WeightedScore                       |
|                                          |
|  Domain Services:                        |
|    - TextComparator                      |
|    - TableComparator                     |
|    - ListComparator                      |
|    - CodeComparator                      |
|    - SimilarityCalculator                |
+------------------------------------------+
```

#### Aggregate: ComparisonResult (Root)

```
ComparisonResult
├── alignment_ref: AlignmentResultId
├── section_comparisons: List[SectionComparison]
│   ├── alignment: SectionAlignment
│   ├── overall_score: SimilarityScore
│   ├── block_comparisons: List[BlockComparison]
│   │   ├── old_block: NormalizedBlock
│   │   ├── new_block: NormalizedBlock (optional)
│   │   ├── score: SimilarityScore
│   │   ├── diff: List[DiffHunk]
│   │   └── verdict: ComparisonVerdict
│   ├── missing_blocks: List[NormalizedBlock]
│   ├── extra_blocks: List[NormalizedBlock]
│   └── weighted_scores: WeightedScoreBreakdown
├── global_statistics: ComparisonStatistics
└── thresholds_applied: ThresholdConfiguration
```

#### Value Object: WeightedScoreBreakdown

Scoring weights per block type:

```
WeightedScoreBreakdown
├── paragraphs: WeightedScore (weight: 0.35)
├── lists: WeightedScore (weight: 0.15)
├── code_blocks: WeightedScore (weight: 0.20)
├── tables: WeightedScore (weight: 0.15)
├── admonitions: WeightedScore (weight: 0.10)
└── images_links: WeightedScore (weight: 0.05)
```

#### Invariants

1. Similarity scores are always in range [0.0, 1.0]
2. Block comparisons maintain referential integrity to source blocks
3. Missing/extra blocks are mutually exclusive with matched blocks

---

### 3.5 Reporting Context

**Responsibility**: Generate human-readable audit reports from comparison results.

**Boundaries**:
- Receives comparison results from Comparison Context
- Produces formatted reports (Markdown, JSON)
- Owns presentation logic and priority classification

```
+------------------------------------------+
|         REPORTING CONTEXT                |
|------------------------------------------|
|  Aggregates:                             |
|    - AuditReport (Root)                  |
|                                          |
|  Entities:                               |
|    - Finding                             |
|    - ReportSection                       |
|                                          |
|  Value Objects:                          |
|    - Priority                            |
|    - FindingCategory                     |
|    - Evidence                            |
|    - Recommendation                      |
|                                          |
|  Domain Services:                        |
|    - FindingClassifier                   |
|    - MarkdownRenderer                    |
|    - JsonRenderer                        |
|    - ReportAggregator                    |
+------------------------------------------+
```

#### Aggregate: AuditReport (Root)

```
AuditReport
├── metadata: ReportMetadata
│   ├── generated_at: Timestamp
│   ├── tool_version: Version
│   ├── old_source: SourceInfo
│   └── new_source: SourceInfo
├── summary: ExecutiveSummary
│   ├── total_sections_old: int
│   ├── matched_sections: int
│   ├── missing_sections: int
│   ├── overall_similarity: SimilarityScore
│   └── findings_by_priority: Dict[Priority, int]
├── findings: List[Finding]
│   ├── id: FindingId
│   ├── priority: Priority
│   ├── category: FindingCategory
│   ├── section_ref: SectionRef
│   ├── message: str
│   ├── evidence: Evidence
│   └── recommendation: Recommendation
└── section_details: List[ReportSection]
```

#### Value Object: Priority

```
Priority (enumeration)
├── P0 (Critical)  # Version mismatch, tool failures, major missing sections
├── P1 (High)      # Broken links/anchors, missing images, missing tables/code
├── P2 (Medium)    # Text drift, reordered items, formatting differences
└── P3 (Low)       # Minor cosmetic differences, style variations
```

#### Value Object: FindingCategory

```
FindingCategory (enumeration)
├── MISSING_SECTION
├── BROKEN_LINK
├── BROKEN_ANCHOR
├── MISSING_IMAGE
├── TABLE_DRIFT
├── CODE_DRIFT
├── TEXT_DRIFT
├── LIST_DRIFT
├── ADMONITION_DRIFT
└── STRUCTURAL_CHANGE
```

---

### 3.6 Link Validation Context

**Responsibility**: Validate internal and external link integrity.

**Boundaries**:
- Receives documents from Extraction Context
- Validates link targets exist and are reachable
- Produces link validation results

```
+------------------------------------------+
|      LINK VALIDATION CONTEXT             |
|------------------------------------------|
|  Aggregates:                             |
|    - LinkValidationResult (Root)         |
|                                          |
|  Entities:                               |
|    - LinkCheck                           |
|    - AnchorRegistry                      |
|                                          |
|  Value Objects:                          |
|    - LinkTarget                          |
|    - ValidationStatus                    |
|    - LinkType                            |
|    - AnchorId                            |
|                                          |
|  Domain Services:                        |
|    - InternalLinkValidator               |
|    - ExternalLinkValidator               |
|    - AnchorResolver                      |
|    - UrlCanonicalizer                    |
+------------------------------------------+
```

#### Aggregate: LinkValidationResult (Root)

```
LinkValidationResult
├── document_ref: DocumentSourceId
├── total_links: int
├── link_checks: List[LinkCheck]
│   ├── source_location: SourceLocation
│   ├── link_target: LinkTarget
│   ├── link_type: LinkType
│   ├── status: ValidationStatus
│   └── error_detail: str (optional)
├── anchor_registry: AnchorRegistry
│   └── anchors: Dict[AnchorId, SourceLocation]
├── broken_links: List[LinkCheck]
└── statistics: LinkStatistics
```

#### Value Object: LinkType

```
LinkType (enumeration)
├── INTERNAL_PAGE      # Link to another page in same doc set
├── INTERNAL_ANCHOR    # Link to anchor in same page
├── CROSS_PAGE_ANCHOR  # Link to anchor in different page
├── EXTERNAL           # Link to external URL
└── IMAGE              # Image source reference
```

#### Value Object: ValidationStatus

```
ValidationStatus (enumeration)
├── VALID              # Target exists and is reachable
├── BROKEN             # Target does not exist
├── REDIRECT           # Target redirects (may need update)
├── TIMEOUT            # External URL timed out
└── UNCHECKED          # Not validated (e.g., external in offline mode)
```

---

## 4. Context Map

### 4.1 Context Relationships

```
+-------------------+
| Document          |
|---|
| Extraction        |
| Context           |
+---------+---------+
|
| Published Language (Document IR)
          v
+---------+---------+     +-------------------+
| Content           |     | Link              |
|---|---|---|
| Normalization     |     | Validation        |
| Context           |     | Context           |
+---------+---------+     +---------+---------+
|                         |
|---|
| Conformist              | Shared Kernel
          v                         | (AnchorRegistry)
+---------+---------+               |
| Section           |<--------------+
| Alignment         |
|---|
| Context           |
+---------+---------+
|
| Customer/Supplier
          v
+---------+---------+
| Comparison        |
|---|
| Context           |
+---------+---------+
|
| Customer/Supplier
          v
+---------+---------+
| Reporting         |
|---|
| Context           |
+---------+---------+
```

### 4.2 Integration Patterns
| Upstream | Downstream | Pattern | Description |
|----------|------------|---------|-------------|
| Extraction | Normalization | **Published Language** | Document IR is the shared schema |
| Extraction | Link Validation | **Published Language** | Raw links extracted for validation |
| Normalization | Alignment | **Conformist** | Alignment conforms to normalization output |
| Link Validation | Alignment | **Shared Kernel** | Anchor registry shared for anchor validation |
| Alignment | Comparison | **Customer/Supplier** | Comparison requests aligned pairs |
| Comparison | Reporting | **Customer/Supplier** | Reporting consumes comparison results |

### 4.3 Context Interaction Diagram

```
                                    EXTRACTION CONTEXT
                                   /                   \
                                  /                     \
                           [Document IR]           [Raw Links]
                                /                         \
                               v                           v
                    NORMALIZATION               LINK VALIDATION
                    CONTEXT                     CONTEXT
                           \                         /
                     [Normalized Docs]    [Anchor Registry]
                             \                     /
                              v                   v
                           ALIGNMENT CONTEXT
|
                            [Aligned Pairs]
|
                                   v
                           COMPARISON CONTEXT
|
                          [Comparison Results]
|
                                   v
                           REPORTING CONTEXT
|
                              [Audit Report]
```

---

## 5. Tactical Design

### 5.1 Aggregate Design Principles

1. **Small Aggregates**: Each aggregate protects a single consistency boundary
2. **Reference by Identity**: Aggregates reference each other by ID, not direct object reference
3. **Eventual Consistency**: Cross-aggregate consistency via domain events

### 5.2 Repository Pattern

Each bounded context exposes repositories for aggregate persistence:

```
<<interface>>
Repository[T]
├── get(id: Id) -> T | None
├── save(aggregate: T) -> None
├── delete(id: Id) -> None
└── list(filter: Filter) -> List[T]
```

Concrete implementations:
| Context | Repository | Storage |
|---------|------------|---------|
| Extraction | `DocumentSourceRepository` | In-memory |
| Normalization | `NormalizedDocumentRepository` | In-memory |
| Alignment | `AlignmentResultRepository` | In-memory |
| Comparison | `ComparisonResultRepository` | In-memory |
| Reporting | `AuditReportRepository` | File system |
| Link Validation | `LinkValidationResultRepository` | In-memory |

### 5.3 Domain Services

Domain services encapsulate logic that does not naturally fit within an entity or value object:
| Context | Service | Responsibility |
|---------|---------|----------------|
| Extraction | `HtmlExtractor` | Parse HTML into Document IR |
| Extraction | `MarkdownExtractor` | Parse Markdown into Document IR |
| Normalization | `TextNormalizer` | Apply normalization pipeline |
| Alignment | `AlignmentStrategy` | Execute multi-pass alignment |
| Comparison | `SimilarityCalculator` | Compute weighted similarity scores |
| Reporting | `FindingClassifier` | Classify findings by priority |
| Link Validation | `AnchorResolver` | Resolve anchor references |

---

## 6. Domain Events

### 6.1 Event Catalog
| Event | Publisher | Consumers | Payload |
|-------|-----------|-----------|---------|
| `DocumentExtracted` | Extraction | Normalization, Link Validation | `{document_id, format, section_count}` |
| `DocumentNormalized` | Normalization | Alignment | `{document_id, section_count}` |
| `LinksValidated` | Link Validation | Alignment, Reporting | `{document_id, broken_count, anchor_registry_id}` |
| `SectionsAligned` | Alignment | Comparison | `{alignment_id, matched_count, unmatched_count}` |
| `ComparisonCompleted` | Comparison | Reporting | `{comparison_id, overall_score, finding_count}` |
| `ReportGenerated` | Reporting | (external) | `{report_id, output_path, summary}` |

### 6.2 Event Flow

```
[DocumentExtracted]
|
       +---> Normalization Context
|            |
|---|
|     [DocumentNormalized]
|            |
|---|
       +---> Link Validation Context
|            |
|---|
|     [LinksValidated]
|            |
|---|
       +------------+
|
                    v
            Alignment Context
|
             [SectionsAligned]
|
                    v
            Comparison Context
|
           [ComparisonCompleted]
|
                    v
            Reporting Context
|
             [ReportGenerated]
```

### 6.3 Event Design

```
DomainEvent
├── event_id: UUID
├── event_type: str
├── timestamp: datetime
├── aggregate_id: str
├── aggregate_type: str
└── payload: Dict[str, Any]
```

---

## 7. Anti-Corruption Layers

### 7.1 ACL: External HTML to Document IR

**Purpose**: Protect the core domain from HTML format complexities.

**Location**: Between raw HTML parsing and Document Extraction aggregate.

```
+------------------+     +------------------+     +------------------+
|                  |     |                  |     |                  |
|---|---|---|---|---|
|  Raw HTML        | --> |  HTML ACL        | --> |  Document IR     |
|  (stdlib parser) |     |  (Translator)    |     |  (Domain Model)  |
|                  |     |                  |     |                  |
+------------------+     +------------------+     +------------------+
```

**Responsibilities**:
- Translate HTML DOM events to Document IR structures
- Handle HTML entity decoding
- Normalize heading levels and anchor extraction
- Handle malformed HTML gracefully

### 7.2 ACL: External Markdown to Document IR

**Purpose**: Protect the core domain from Markdown syntax variations.

**Location**: Between raw Markdown text and Document Extraction aggregate.

```
+------------------+     +------------------+     +------------------+
|                  |     |                  |     |                  |
|---|---|---|---|---|
|  Raw Markdown    | --> |  Markdown ACL    | --> |  Document IR     |
|  (text)          |     |  (Translator)    |     |  (Domain Model)  |
|                  |     |                  |     |                  |
+------------------+     +------------------+     +------------------+
```

**Responsibilities**:
- Parse Markdown syntax without external dependencies
- Handle Material for MkDocs extensions (admonitions, tabs)
- Generate heading slugs matching MkDocs behavior
- Handle inline formatting for normalization

### 7.3 ACL: External URL Validation

**Purpose**: Isolate HTTP concerns from Link Validation domain.

**Location**: Between domain service and `urllib.request`.

```
+------------------+     +------------------+     +------------------+
|                  |     |                  |     |                  |
|---|---|---|---|---|
|  LinkValidator   | --> |  HTTP ACL        | --> |  urllib.request  |
|  (Domain)        |     |  (Adapter)       |     |  (stdlib)        |
|                  |     |                  |     |                  |
+------------------+     +------------------+     +------------------+
```

**Responsibilities**:
- Translate domain `LinkTarget` to HTTP requests
- Handle timeouts, redirects, SSL errors
- Map HTTP responses to `ValidationStatus`
- Implement retry and backoff policies

---

## 8. Hexagonal Architecture

### 8.1 Port and Adapter Design

```
                        +----------------------------------+
|                                  |
|---|
    +------------+      |        APPLICATION CORE          |      +------------+
|            |      |                                  |      |            |
|---|---|---|---|---|
| CLI        |----->|  +----------------------------+  |<-----| File       |
| Adapter    |      |  |                            |  |      | System     |
| (Primary)  |      |  |    DOMAIN MODEL            |  |      | Adapter    |
    +------------+      |  |    (Bounded Contexts)      |  |      | (Secondary)|
|  |                            |  |      +------------+
    +------------+      |  +----------------------------+  |
|            |      |                                  |      +------------+
| API        |----->|  +----------------------------+  |<-----| HTTP       |
|---|---|---|---|---|
| Adapter    |      |  |                            |  |      | Adapter    |
| (Primary)  |      |  |    APPLICATION SERVICES    |  |      | (Secondary)|
    +------------+      |  |    (Use Cases)             |  |      +------------+
|  |                            |  |
|---|---|---|
|  +----------------------------+  |      +------------+
|                                  |      |            |
|---|---|---|
                        +----------------------------------+<-----| Memory     |
| Adapter    |
|---|
| (Secondary)|
                                                                  +------------+
```

### 8.2 Primary Ports (Driving)
| Port | Description |
|------|-------------|
| `CompareDocuments` | Main use case - compare two document sources |
| `ValidateLinks` | Validate links in a document set |
| `GenerateReport` | Generate audit report from comparison |
| `ExtractDocument` | Extract single document for inspection |

### 8.3 Secondary Ports (Driven)
| Port | Description |
|------|-------------|
| `DocumentReader` | Read document content from source |
| `ReportWriter` | Write report to destination |
| `HttpClient` | Make HTTP requests for link validation |
| `EventPublisher` | Publish domain events |

### 8.4 Application Services

Application services orchestrate use cases by coordinating domain objects:

```
CompareDocumentsService
├── extract_old_document(source: SourcePath) -> DocumentSource
├── extract_new_documents(source: SourcePath) -> List[DocumentSource]
├── normalize_documents(docs: List[DocumentSource]) -> List[NormalizedDocument]
├── align_sections(old: NormalizedDocument, new: NormalizedDocument) -> AlignmentResult
├── compare_aligned(alignment: AlignmentResult) -> ComparisonResult
├── validate_links(docs: List[DocumentSource]) -> LinkValidationResult
└── generate_report(comparison: ComparisonResult, links: LinkValidationResult) -> AuditReport
```

---

## 9. Quality Attributes

### 9.1 Architectural Decisions Record (ADR)

#### ADR-001: Pure Python Standard Library

**Context**: Tool must be easy to deploy without dependency management overhead.

**Decision**: Implement entirely using Python stdlib (html.parser, difflib, dataclasses, etc.).

**Consequences**:
- (+) Zero external dependencies
- (+) Easy installation and deployment
- (-) More effort for parsing (no BeautifulSoup, markdown-it)
- (-) Limited Markdown extension support

#### ADR-002: In-Memory Processing

**Context**: Documents are relatively small (megabytes, not gigabytes).

**Decision**: Process documents entirely in memory, no database.

**Consequences**:
- (+) Simpler architecture
- (+) Faster processing
- (-) Memory usage proportional to document size
- (-) No persistence between runs (except final report)

#### ADR-003: Event-Driven Context Communication

**Context**: Bounded contexts need loose coupling for maintainability.

**Decision**: Use domain events for cross-context communication.

**Consequences**:
- (+) Loose coupling between contexts
- (+) Clear audit trail of processing
- (-) Slightly more complex than direct calls
- (-) Event ordering must be managed

### 9.2 Non-Functional Requirements
| Attribute | Requirement | Measurement |
|-----------|-------------|-------------|
| **Performance** | Process 500KB HTML + 50 Markdown files in < 30 seconds | Wall clock time |
| **Accuracy** | Detect content drift with > 95% recall | Manual validation sample |
| **Usability** | CLI learnable in < 5 minutes | User testing |
| **Maintainability** | New format support in < 1 week | Development effort |
| **Reliability** | No false negatives for P0/P1 findings | Regression test suite |

---

## 10. Appendices

### Appendix A: Module Structure

```
docdiff/
├── __init__.py
├── __main__.py              # CLI entrypoint
├── cli.py                   # CLI adapter (primary port)
│
├── domain/                  # Domain model
│   ├── __init__.py
│   ├── extraction/          # Document Extraction Context
│   │   ├── __init__.py
│   │   ├── aggregates.py
│   │   ├── entities.py
│   │   ├── value_objects.py
│   │   └── services.py
│   │
│   ├── normalization/       # Content Normalization Context
│   │   ├── __init__.py
│   │   ├── aggregates.py
│   │   ├── value_objects.py
│   │   └── services.py
│   │
│   ├── alignment/           # Section Alignment Context
│   │   ├── __init__.py
│   │   ├── aggregates.py
│   │   ├── value_objects.py
│   │   └── services.py
│   │
│   ├── comparison/          # Comparison Context
│   │   ├── __init__.py
│   │   ├── aggregates.py
│   │   ├── value_objects.py
│   │   └── services.py
│   │
│   ├── reporting/           # Reporting Context
│   │   ├── __init__.py
│   │   ├── aggregates.py
│   │   ├── value_objects.py
│   │   └── services.py
│   │
│   ├── links/               # Link Validation Context
│   │   ├── __init__.py
│   │   ├── aggregates.py
│   │   ├── value_objects.py
│   │   └── services.py
│   │
│   └── events.py            # Domain events
│
├── application/             # Application services
│   ├── __init__.py
│   ├── compare_documents.py
│   └── ports.py             # Port interfaces
│
├── adapters/                # Adapters (infrastructure)
│   ├── __init__.py
│   ├── html_parser.py       # HTML ACL
│   ├── markdown_parser.py   # Markdown ACL
│   ├── file_system.py       # File I/O adapter
│   ├── http_client.py       # HTTP adapter
│   └── renderers.py         # Report renderers
│
└── shared/                  # Shared kernel
    ├── __init__.py
    ├── identifiers.py       # ID value objects
    └── result.py            # Result type
```

### Appendix B: Key Data Flows

#### B.1 Main Comparison Flow

```
1. CLI receives arguments
2. CLI adapter calls CompareDocumentsService
3. Service extracts old HTML document
   - HtmlExtractor parses via html.parser
   - HTML ACL translates to Document IR
   - DocumentExtracted event published
4. Service extracts new Markdown documents
   - MarkdownExtractor parses each .md file
   - Markdown ACL translates to Document IR
   - DocumentExtracted events published
5. Service normalizes all documents
   - TextNormalizer applies pipeline
   - DocumentNormalized events published
6. Service validates links
   - AnchorResolver builds anchor registry
   - InternalLinkValidator checks page/anchor references
   - LinksValidated event published
7. Service aligns sections
   - AlignmentStrategy executes multi-pass matching
   - SectionsAligned event published
8. Service compares aligned pairs
   - SimilarityCalculator computes scores
   - ComparisonCompleted event published
9. Service generates report
   - FindingClassifier prioritizes issues
   - MarkdownRenderer formats output
   - ReportGenerated event published
10. Report written to file system
```

### Appendix C: Glossary
| Term | Definition |
|------|------------|
| **Aggregate** | A cluster of domain objects treated as a single unit |
| **Aggregate Root** | The entry point entity for an aggregate |
| **Anti-Corruption Layer** | A translation layer protecting domain from external models |
| **Bounded Context** | A boundary within which a domain model is defined and applicable |
| **Domain Event** | Something that happened in the domain that domain experts care about |
| **Entity** | An object defined by its identity rather than attributes |
| **Port** | An interface defining how the application interacts with the outside world |
| **Adapter** | An implementation of a port that connects to external systems |
| **Value Object** | An object defined by its attributes, with no conceptual identity |
| **Ubiquitous Language** | Shared vocabulary between developers and domain experts |

---

**Document Status**: This architecture design is ready for implementation review.

**Next Steps**:
1. Review with stakeholders for domain accuracy
2. Validate data structure assumptions with sample documents
3. Prototype HTML and Markdown extraction adapters
4. Implement core domain model with unit tests
