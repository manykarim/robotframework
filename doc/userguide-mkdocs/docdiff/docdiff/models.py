"""Data models for the docdiff comparison tool."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class BlockType(Enum):
    """Types of content blocks."""
    PARAGRAPH = "paragraph"
    CODE = "code"
    TABLE = "table"
    LIST = "list"
    HEADING = "heading"
    LINK = "link"
    IMAGE = "image"
    ADMONITION = "admonition"
    UNKNOWN = "unknown"


class Severity(Enum):
    """Severity levels for findings."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Priority(Enum):
    """Priority levels for findings (compatible with CLI exit codes).

    P0: Critical issues that must be addressed immediately (exit code 2)
    P1: Important issues that should be addressed soon (exit code 2)
    P2: Minor issues or suggestions for improvement (exit code 1)
    """
    P0 = 0  # Critical
    P1 = 1  # Important
    P2 = 2  # Minor

    @classmethod
    def from_severity(cls, severity: Severity) -> "Priority":
        """Convert a Severity to a Priority level."""
        mapping = {
            Severity.CRITICAL: cls.P0,
            Severity.ERROR: cls.P0,
            Severity.WARNING: cls.P1,
            Severity.INFO: cls.P2,
        }
        return mapping.get(severity, cls.P2)


class FindingCategory(Enum):
    """Categories for classifying findings."""
    CONTENT_MISSING = "content_missing"
    CONTENT_CHANGED = "content_changed"
    CONTENT_ADDED = "content_added"
    STRUCTURE_CHANGED = "structure_changed"
    FORMATTING_CHANGED = "formatting_changed"
    LINK_BROKEN = "link_broken"
    LINK_CHANGED = "link_changed"
    CODE_BLOCK_CHANGED = "code_block_changed"
    TABLE_CHANGED = "table_changed"
    IMAGE_MISSING = "image_missing"
    ANCHOR_MISSING = "anchor_missing"
    HEADING_LEVEL_CHANGED = "heading_level_changed"
    SEMANTIC_DRIFT = "semantic_drift"
    WHITESPACE_ONLY = "whitespace_only"


@dataclass
class Block:
    """A content block within a section.

    This class supports two initialization patterns:
    1. New style: block_type (BlockType enum), content (str)
    2. Legacy style: text (str), block_type (str), plus optional extras
    """
    block_type: BlockType | str = BlockType.UNKNOWN
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    line_number: int | None = None
    # Extended attributes for extractors
    text: str | None = None  # alias for content
    language: str | None = None  # for code blocks
    source_line: int | None = None  # alias for line_number
    admonition_type: str | None = None
    level: int | None = None  # for lists
    ordered: bool | None = None  # for lists
    items: list[str] | None = None  # for lists
    href: str | None = None  # for links
    src: str | None = None  # for images
    alt: str | None = None  # for images
    alt_text: str | None = None  # alias for alt (for images)
    matrix: list[list[str]] | None = None  # for tables
    anchor: str | None = None  # for headings
    list_type: str | None = None  # for lists (ordered/unordered)

    def __post_init__(self):
        """Normalize attributes after initialization."""
        # Handle text/content aliasing
        if self.text is not None and not self.content:
            self.content = self.text
        elif self.content and self.text is None:
            self.text = self.content

        # Handle source_line/line_number aliasing
        if self.source_line is not None and self.line_number is None:
            self.line_number = self.source_line
        elif self.line_number is not None and self.source_line is None:
            self.source_line = self.line_number

        # Convert string block_type to enum if needed
        if isinstance(self.block_type, str):
            type_map = {
                "paragraph": BlockType.PARAGRAPH,
                "code": BlockType.CODE,
                "code_block": BlockType.CODE,
                "table": BlockType.TABLE,
                "list": BlockType.LIST,
                "heading": BlockType.HEADING,
                "link": BlockType.LINK,
                "image": BlockType.IMAGE,
                "admonition": BlockType.ADMONITION,
            }
            self.block_type = type_map.get(self.block_type.lower(), BlockType.UNKNOWN)

        # Store extra attributes in metadata
        if self.language and "language" not in self.metadata:
            self.metadata["language"] = self.language
        if self.admonition_type and "admonition_type" not in self.metadata:
            self.metadata["admonition_type"] = self.admonition_type
        if self.level is not None and "level" not in self.metadata:
            self.metadata["level"] = self.level
        if self.ordered is not None and "ordered" not in self.metadata:
            self.metadata["ordered"] = self.ordered
        if self.items and "items" not in self.metadata:
            self.metadata["items"] = self.items
        if self.href and "href" not in self.metadata:
            self.metadata["href"] = self.href
        if self.src and "src" not in self.metadata:
            self.metadata["src"] = self.src
        if self.alt and "alt" not in self.metadata:
            self.metadata["alt"] = self.alt
        if self.matrix and "matrix" not in self.metadata:
            self.metadata["matrix"] = self.matrix
        if self.anchor and "anchor" not in self.metadata:
            self.metadata["anchor"] = self.anchor
        if self.list_type and "list_type" not in self.metadata:
            self.metadata["list_type"] = self.list_type
        # Handle alt_text/alt aliasing
        if self.alt_text is not None and self.alt is None:
            self.alt = self.alt_text
        elif self.alt is not None and self.alt_text is None:
            self.alt_text = self.alt

    def to_dict(self) -> dict[str, Any]:
        """Convert block to dictionary representation."""
        return {
            "type": self.block_type.value if isinstance(self.block_type, BlockType) else self.block_type,
            "content": self.content,
            "metadata": self.metadata,
            "line_number": self.line_number,
        }


@dataclass
class Section:
    """A section of the document with a heading and content blocks.

    Supports both structured blocks and raw content approaches.
    """
    title: str
    key: str  # normalized key for matching
    level: int = 1  # heading level (1-6)
    number: str = ""  # e.g., "2.1.3"
    blocks: list[Block] = field(default_factory=list)
    subsections: list["Section"] = field(default_factory=list)
    parent: "Section | None" = None
    line_number: int | None = None
    # Extended attributes for extractors
    content: str = ""  # raw content (alternative to blocks)
    source_type: str = ""  # e.g., "markdown", "html"
    source_path: str = ""  # file path
    anchor: str = ""  # anchor ID
    children: list["Section"] = field(default_factory=list)  # alias for subsections
    parent_key: str | None = None  # key of parent section for context matching

    def __post_init__(self):
        """Normalize attributes after initialization."""
        # Sync children and subsections
        if self.children and not self.subsections:
            self.subsections = self.children
        elif self.subsections and not self.children:
            self.children = self.subsections

    def to_dict(self) -> dict[str, Any]:
        """Convert section to dictionary representation."""
        return {
            "number": self.number,
            "title": self.title,
            "level": self.level,
            "key": self.key,
            "line_number": self.line_number,
            "source_type": self.source_type,
            "content": self.content[:100] + "..." if len(self.content) > 100 else self.content,
            "blocks": [block.to_dict() for block in self.blocks],
            "subsections": [sub.to_dict() for sub in self.subsections],
        }

    def get_full_path(self) -> str:
        """Get the full hierarchical path of this section."""
        parts = []
        current: Section | None = self
        while current is not None:
            if current.title:
                parts.append(current.title)
            current = current.parent
        return " > ".join(reversed(parts))


@dataclass
class Finding:
    """A comparison finding/issue."""
    category: str
    message: str
    severity: Severity | None = None  # Can be set explicitly or derived from priority
    source_location: str | None = None
    target_location: str | None = None
    source_content: str | None = None
    target_content: str | None = None
    suggestion: str | None = None
    priority: Priority | None = None  # Can be set explicitly or derived from severity
    # Extended attributes for reporter compatibility
    location: str | None = None  # alias for source_location
    section_key: str | None = None
    old_value: str | None = None  # alias for source_content
    new_value: str | None = None  # alias for target_content
    evidence: str | None = None
    line_number: int | None = None
    block_type: str | None = None  # Type of block this finding relates to

    def __post_init__(self):
        """Normalize aliases after initialization."""
        # Derive severity from priority if not provided
        if self.severity is None and self.priority is not None:
            priority_to_severity = {
                Priority.P0: Severity.CRITICAL,
                Priority.P1: Severity.WARNING,
                Priority.P2: Severity.INFO,
            }
            self.severity = priority_to_severity.get(self.priority, Severity.INFO)
        elif self.severity is None:
            self.severity = Severity.INFO

        # Handle location/source_location aliasing
        if self.location is None and self.source_location:
            self.location = self.source_location
        elif self.source_location is None and self.location:
            self.source_location = self.location
        # Handle old_value/source_content aliasing
        if self.old_value is None and self.source_content:
            self.old_value = self.source_content
        elif self.source_content is None and self.old_value:
            self.source_content = self.old_value
        # Handle new_value/target_content aliasing
        if self.new_value is None and self.target_content:
            self.new_value = self.target_content
        elif self.target_content is None and self.new_value:
            self.target_content = self.new_value

    def get_priority(self) -> Priority:
        """Get the priority level for this finding."""
        if self.priority is not None:
            return self.priority
        return Priority.from_severity(self.severity)

    def to_dict(self) -> dict[str, Any]:
        """Convert finding to dictionary representation for JSON serialization."""
        return {
            "category": self.category,
            "message": self.message,
            "severity": self.severity.value if self.severity else None,
            "priority": self.get_priority().name,
            "source_location": self.source_location,
            "target_location": self.target_location,
            "source_content": self.source_content,
            "target_content": self.target_content,
            "suggestion": self.suggestion,
            "section_key": self.section_key,
            "evidence": self.evidence,
            "line_number": self.line_number,
            "block_type": self.block_type,
        }

    def to_markdown(self) -> str:
        """Convert finding to Markdown format."""
        lines = [f"### {self.severity.value.upper()}: {self.category}"]
        lines.append("")
        lines.append(self.message)

        if self.source_location:
            lines.append("")
            lines.append(f"**Source Location:** {self.source_location}")

        if self.target_location:
            lines.append(f"**Target Location:** {self.target_location}")

        if self.source_content:
            lines.append("")
            lines.append("**Source Content:**")
            lines.append(f"```\n{self.source_content}\n```")

        if self.target_content:
            lines.append("")
            lines.append("**Target Content:**")
            lines.append(f"```\n{self.target_content}\n```")

        if self.suggestion:
            lines.append("")
            lines.append(f"**Suggestion:** {self.suggestion}")

        return "\n".join(lines)


@dataclass
class AlignmentResult:
    """Result of section alignment."""
    matched: list[tuple[Section, Section]] = field(default_factory=list)
    source_only: list[Section] = field(default_factory=list)
    target_only: list[Section] = field(default_factory=list)
    match_stats: dict[str, int] = field(default_factory=dict)

    def get_match_rate(self) -> float:
        """Calculate the match rate as a percentage."""
        total = len(self.matched) + len(self.source_only) + len(self.target_only)
        if total == 0:
            return 100.0
        return (len(self.matched) / total) * 100


@dataclass
class SectionMatch:
    """Represents a match between an old and new section."""
    old_section: Section
    new_section: Section | None = None
    similarity: float = 0.0
    matched: bool = False
    findings: list["Finding"] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "old_section": self.old_section.title if self.old_section else None,
            "new_section": self.new_section.title if self.new_section else None,
            "similarity": self.similarity,
            "matched": self.matched,
            "findings_count": len(self.findings),
        }


@dataclass
class ComparisonResult:
    """Overall comparison result."""
    source_file: str
    target_file: str
    findings: list[Finding] = field(default_factory=list)
    alignment: AlignmentResult | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    # Extended attributes for reporter compatibility
    matches: list[SectionMatch] = field(default_factory=list)
    missing_sections: list[Section] = field(default_factory=list)
    extra_sections: list[Section] = field(default_factory=list)
    timestamp: str = ""

    @property
    def old_source(self) -> str:
        """Alias for source_file for reporter compatibility."""
        return self.source_file

    @property
    def new_source(self) -> str:
        """Alias for target_file for reporter compatibility."""
        return self.target_file

    @property
    def total_old_sections(self) -> int:
        """Total number of sections in old document."""
        return len(self.matches) + len(self.missing_sections)

    @property
    def matched_count(self) -> int:
        """Number of successfully matched sections."""
        return len([m for m in self.matches if m.matched])

    @property
    def match_percentage(self) -> float:
        """Percentage of old sections that were matched."""
        total = self.total_old_sections
        if total == 0:
            return 100.0
        return (self.matched_count / total) * 100

    def get_findings_by_priority(self, priority: Priority) -> list[Finding]:
        """Get findings filtered by priority level."""
        return [f for f in self.findings if f.get_priority() == priority]

    def get_findings_by_category(self, category: str) -> list[Finding]:
        """Get findings filtered by category."""
        return [f for f in self.findings if f.category == category]

    def has_critical_findings(self) -> bool:
        """Check if there are any P0 or P1 (critical/important) findings."""
        for finding in self.findings:
            priority = finding.get_priority()
            if priority in (Priority.P0, Priority.P1):
                return True
        return False

    def has_warnings(self) -> bool:
        """Check if there are P2 findings."""
        for finding in self.findings:
            if finding.get_priority() == Priority.P2:
                return True
        return False

    def get_exit_code(self, strict: bool = False) -> int:
        """Determine exit code based on findings.

        Args:
            strict: If True, return 2 for P0/P1 findings or any findings at all.

        Returns:
            0 - Success (no P0/P1 findings)
            1 - Warnings only (P2 findings)
            2 - Errors (P0/P1 findings, or with --strict any findings)
        """
        if self.has_critical_findings():
            return 2
        if strict and self.has_warnings():
            return 2
        if self.has_warnings():
            return 1
        return 0

    def to_dict(self) -> dict[str, Any]:
        """Convert result to a dictionary for JSON serialization."""
        return {
            "source_file": self.source_file,
            "target_file": self.target_file,
            "metadata": self.metadata,
            "summary": self.summary(),
            "findings": [
                {
                    "category": f.category,
                    "severity": f.severity.value,
                    "priority": f.get_priority().name,
                    "message": f.message,
                    "source_location": f.source_location,
                    "target_location": f.target_location,
                    "source_content": f.source_content,
                    "target_content": f.target_content,
                    "suggestion": f.suggestion,
                }
                for f in self.findings
            ],
            "alignment": {
                "matched_count": len(self.alignment.matched) if self.alignment else 0,
                "source_only_count": len(self.alignment.source_only) if self.alignment else 0,
                "target_only_count": len(self.alignment.target_only) if self.alignment else 0,
                "match_rate": self.alignment.get_match_rate() if self.alignment else 0.0,
            },
        }

    def summary(self) -> dict[str, Any]:
        """Generate a summary of the comparison results."""
        severity_counts = {s.value: 0 for s in Severity}
        priority_counts = {p.name: 0 for p in Priority}
        category_counts: dict[str, int] = {}

        for finding in self.findings:
            severity_counts[finding.severity.value] += 1
            priority_counts[finding.get_priority().name] += 1
            category_counts[finding.category] = category_counts.get(finding.category, 0) + 1

        match_rate = 0.0
        if self.alignment:
            match_rate = self.alignment.get_match_rate()

        return {
            "source_file": self.source_file,
            "target_file": self.target_file,
            "total_findings": len(self.findings),
            "by_severity": severity_counts,
            "by_priority": priority_counts,
            "by_category": category_counts,
            "match_rate": match_rate,
            "metadata": self.metadata,
        }
