"""Reporter modules for generating comparison reports.

This package provides functions to generate reports from ComparisonResult
objects in various formats including Markdown and JSON.
"""

from docdiff.reporters.markdown_reporter import (
    format_diff,
    format_finding,
    generate_json_report,
    generate_markdown_report,
    generate_summary_stats,
)

__all__ = [
    "generate_markdown_report",
    "generate_json_report",
    "format_finding",
    "format_diff",
    "generate_summary_stats",
]
