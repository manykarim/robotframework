"""Command-line interface for docdiff documentation comparison tool.

This module provides the CLI for comparing old HTML documentation with
new Markdown documentation, detecting content drift and generating reports.
"""

import argparse
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from docdiff import __version__
from docdiff.models import (
    AlignmentResult,
    ComparisonResult,
    Finding,
    FindingCategory,
    Priority,
    Section,
    Severity,
)

# Lazy imports to avoid circular dependencies and speed up --help
_extractors = None
_aligners = None
_comparators = None
_validators = None
_reporters = None


def _get_extractors():
    """Lazy load extractors module."""
    global _extractors
    if _extractors is None:
        from docdiff import extractors as _extractors
    return _extractors


def _get_aligners():
    """Lazy load aligners module."""
    global _aligners
    if _aligners is None:
        from docdiff import aligners as _aligners
    return _aligners


def _get_comparators():
    """Lazy load comparators module."""
    global _comparators
    if _comparators is None:
        from docdiff import comparators as _comparators
    return _comparators


def _get_validators():
    """Lazy load validators module."""
    global _validators
    if _validators is None:
        from docdiff import validators as _validators
    return _validators


def _get_reporters():
    """Lazy load reporters module."""
    global _reporters
    if _reporters is None:
        from docdiff import reporters as _reporters
    return _reporters


logger = logging.getLogger("docdiff")


def setup_logging(verbose: bool = False, quiet: bool = False) -> None:
    """Configure logging based on verbosity settings.

    Args:
        verbose: If True, set log level to DEBUG.
        quiet: If True, set log level to ERROR (only errors shown).
               If both verbose and quiet are True, quiet takes precedence.
    """
    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    # Configure root logger
    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
    )

    # Set our logger specifically
    logger.setLevel(level)


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="docdiff",
        description="Documentation comparison tool for RST to Markdown migrations",
        epilog="""
Exit Codes:
  0 - Success (no P0/P1 findings)
  1 - Warnings only (P2 findings)
  2 - Errors (P0/P1 findings, or with --strict)

Examples:
  docdiff --old-html userguide.html --new-md-dir docs/
  docdiff --old-html userguide.html --new-md-dir docs/ --format json --out report.json
  docdiff --old-html userguide.html --new-md-dir docs/ --section "^2\\." --min-similarity 0.85
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Required arguments
    required = parser.add_argument_group("required arguments")
    required.add_argument(
        "--old-html",
        metavar="FILE",
        required=True,
        help="Path to old HTML documentation file",
    )
    required.add_argument(
        "--new-md-dir",
        metavar="DIR",
        required=True,
        help="Path to new Markdown documentation directory",
    )

    # Output options
    output = parser.add_argument_group("output options")
    output.add_argument(
        "--out",
        "-o",
        metavar="FILE",
        help="Output report file (default: stdout)",
    )
    output.add_argument(
        "--format",
        "-f",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format: markdown, json (default: markdown)",
    )

    # URL options for link validation
    urls = parser.add_argument_group("URL options")
    urls.add_argument(
        "--base-url-old",
        metavar="URL",
        help="Base URL for old documentation (for link validation)",
    )
    urls.add_argument(
        "--base-url-new",
        metavar="URL",
        help="Base URL for new documentation (for link validation)",
    )

    # Filtering options
    filtering = parser.add_argument_group("filtering options")
    filtering.add_argument(
        "--section",
        metavar="PATTERN",
        help="Only compare sections matching regex pattern",
    )
    filtering.add_argument(
        "--min-similarity",
        metavar="N",
        type=float,
        default=0.90,
        help="Minimum similarity threshold 0-1 (default: 0.90)",
    )

    # Behavior options
    behavior = parser.add_argument_group("behavior options")
    behavior.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 2 on P0/P1 findings",
    )
    behavior.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )
    behavior.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Quiet mode (errors only)",
    )

    # Version
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    return parser


def validate_args(args: argparse.Namespace) -> List[str]:
    """Validate command-line arguments.

    Args:
        args: Parsed command-line arguments.

    Returns:
        List of error messages (empty if valid).
    """
    errors = []

    # Check old HTML file exists
    if not os.path.isfile(args.old_html):
        errors.append(f"Old HTML file not found: {args.old_html}")

    # Check new MD directory exists
    if not os.path.isdir(args.new_md_dir):
        errors.append(f"New Markdown directory not found: {args.new_md_dir}")

    # Check output directory exists if specified
    if args.out:
        out_dir = os.path.dirname(args.out)
        if out_dir and not os.path.isdir(out_dir):
            errors.append(f"Output directory not found: {out_dir}")

    # Validate similarity threshold
    if not 0 <= args.min_similarity <= 1:
        errors.append(f"Similarity threshold must be between 0 and 1: {args.min_similarity}")

    # Validate regex pattern if provided
    if args.section:
        try:
            re.compile(args.section)
        except re.error as e:
            errors.append(f"Invalid section regex pattern: {e}")

    return errors


def filter_sections_by_pattern(
    sections: List[Section], pattern: str
) -> List[Section]:
    """Filter sections to only include those matching the pattern.

    Args:
        sections: List of sections to filter.
        pattern: Regex pattern to match against section keys or numbers.

    Returns:
        Filtered list of sections.
    """
    regex = re.compile(pattern)
    filtered = []

    for section in sections:
        # Match against section number if present
        if section.number and regex.search(section.number):
            filtered.append(section)
        # Also match against section key
        elif regex.search(section.key):
            filtered.append(section)
        # Match against title
        elif regex.search(section.title):
            filtered.append(section)

    return filtered


def flatten_all_sections(sections: List[Section]) -> List[Section]:
    """Recursively flatten a section hierarchy into a flat list.

    Args:
        sections: List of top-level sections with subsections.

    Returns:
        Flat list of all sections including nested subsections.
    """
    result = []
    for section in sections:
        result.append(section)
        # Support both 'children' (old model) and 'subsections' (new model)
        children = getattr(section, 'subsections', None) or getattr(section, 'children', [])
        if children:
            result.extend(flatten_all_sections(children))
    return result


def run_comparison(args: argparse.Namespace) -> ComparisonResult:
    """Run the documentation comparison.

    Args:
        args: Parsed command-line arguments.

    Returns:
        ComparisonResult containing all findings and statistics.
    """
    extractors = _get_extractors()
    aligners = _get_aligners()
    comparators = _get_comparators()
    validators = _get_validators()
    reporters = _get_reporters()

    logger.info("Starting documentation comparison...")
    logger.info(f"  Old HTML: {args.old_html}")
    logger.info(f"  New MD dir: {args.new_md_dir}")

    # Initialize result
    timestamp = datetime.now().isoformat()

    # Step 1: Extract sections from old HTML
    logger.info("Extracting sections from old HTML...")
    try:
        old_sections = extractors.extract_from_html_file(args.old_html)
        logger.debug(f"Extracted {len(old_sections)} top-level sections from HTML")
    except FileNotFoundError:
        logger.error(f"HTML file not found: {args.old_html}")
        raise
    except Exception as e:
        logger.error(f"Error extracting HTML: {e}")
        raise

    # Step 2: Extract sections from new Markdown directory
    logger.info("Extracting sections from Markdown directory...")
    try:
        md_sections_by_file = extractors.extract_from_directory(args.new_md_dir)
        # Flatten all markdown sections into a single list
        new_sections = []
        for file_path, sections in md_sections_by_file.items():
            logger.debug(f"  {file_path}: {len(sections)} sections")
            new_sections.extend(sections)
        logger.debug(f"Extracted {len(new_sections)} total sections from Markdown")
    except FileNotFoundError:
        logger.error(f"Markdown directory not found: {args.new_md_dir}")
        raise
    except Exception as e:
        logger.error(f"Error extracting Markdown: {e}")
        raise

    # Flatten section hierarchies for comparison
    old_flat = flatten_all_sections(old_sections)
    new_flat = flatten_all_sections(new_sections)

    logger.info(f"Total sections - Old: {len(old_flat)}, New: {len(new_flat)}")

    # Step 3: Apply section filter if specified
    if args.section:
        logger.info(f"Filtering sections with pattern: {args.section}")
        old_flat = filter_sections_by_pattern(old_flat, args.section)
        new_flat = filter_sections_by_pattern(new_flat, args.section)
        logger.info(f"After filtering - Old: {len(old_flat)}, New: {len(new_flat)}")

    # Step 4: Align sections between old and new
    logger.info("Aligning sections...")
    alignment_result = aligners.align_sections(old_flat, new_flat)
    logger.debug(f"Created {len(alignment_result.matched)} matched, {len(alignment_result.source_only)} source-only, {len(alignment_result.target_only)} target-only")

    # Step 5: Compare aligned sections and generate findings
    logger.info("Comparing sections...")
    all_findings: List[Finding] = []
    matched_pairs: List[tuple] = []
    source_only: List[Section] = alignment_result.source_only
    target_only: List[Section] = alignment_result.target_only

    # Track which new sections are matched
    matched_new_keys = set()

    # Process matched pairs
    for old_section, new_section in alignment_result.matched:
        matched_new_keys.add(new_section.key)

        # Compare the matched sections
        similarity, findings = comparators.compare_section(
            old_section, new_section
        )

        # Filter findings based on similarity threshold
        if similarity < args.min_similarity:
            for finding in findings:
                all_findings.append(finding)

        matched_pairs.append((old_section, new_section))

        logger.debug(
            f"  Matched: {old_section.key} -> "
            f"{new_section.key} ({similarity:.2%})"
        )

    # Add findings for missing sections (source-only)
    for old_section in source_only:
        finding = Finding(
            category=FindingCategory.CONTENT_MISSING.value,
            severity=Severity.CRITICAL,
            priority=Priority.P0,
            message=f"Section missing from new documentation: {old_section.title}",
            source_location=old_section.key,
            source_content=old_section.title,
            suggestion="Add this section to the new documentation",
        )
        all_findings.append(finding)

        logger.debug(f"  Missing: {old_section.key}")

    # Find extra sections (in new but not in old)
    for section in new_flat:
        if section.key not in matched_new_keys:
            target_only.append(section)

            finding = Finding(
                category=FindingCategory.CONTENT_ADDED.value,
                severity=Severity.INFO,
                priority=Priority.P2,
                message=f"New section added: {section.title}",
                target_location=section.key,
                target_content=section.title,
            )
            all_findings.append(finding)

            logger.debug(f"  Extra: {section.key}")

    # Step 6: Validate links
    logger.info("Validating links...")
    try:
        old_links = validators.extract_all_links(old_flat)
        new_links = validators.extract_all_links(new_flat)
        new_anchor_map = validators.build_anchor_map(new_flat)

        # Build anchor maps for drift detection (anchor_id -> heading_text)
        old_anchor_headings: dict[str, str] = {}
        new_anchor_headings: dict[str, str] = {}
        for section in old_flat:
            if hasattr(section, 'key') and hasattr(section, 'title'):
                old_anchor_headings[section.key] = section.title
        for section in new_flat:
            if hasattr(section, 'key') and hasattr(section, 'title'):
                new_anchor_headings[section.key] = section.title

        # Check for anchor drift
        anchor_findings = validators.check_anchor_drift(old_anchor_headings, new_anchor_headings)
        all_findings.extend(anchor_findings)

        # Validate internal links in new documentation
        link_findings = validators.validate_link_targets(new_links, new_anchor_map)
        all_findings.extend(link_findings)

        logger.debug(f"Link validation: {len(old_links)} old, {len(new_links)} new")
    except Exception as e:
        logger.warning(f"Link validation error: {e}")

    # Step 7: Validate images
    logger.info("Validating images...")
    try:
        old_images = validators.extract_all_images(old_flat)
        new_images = validators.extract_all_images(new_flat)

        # Compare image sets
        image_findings = validators.compare_image_sets(old_images, new_images)
        all_findings.extend(image_findings)

        # Validate image files exist in new documentation
        img_validation_findings = validators.validate_images(
            new_images, args.new_md_dir
        )
        all_findings.extend(img_validation_findings)

        logger.debug(f"Image validation: {len(old_images)} old, {len(new_images)} new")
    except Exception as e:
        logger.warning(f"Image validation error: {e}")

    # Build alignment result
    alignment_result = AlignmentResult(
        matched=matched_pairs,
        source_only=source_only,
        target_only=target_only,
        match_stats={
            "matched": len(matched_pairs),
            "source_only": len(source_only),
            "target_only": len(target_only),
        },
    )

    # Build final result
    result = ComparisonResult(
        source_file=str(Path(args.old_html).resolve()),
        target_file=str(Path(args.new_md_dir).resolve()),
        findings=all_findings,
        alignment=alignment_result,
        metadata={
            "min_similarity": args.min_similarity,
            "section_filter": args.section,
            "base_url_old": args.base_url_old,
            "base_url_new": args.base_url_new,
            "timestamp": timestamp,
        },
    )

    # Calculate match statistics
    total_old = len(matched_pairs) + len(source_only)
    matched_count = len(matched_pairs)

    logger.info("Comparison complete.")
    logger.info(f"  Matched: {matched_count}/{total_old}")
    logger.info(f"  Missing: {len(source_only)}")
    logger.info(f"  Extra: {len(target_only)}")
    logger.info(f"  Findings: {len(all_findings)}")

    return result


def generate_report(result: ComparisonResult, format: str) -> str:
    """Generate a report from comparison results.

    Args:
        result: ComparisonResult to format.
        format: Output format ('markdown' or 'json').

    Returns:
        Formatted report string.
    """
    reporters = _get_reporters()

    if format == "json":
        return reporters.generate_json_report(result)
    else:
        return reporters.generate_markdown_report(result)


def write_output(content: str, output_path: Optional[str]) -> None:
    """Write content to file or stdout.

    Args:
        content: Content to write.
        output_path: Path to output file, or None for stdout.
    """
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Report written to: {output_path}")
    else:
        print(content)


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point for the CLI.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).

    Returns:
        Exit code (0=success, 1=warnings, 2=errors).
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    # Setup logging first
    setup_logging(verbose=args.verbose, quiet=args.quiet)

    # Validate arguments
    errors = validate_args(args)
    if errors:
        for error in errors:
            logger.error(error)
        return 2

    try:
        # Run comparison
        result = run_comparison(args)

        # Generate and write report
        report = generate_report(result, args.format)
        write_output(report, args.out)

        # Determine exit code
        exit_code = result.get_exit_code(strict=args.strict)

        if exit_code == 2:
            logger.warning("Critical findings detected (P0/P1)")
        elif exit_code == 1:
            logger.info("Warnings detected (P2)")
        else:
            logger.info("No significant findings")

        return exit_code

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 2
    except PermissionError as e:
        logger.error(f"Permission denied: {e}")
        return 2
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
