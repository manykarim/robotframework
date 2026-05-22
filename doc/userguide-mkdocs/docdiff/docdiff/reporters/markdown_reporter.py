"""Markdown report generation for documentation comparison results.

This module provides functions to generate comprehensive Markdown and JSON
reports from ComparisonResult objects.
"""

import difflib
import json
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from docdiff.models import (
    ComparisonResult,
    Finding,
    FindingCategory,
    Priority,
    SectionMatch,
)


def _generate_mapping_table(result: ComparisonResult) -> str:
    """Generate old -> new section mapping table.

    Args:
        result: The ComparisonResult containing section matches.

    Returns:
        Markdown formatted table showing section mappings.
    """
    lines = ["## Section Mapping", ""]
    lines.append("| Old Section | New Section | Similarity |")
    lines.append("|-------------|-------------|------------|")

    for match in result.matches:
        if match.matched and match.new_section:
            old_title = match.old_section.title[:40]
            if len(match.old_section.title) > 40:
                old_title += "..."
            new_title = match.new_section.title[:40]
            if len(match.new_section.title) > 40:
                new_title += "..."
            sim = f"{match.similarity:.0%}"
            lines.append(f"| {old_title} | {new_title} | {sim} |")

    # Add unmatched sections
    unmatched = [m for m in result.matches if not m.matched]
    if unmatched:
        lines.append("")
        lines.append("### Unmatched Sections")
        lines.append("")
        for match in unmatched:
            old_title = match.old_section.title[:50]
            if len(match.old_section.title) > 50:
                old_title += "..."
            lines.append(f"- {old_title}")

    return "\n".join(lines)


def _group_findings_by_section(
    findings: List[Finding],
) -> Dict[str, List[Finding]]:
    """Group findings by their section location.

    Args:
        findings: List of findings to group.

    Returns:
        Dictionary mapping section keys to their findings.
    """
    grouped: Dict[str, List[Finding]] = defaultdict(list)
    for finding in findings:
        section = finding.section_key or finding.location or "Unknown"
        grouped[section].append(finding)
    return dict(grouped)


def _generate_diff_excerpt(
    old_content: str, new_content: str, max_lines: int = 10
) -> str:
    """Generate a truncated unified diff excerpt.

    Args:
        old_content: Original content.
        new_content: New content.
        max_lines: Maximum lines to include.

    Returns:
        Unified diff string truncated to max_lines.
    """
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)

    diff_lines = list(
        difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile="old",
            tofile="new",
            n=2,  # Smaller context for excerpts
        )
    )

    if not diff_lines:
        return "No differences found."

    # Take only the first max_lines
    result_lines = []
    for line in diff_lines[:max_lines]:
        result_lines.append(line.rstrip("\n\r"))

    if len(diff_lines) > max_lines:
        result_lines.append(f"... ({len(diff_lines) - max_lines} more lines)")

    return "\n".join(result_lines)


def _format_diff_section(match: SectionMatch) -> str:
    """Format diff for section with significant changes.

    Args:
        match: The SectionMatch to format.

    Returns:
        Markdown formatted diff section, or empty string if similarity >= 0.95.
    """
    if match.similarity >= 0.95:
        return ""  # No significant changes

    if not match.new_section:
        return ""

    lines = [f"### Diff: {match.old_section.title}", ""]
    lines.append(f"**Similarity:** {match.similarity:.1%}")
    lines.append("")
    lines.append("```diff")

    old_content = match.old_section.content or ""
    new_content = match.new_section.content or ""
    diff = _generate_diff_excerpt(old_content, new_content, max_lines=10)
    lines.append(diff)
    lines.append("```")

    return "\n".join(lines)


def _generate_statistics(result: ComparisonResult) -> str:
    """Generate detailed statistics section.

    Args:
        result: The ComparisonResult to analyze.

    Returns:
        Markdown formatted statistics section.
    """
    lines = ["## Statistics", ""]

    # Match statistics
    total = result.total_old_sections
    matched = result.matched_count
    missing = len(result.missing_sections)
    extra = len(result.extra_sections)

    lines.append("### Section Coverage")
    lines.append("")
    lines.append(f"- **Total Old Sections:** {total}")
    if total > 0:
        lines.append(f"- **Matched:** {matched} ({matched/total*100:.1f}%)")
    else:
        lines.append("- **Matched:** 0")
    lines.append(f"- **Missing:** {missing}")
    lines.append(f"- **Extra:** {extra}")

    # Similarity distribution
    similarities = [m.similarity for m in result.matches if m.matched]
    if similarities:
        lines.append("")
        lines.append("### Similarity Distribution")
        lines.append("")
        avg_sim = sum(similarities) / len(similarities)
        min_sim = min(similarities)
        max_sim = max(similarities)
        lines.append(f"- **Average Similarity:** {avg_sim:.1%}")
        lines.append(f"- **Minimum Similarity:** {min_sim:.1%}")
        lines.append(f"- **Maximum Similarity:** {max_sim:.1%}")

        # Similarity buckets
        high = len([s for s in similarities if s >= 0.9])
        medium = len([s for s in similarities if 0.7 <= s < 0.9])
        low = len([s for s in similarities if s < 0.7])
        lines.append("")
        lines.append("| Range | Count | Percentage |")
        lines.append("|-------|-------|------------|")
        total_matched = len(similarities)
        lines.append(
            f"| >= 90% | {high} | {high/total_matched*100:.1f}% |"
        )
        lines.append(
            f"| 70-89% | {medium} | {medium/total_matched*100:.1f}% |"
        )
        lines.append(
            f"| < 70% | {low} | {low/total_matched*100:.1f}% |"
        )

    # Finding statistics by category
    lines.append("")
    lines.append("### Findings by Category")
    lines.append("")
    lines.append("| Category | Count | Priority Distribution |")
    lines.append("|----------|-------|----------------------|")

    category_stats: Dict[str, Dict[str, int]] = defaultdict(
        lambda: {"total": 0, "P0": 0, "P1": 0, "P2": 0}
    )
    for finding in result.findings:
        cat = finding.category
        category_stats[cat]["total"] += 1
        priority = finding.get_priority()
        category_stats[cat][priority.name] += 1

    for cat, stats in sorted(
        category_stats.items(), key=lambda x: -x[1]["total"]
    ):
        dist_parts = []
        if stats["P0"] > 0:
            dist_parts.append(f"P0:{stats['P0']}")
        if stats["P1"] > 0:
            dist_parts.append(f"P1:{stats['P1']}")
        if stats["P2"] > 0:
            dist_parts.append(f"P2:{stats['P2']}")
        dist_str = ", ".join(dist_parts) if dist_parts else "-"
        lines.append(f"| {cat} | {stats['total']} | {dist_str} |")

    return "\n".join(lines)


def _format_grouped_findings(result: ComparisonResult) -> str:
    """Format findings grouped by section.

    Args:
        result: The ComparisonResult containing findings.

    Returns:
        Markdown formatted grouped findings section.
    """
    lines = ["## Findings by Section", ""]

    grouped = _group_findings_by_section(result.findings)

    if not grouped:
        lines.append("*No findings to display.*")
        return "\n".join(lines)

    # Sort sections by number of findings (descending)
    sorted_sections = sorted(
        grouped.items(), key=lambda x: len(x[1]), reverse=True
    )

    for section_key, findings in sorted_sections:
        # Count by priority for this section
        p0_count = len([f for f in findings if f.get_priority() == Priority.P0])
        p1_count = len([f for f in findings if f.get_priority() == Priority.P1])
        p2_count = len([f for f in findings if f.get_priority() == Priority.P2])

        priority_str = []
        if p0_count:
            priority_str.append(f"{p0_count} critical")
        if p1_count:
            priority_str.append(f"{p1_count} important")
        if p2_count:
            priority_str.append(f"{p2_count} minor")

        lines.append(f"### {section_key}")
        lines.append("")
        lines.append(f"**{len(findings)} findings** ({', '.join(priority_str)})")
        lines.append("")

        for finding in findings:
            lines.append(format_finding(finding))
            lines.append("")

    return "\n".join(lines)


def generate_markdown_report(result: ComparisonResult) -> str:
    """Generate a comprehensive Markdown report from comparison results.

    Args:
        result: The ComparisonResult object containing all comparison data.

    Returns:
        A formatted Markdown string containing the full report.
    """
    lines: List[str] = []
    stats = generate_summary_stats(result)
    timestamp = result.timestamp or datetime.now().isoformat()

    # Header
    lines.append("# Documentation Comparison Report")
    lines.append("")
    lines.append(f"**Generated:** {timestamp}")
    lines.append(f"**Old Source:** {result.old_source}")
    lines.append(f"**New Source:** {result.new_source}")
    lines.append("")

    # Executive Summary
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(f"- **Total Old Sections:** {stats['total_old_sections']}")
    lines.append(
        f"- **Matched Sections:** {stats['matched_count']} "
        f"({stats['match_percentage']:.1f}%)"
    )
    lines.append(f"- **Missing Sections:** {stats['missing_count']}")
    lines.append(f"- **Extra Sections:** {stats['extra_count']}")
    lines.append(f"- **Total Findings:** {stats['total_findings']}")
    lines.append("")

    # Findings Summary Table
    lines.append("### Findings Summary")
    lines.append("")
    lines.append("| Priority | Count | Categories |")
    lines.append("|----------|-------|------------|")

    for priority in [Priority.P0, Priority.P1, Priority.P2]:
        priority_stats = stats["by_priority"].get(priority.name, {})
        count = priority_stats.get("count", 0)
        categories = priority_stats.get("categories", [])
        cat_str = ", ".join(categories[:3])
        if len(categories) > 3:
            cat_str += f" (+{len(categories) - 3} more)"
        lines.append(f"| {priority.name} | {count} | {cat_str or '-'} |")

    lines.append("")

    # Section Mapping Table (NEW)
    lines.append(_generate_mapping_table(result))
    lines.append("")

    # Statistics Section (NEW - enhanced)
    lines.append(_generate_statistics(result))
    lines.append("")

    # Critical Issues (P0)
    p0_findings = result.get_findings_by_priority(Priority.P0)
    lines.append("## Critical Issues (P0)")
    lines.append("")
    if p0_findings:
        for finding in p0_findings:
            lines.append(format_finding(finding))
            lines.append("")
    else:
        lines.append("*No critical issues found.*")
        lines.append("")

    # Important Issues (P1)
    p1_findings = result.get_findings_by_priority(Priority.P1)
    lines.append("## Important Issues (P1)")
    lines.append("")
    if p1_findings:
        for finding in p1_findings:
            lines.append(format_finding(finding))
            lines.append("")
    else:
        lines.append("*No important issues found.*")
        lines.append("")

    # Minor Issues (P2)
    p2_findings = result.get_findings_by_priority(Priority.P2)
    lines.append("## Minor Issues (P2)")
    lines.append("")
    if p2_findings:
        for finding in p2_findings:
            lines.append(format_finding(finding))
            lines.append("")
    else:
        lines.append("*No minor issues found.*")
        lines.append("")

    # Findings by Section (NEW - grouped view)
    lines.append(_format_grouped_findings(result))
    lines.append("")

    # Section-by-Section Analysis
    lines.append("## Section-by-Section Analysis")
    lines.append("")

    if result.matches:
        for match in result.matches:
            lines.append(_format_section_match(match))
            lines.append("")
    else:
        lines.append("*No section matches to analyze.*")
        lines.append("")

    # Missing Sections
    lines.append("## Missing Sections")
    lines.append("")
    if result.missing_sections:
        lines.append(
            "The following sections from the old documentation were not found "
            "in the new documentation:"
        )
        lines.append("")
        for section in result.missing_sections:
            number_str = f"{section.number} " if section.number else ""
            lines.append(f"- **{number_str}{section.title}** (`{section.key}`)")
    else:
        lines.append("*No missing sections.*")
    lines.append("")

    # Extra Sections
    lines.append("## Extra Sections")
    lines.append("")
    if result.extra_sections:
        lines.append(
            "The following sections in the new documentation were not found "
            "in the old documentation:"
        )
        lines.append("")
        for section in result.extra_sections:
            number_str = f"{section.number} " if section.number else ""
            lines.append(f"- **{number_str}{section.title}** (`{section.key}`)")
    else:
        lines.append("*No extra sections.*")
    lines.append("")

    # Significant Changes with Diffs (NEW - inline diffs for changed sections)
    lines.append("## Significant Content Changes")
    lines.append("")
    significant_changes = [
        m for m in result.matches
        if m.matched and m.new_section and m.similarity < 0.95
    ]
    if significant_changes:
        lines.append(
            f"The following {len(significant_changes)} sections have significant "
            "content differences (similarity < 95%):"
        )
        lines.append("")
        for match in sorted(significant_changes, key=lambda m: m.similarity):
            diff_section = _format_diff_section(match)
            if diff_section:
                lines.append(diff_section)
                lines.append("")
    else:
        lines.append("*No significant content changes detected.*")
        lines.append("")

    # Appendix: Detailed Diffs
    lines.append("## Appendix: Detailed Diffs")
    lines.append("")

    significant_diffs = _get_significant_diffs(result)
    if significant_diffs:
        for match, old_content, new_content in significant_diffs:
            section_title = match.old_section.title
            number_str = (
                f"{match.old_section.number} " if match.old_section.number else ""
            )
            lines.append(f"### {number_str}{section_title}")
            lines.append("")
            lines.append(f"**Similarity:** {match.similarity * 100:.1f}%")
            lines.append("")
            diff_text = format_diff(old_content, new_content)
            lines.append(diff_text)
            lines.append("")
    else:
        lines.append("*No significant diffs to display.*")
        lines.append("")

    return "\n".join(lines)


def generate_json_report(result: ComparisonResult) -> str:
    """Generate a JSON report from comparison results.

    Args:
        result: The ComparisonResult object containing all comparison data.

    Returns:
        A JSON string containing the full report data.
    """
    stats = generate_summary_stats(result)

    report_data = {
        "report_type": "documentation_comparison",
        "generated_at": result.timestamp or datetime.now().isoformat(),
        "sources": {
            "old": result.old_source,
            "new": result.new_source,
        },
        "summary": {
            "total_old_sections": stats["total_old_sections"],
            "matched_count": stats["matched_count"],
            "match_percentage": stats["match_percentage"],
            "missing_count": stats["missing_count"],
            "extra_count": stats["extra_count"],
            "total_findings": stats["total_findings"],
        },
        "findings_by_priority": {
            priority.name: {
                "count": stats["by_priority"].get(priority.name, {}).get("count", 0),
                "categories": stats["by_priority"]
                .get(priority.name, {})
                .get("categories", []),
                "findings": [
                    f.to_dict() for f in result.get_findings_by_priority(priority)
                ],
            }
            for priority in [Priority.P0, Priority.P1, Priority.P2]
        },
        "findings_by_category": {
            cat: {
                "count": stats["by_category"].get(cat, 0),
                "findings": [f.to_dict() for f in result.get_findings_by_category(cat)],
            }
            for cat in stats["by_category"].keys()
        },
        "section_matches": [m.to_dict() for m in result.matches],
        "missing_sections": [
            {
                "key": s.key,
                "title": s.title,
                "number": s.number,
                "level": s.level,
                "source_line": s.source_line,
            }
            for s in result.missing_sections
        ],
        "extra_sections": [
            {
                "key": s.key,
                "title": s.title,
                "number": s.number,
                "level": s.level,
                "source_line": s.source_line,
            }
            for s in result.extra_sections
        ],
        "metadata": result.metadata,
    }

    return json.dumps(report_data, indent=2, ensure_ascii=False)


def format_finding(finding: Finding) -> str:
    """Format a single finding as Markdown.

    Args:
        finding: The Finding object to format.

    Returns:
        A Markdown-formatted string representing the finding.
    """
    lines: List[str] = []

    # Priority indicator
    priority_icons = {
        Priority.P0: "[CRITICAL]",
        Priority.P1: "[IMPORTANT]",
        Priority.P2: "[MINOR]",
    }
    icon = priority_icons.get(finding.priority, "[INFO]")

    # Main message
    location = finding.location or finding.section_key
    if location:
        lines.append(f"- {icon} **{finding.category}** in `{location}`")
    else:
        lines.append(f"- {icon} **{finding.category}**")

    lines.append(f"  - {finding.message}")

    # Old/new values comparison
    if finding.old_value is not None or finding.new_value is not None:
        if finding.old_value is not None:
            old_display = _truncate_text(finding.old_value, 100)
            lines.append(f"  - **Old:** `{old_display}`")
        if finding.new_value is not None:
            new_display = _truncate_text(finding.new_value, 100)
            lines.append(f"  - **New:** `{new_display}`")

    # Evidence
    if finding.evidence:
        evidence_display = _truncate_text(finding.evidence, 200)
        lines.append(f"  - **Evidence:** {evidence_display}")

    # Line number
    if finding.line_number is not None:
        lines.append(f"  - **Line:** {finding.line_number}")

    # Suggestion
    if finding.suggestion:
        lines.append(f"  - **Suggestion:** {finding.suggestion}")

    return "\n".join(lines)


def format_diff(
    old_text: str, new_text: str, context: int = 3, max_lines: int = 50
) -> str:
    """Format a unified diff as a Markdown code block.

    Args:
        old_text: The original text content.
        new_text: The new text content.
        context: Number of context lines around changes.
        max_lines: Maximum number of diff lines to include.

    Returns:
        A Markdown code block containing the unified diff.
    """
    old_lines = old_text.splitlines(keepends=True)
    new_lines = new_text.splitlines(keepends=True)

    diff_lines = list(
        difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile="old",
            tofile="new",
            n=context,
        )
    )

    if not diff_lines:
        return "*No differences.*"

    # Truncate if too long
    truncated = False
    if len(diff_lines) > max_lines:
        diff_lines = diff_lines[:max_lines]
        truncated = True

    # Format as code block
    result_lines = ["```diff"]
    for line in diff_lines:
        # Remove trailing newline for cleaner output
        result_lines.append(line.rstrip("\n\r"))
    result_lines.append("```")

    if truncated:
        result_lines.append(f"*... diff truncated (showing first {max_lines} lines)*")

    return "\n".join(result_lines)


def generate_summary_stats(result: ComparisonResult) -> Dict[str, Any]:
    """Compute aggregate statistics from comparison results.

    Args:
        result: The ComparisonResult object to analyze.

    Returns:
        A dictionary containing computed statistics including:
        - total_old_sections: Total sections in old documentation
        - matched_count: Number of matched sections
        - match_percentage: Percentage of sections matched
        - missing_count: Number of missing sections
        - extra_count: Number of extra sections
        - total_findings: Total number of findings
        - by_priority: Findings grouped by priority level
        - by_category: Findings grouped by category
    """
    # Basic counts
    total_old = result.total_old_sections
    matched = result.matched_count
    match_pct = result.match_percentage

    # Group findings by priority
    by_priority: Dict[str, Dict[str, Any]] = {}
    for priority in Priority:
        findings = result.get_findings_by_priority(priority)
        categories = list(set(f.category for f in findings))
        by_priority[priority.name] = {
            "count": len(findings),
            "categories": categories,
        }

    # Group findings by category
    by_category: Dict[str, int] = defaultdict(int)
    for finding in result.findings:
        by_category[finding.category] += 1

    # Similarity statistics for matched sections
    similarities = [m.similarity for m in result.matches if m.matched]
    avg_similarity = sum(similarities) / len(similarities) if similarities else 0.0
    min_similarity = min(similarities) if similarities else 0.0
    max_similarity = max(similarities) if similarities else 0.0

    # Coverage by category
    category_coverage: Dict[str, Dict[str, int]] = defaultdict(
        lambda: {"total": 0, "issues": 0}
    )
    for finding in result.findings:
        category_coverage[finding.category]["issues"] += 1

    return {
        "total_old_sections": total_old,
        "matched_count": matched,
        "match_percentage": match_pct,
        "missing_count": len(result.missing_sections),
        "extra_count": len(result.extra_sections),
        "total_findings": len(result.findings),
        "by_priority": by_priority,
        "by_category": dict(by_category),
        "similarity_stats": {
            "average": avg_similarity,
            "minimum": min_similarity,
            "maximum": max_similarity,
        },
        "category_coverage": dict(category_coverage),
    }


def _format_section_match(match: SectionMatch) -> str:
    """Format a section match for the Markdown report.

    Args:
        match: The SectionMatch object to format.

    Returns:
        A Markdown-formatted string for the section.
    """
    lines: List[str] = []

    # Section header
    number_str = f"{match.old_section.number} " if match.old_section.number else ""
    lines.append(f"### {number_str}{match.old_section.title}")
    lines.append("")

    if match.matched and match.new_section:
        new_title = match.new_section.title
        new_number = f"{match.new_section.number} " if match.new_section.number else ""
        lines.append(f"- **Match:** {new_number}{new_title}")
        lines.append(f"- **Similarity:** {match.similarity * 100:.1f}%")
    else:
        lines.append("- **Match:** *Not found*")
        lines.append("- **Similarity:** N/A")

    lines.append(f"- **Findings:** {len(match.findings)} issues")
    lines.append("")

    # List findings for this section
    if match.findings:
        for finding in match.findings:
            lines.append(format_finding(finding))
            lines.append("")

    return "\n".join(lines)


def _get_significant_diffs(
    result: ComparisonResult, threshold: float = 0.95
) -> List[tuple]:
    """Get section matches with significant content differences.

    Args:
        result: The ComparisonResult to analyze.
        threshold: Similarity threshold below which diffs are significant.

    Returns:
        List of tuples (match, old_content, new_content) for significant diffs.
    """
    significant = []

    for match in result.matches:
        if match.matched and match.new_section:
            if match.similarity < threshold:
                old_content = match.old_section.content or ""
                new_content = match.new_section.content or ""
                if old_content or new_content:
                    significant.append((match, old_content, new_content))

    # Sort by similarity (lowest first)
    significant.sort(key=lambda x: x[0].similarity)

    return significant[:10]  # Limit to top 10 most different


def _truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to a maximum length with ellipsis.

    Args:
        text: The text to truncate.
        max_length: Maximum length before truncation.

    Returns:
        The truncated text with ellipsis if needed.
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."
