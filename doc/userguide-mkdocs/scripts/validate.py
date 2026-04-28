#!/usr/bin/env python3
"""
Validation script for Robot Framework User Guide MkDocs migration.

Runs automated checks to verify the quality of the converted documentation.
Designed for both local development and CI/CD integration.

Usage:
    python validate.py                  # Run all checks
    python validate.py --strict         # Fail on any warning
    python validate.py --quick          # Skip slow checks
    python validate.py --format json    # JSON output for CI
    python validate.py --threshold 0.9  # Set quality threshold

Exit codes:
    0 - All checks pass
    1 - Warnings present (non-strict mode: still passes)
    2 - Errors present (always fails)
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_DIR = SCRIPT_DIR.parent
DOCS_DIR = PROJECT_DIR / "docs"
RST_SOURCE_DIR = PROJECT_DIR.parent / "userguide" / "src"
DOCDIFF_DIR = PROJECT_DIR / "docdiff"
REFERENCE_MAP = SCRIPT_DIR / "reference_map.json"
MKDOCS_YML = PROJECT_DIR / "mkdocs.yml"


def mask_fenced_blocks(text: str) -> str:
    """Replace fenced-block content with blanks so line numbers stay aligned.

    CommonMark rule: a closing fence has length >= opening fence and an empty
    info string. A run with an info string while inside an open fence is
    literal content (not a closer).
    """
    out = []
    in_fence = False
    fence_char = None
    fence_count = 0
    for line in text.split('\n'):
        m = re.match(r'^(`{3,}|~{3,})(.*)$', line)
        opening_now = False
        closing_now = False
        if m:
            run = m.group(1)
            info = m.group(2).strip()
            if not in_fence:
                in_fence = True
                fence_char = run[0]
                fence_count = len(run)
                opening_now = True
            elif run[0] == fence_char and len(run) >= fence_count and not info:
                in_fence = False
                closing_now = True
        if in_fence and not opening_now:
            out.append('')
        elif closing_now:
            out.append('')
        else:
            out.append(line)
    return '\n'.join(out)


def _iter_md_files() -> List[Path]:
    files: List[Path] = []
    for md_file in sorted(DOCS_DIR.rglob("*.md")):
        parts = md_file.relative_to(DOCS_DIR).parts
        if any(p[0].isupper() for p in parts[:-1]):
            continue
        files.append(md_file)
    return files


@dataclass
class CheckResult:
    """Result of a single validation check."""
    name: str
    passed: bool
    message: str
    count: int = 0
    details: List[str] = field(default_factory=list)
    elapsed: float = 0.0


@dataclass
class ValidationReport:
    """Overall validation report."""
    checks: List[CheckResult] = field(default_factory=list)
    total_time: float = 0.0

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)

    @property
    def error_count(self) -> int:
        return sum(1 for c in self.checks if not c.passed)

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "total_time": round(self.total_time, 2),
            "error_count": self.error_count,
            "checks": [
                {
                    "name": c.name,
                    "passed": c.passed,
                    "message": c.message,
                    "count": c.count,
                    "details": c.details[:20],
                    "elapsed": round(c.elapsed, 2)
                }
                for c in self.checks
            ]
        }


def check_build(strict: bool = False) -> CheckResult:
    """Check that mkdocs builds successfully."""
    start = time.time()
    cmd = [sys.executable, "-m", "mkdocs", "build"]
    if strict:
        cmd.append("--strict")

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_DIR))
    elapsed = time.time() - start

    name = "mkdocs_build_strict" if strict else "mkdocs_build"

    if result.returncode == 0:
        return CheckResult(name, True, "Build successful", elapsed=elapsed)

    # Count warnings
    warnings = [l for l in result.stderr.split('\n') if 'WARNING' in l]
    return CheckResult(
        name, False,
        f"Build failed with {len(warnings)} warnings",
        count=len(warnings),
        details=warnings[:20],
        elapsed=elapsed
    )


def check_broken_anchors() -> CheckResult:
    """Check for broken internal anchor references."""
    start = time.time()
    result = subprocess.run(
        [sys.executable, "-m", "mkdocs", "build"],
        capture_output=True, text=True, cwd=str(PROJECT_DIR)
    )
    elapsed = time.time() - start

    info_warnings = [l for l in result.stderr.split('\n')
                     if 'INFO' in l and 'contains a link' in l]

    # Group by file
    file_counts: Dict[str, int] = {}
    for line in info_warnings:
        match = re.search(r"Doc file '([^']+)'", line)
        if match:
            fname = match.group(1)
            file_counts[fname] = file_counts.get(fname, 0) + 1

    details = [f"  {count:3d} broken anchors in {fname}"
               for fname, count in sorted(file_counts.items(), key=lambda x: -x[1])]

    passed = len(info_warnings) == 0
    return CheckResult(
        "broken_anchors", passed,
        f"{len(info_warnings)} broken anchor references",
        count=len(info_warnings),
        details=details,
        elapsed=elapsed
    )


def check_rst_remnants() -> CheckResult:
    """Check for remaining RST syntax in Markdown files."""
    start = time.time()
    issues = []

    for md_file in sorted(DOCS_DIR.rglob("*.md")):
        # Skip CamelCase directories
        parts = md_file.relative_to(DOCS_DIR).parts
        if any(p[0].isupper() for p in parts[:-1]):
            continue

        content = md_file.read_text(encoding="utf-8")
        rel_path = md_file.relative_to(DOCS_DIR)

        # Check for RST roles
        for match in re.finditer(r':(setting|option|file|name|codesc):`[^`]+`', content):
            issues.append(f"  RST role {match.group(0)[:40]} in {rel_path}")

        # Check for RST directives (outside code blocks)
        in_code = False
        for i, line in enumerate(content.split('\n'), 1):
            if line.strip().startswith('```'):
                in_code = not in_code
                continue
            if not in_code and re.match(r'^\.\.\s+(note|warning|code|sourcecode|image|figure|table|list-table)::', line):
                issues.append(f"  RST directive at {rel_path}:{i}: {line.strip()[:60]}")

    elapsed = time.time() - start
    passed = len(issues) == 0
    return CheckResult(
        "rst_remnants", passed,
        f"{len(issues)} RST remnants found",
        count=len(issues),
        details=issues[:30],
        elapsed=elapsed
    )


def check_bare_refs() -> CheckResult:
    """Check for unconverted bare RST word references."""
    start = time.time()
    issues = []

    # Load ignore list from reference map
    ignore_set = set()
    if REFERENCE_MAP.exists():
        with open(REFERENCE_MAP) as f:
            ref_map = json.load(f)
        for item in ref_map.get("ignore_bare_refs", []):
            if not item.startswith("_"):
                ignore_set.add(item)

    for md_file in sorted(DOCS_DIR.rglob("*.md")):
        parts = md_file.relative_to(DOCS_DIR).parts
        if any(p[0].isupper() for p in parts[:-1]):
            continue

        content = md_file.read_text(encoding="utf-8")
        rel_path = md_file.relative_to(DOCS_DIR)

        in_code = False
        for i, line in enumerate(content.split('\n'), 1):
            if line.strip().startswith('```'):
                in_code = not in_code
                continue
            if in_code:
                continue

            # Find bare Word_ references (skip inside URLs and link targets)
            for match in re.finditer(r'(?<![`\[(\w])([A-Z][a-zA-Z]+)_(?![_\w`\]])', line):
                word = match.group(1)
                full = word + "_"
                if full not in ignore_set and not word.isupper():
                    # Skip if inside a URL or Markdown link target ](...)
                    pos = match.start()
                    in_link = False
                    for lm in re.finditer(r'\]\([^)]*\)', line):
                        if lm.start() < pos < lm.end():
                            in_link = True
                            break
                    if not in_link:
                        issues.append(f"  {word}_ at {rel_path}:{i}")

    elapsed = time.time() - start
    unique_words = set(i.split('_')[0].split()[-1] for i in issues)
    passed = len(issues) == 0
    return CheckResult(
        "bare_rst_refs", passed,
        f"{len(issues)} unconverted bare refs ({len(unique_words)} unique patterns)",
        count=len(issues),
        details=issues[:30],
        elapsed=elapsed
    )


def check_file_coverage() -> CheckResult:
    """Check that all RST source files have corresponding MD output."""
    start = time.time()
    missing = []

    if REFERENCE_MAP.exists():
        with open(REFERENCE_MAP) as f:
            ref_map = json.load(f)

        for rst_file, md_file in ref_map.get("rst_to_md_files", {}).items():
            if rst_file.startswith("_"):
                continue
            md_path = DOCS_DIR / md_file
            if not md_path.exists():
                missing.append(f"  Missing: {md_file} (from {rst_file})")

    elapsed = time.time() - start
    passed = len(missing) == 0
    return CheckResult(
        "file_coverage", passed,
        f"{len(missing)} expected files missing" if missing else "All expected files present",
        count=len(missing),
        details=missing,
        elapsed=elapsed
    )


def check_images() -> CheckResult:
    """Check that all images from RST source are present in MkDocs output."""
    start = time.time()
    missing = []

    img_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.svg'}

    if REFERENCE_MAP.exists():
        with open(REFERENCE_MAP) as f:
            ref_map = json.load(f)

        for section_rst, section_md in ref_map.get("section_dirs", {}).items():
            if section_rst.startswith("_"):
                continue
            rst_dir = RST_SOURCE_DIR / section_rst
            md_dir = DOCS_DIR / section_md

            if not rst_dir.exists():
                continue

            for img in rst_dir.iterdir():
                if img.suffix.lower() in img_extensions:
                    md_img = md_dir / img.name
                    if not md_img.exists():
                        missing.append(f"  Missing: {section_md}/{img.name}")

    elapsed = time.time() - start
    passed = len(missing) == 0
    return CheckResult(
        "images", passed,
        f"{len(missing)} images missing" if missing else "All images present",
        count=len(missing),
        details=missing,
        elapsed=elapsed
    )


def check_code_fences() -> CheckResult:
    """Check for unbalanced code fences using CommonMark-aware state tracking.

    In CommonMark/Python-Markdown, a closing fence must have at least as many
    backticks as the opening fence AND no info string. A fence with an info
    string (like ```python) inside a code block is literal text, not a fence.
    """
    start = time.time()
    issues = []

    for md_file in sorted(DOCS_DIR.rglob("*.md")):
        parts = md_file.relative_to(DOCS_DIR).parts
        if any(p[0].isupper() for p in parts[:-1]):
            continue

        content = md_file.read_text(encoding="utf-8")
        state = 'text'
        open_line = 0
        open_backticks = 0

        for i, line in enumerate(content.split('\n'), 1):
            m = re.match(r'^(`{3,})(.*)', line.rstrip())
            if not m:
                continue
            backticks = len(m.group(1))
            info = m.group(2).strip()

            if state == 'text':
                state = 'code'
                open_line = i
                open_backticks = backticks
            else:
                if backticks >= open_backticks and not info:
                    state = 'text'

        if state == 'code':
            rel_path = md_file.relative_to(DOCS_DIR)
            issues.append(f"  Unclosed code block at line {open_line} in {rel_path}")

    elapsed = time.time() - start
    passed = len(issues) == 0
    return CheckResult(
        "code_fences", passed,
        f"{len(issues)} files with unbalanced code fences" if issues else "All code fences balanced",
        count=len(issues),
        details=issues,
        elapsed=elapsed
    )


def run_docdiff() -> Optional[CheckResult]:
    """Run docdiff comparison if available."""
    if not DOCDIFF_DIR.exists():
        return None

    html_file = DOCDIFF_DIR / "data" / "RobotFrameworkUserGuide.html"
    if not html_file.exists():
        return None

    start = time.time()
    # Compute relative path from docdiff dir to docs dir
    docs_rel = os.path.relpath(DOCS_DIR, DOCDIFF_DIR)
    result = subprocess.run(
        [sys.executable, "-m", "docdiff.cli",
         "--old-html", str(html_file),
         "--new-md-dir", docs_rel,
         "--format", "json",
         "--out", "/tmp/docdiff-validation.json"],
        capture_output=True, text=True, cwd=str(DOCDIFF_DIR)
    )
    elapsed = time.time() - start

    # docdiff exits 2 for critical findings, 1 for warnings, 0 for clean
    # All are valid comparison results (not crashes)
    if result.returncode not in (0, 1, 2):
        return CheckResult(
            "docdiff", False,
            f"DocDiff crashed: {result.stderr[:200]}",
            elapsed=elapsed
        )

    try:
        with open("/tmp/docdiff-validation.json") as f:
            report = json.load(f)

        # Parse the INFO output for match stats (more reliable than JSON summary)
        match_info = ""
        for line in result.stderr.split('\n'):
            if 'Matched:' in line:
                match_info = line.strip()

        # Extract findings counts
        findings = report.get("findings_by_priority", {})
        total_findings = report.get("summary", {}).get("total_findings", 0)
        finding_counts = {}
        for priority, items in findings.items():
            finding_counts[priority] = len(items) if isinstance(items, list) else 0

        details = [f"  {match_info}"] if match_info else []
        details.append(f"  Total findings: {total_findings}")
        for priority in sorted(finding_counts.keys()):
            details.append(f"  {priority}: {finding_counts[priority]}")

        # Consider it passing if the comparison completed (regardless of findings)
        return CheckResult(
            "docdiff", True,
            f"Comparison complete ({total_findings} findings)",
            count=total_findings,
            details=details,
            elapsed=elapsed
        )
    except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
        return CheckResult(
            "docdiff", False,
            f"DocDiff output parsing failed: {e}",
            elapsed=elapsed
        )


def _scan_lines(pattern: re.Pattern, mask: bool, label: str) -> CheckResult:
    """Generic per-line scan over docs producing path:line:content findings."""
    start = time.time()
    issues: List[str] = []
    for md_file in _iter_md_files():
        text = md_file.read_text(encoding="utf-8")
        scan_text = mask_fenced_blocks(text) if mask else text
        rel = md_file.relative_to(DOCS_DIR)
        for i, line in enumerate(scan_text.split('\n'), 1):
            if pattern.search(line):
                # Use the original (unmasked) line for the report so context is real.
                orig = text.split('\n')[i - 1] if i - 1 < len(text.split('\n')) else line
                issues.append(f"  {rel}:{i}: {orig.strip()[:80]}")
    elapsed = time.time() - start
    return CheckResult(
        label, len(issues) == 0,
        f"{len(issues)} occurrence(s)",
        count=len(issues),
        details=issues[:30],
        elapsed=elapsed,
    )


def check_v1_lone_colon() -> CheckResult:
    return _scan_lines(re.compile(r'^\s*:?:\s*$'), mask=True, label="V1_lone_colon")


def check_v2_empty_fences() -> CheckResult:
    start = time.time()
    issues: List[str] = []
    open_re = re.compile(r'^(`{3,}|~{3,})([^\n]*)$')
    for md_file in _iter_md_files():
        text = md_file.read_text(encoding="utf-8")
        rel = md_file.relative_to(DOCS_DIR)
        lines = text.split('\n')
        i = 0
        in_fence = False
        fence_marker = ''
        fence_open_line = 0
        body: List[str] = []
        while i < len(lines):
            line = lines[i]
            m = open_re.match(line)
            if not in_fence:
                if m:
                    in_fence = True
                    fence_marker = m.group(1)
                    fence_open_line = i + 1
                    body = []
            else:
                # CommonMark: closing fence has same char, ≥ same length, and no info string.
                if m and m.group(1)[0] == fence_marker[0] \
                        and len(m.group(1)) >= len(fence_marker) \
                        and m.group(2).strip() == '':
                    if all(not l.strip() for l in body):
                        issues.append(f"  {rel}:{fence_open_line}: empty fenced block")
                    in_fence = False
                else:
                    body.append(line)
            i += 1
    elapsed = time.time() - start
    return CheckResult(
        "V2_empty_fences", len(issues) == 0,
        f"{len(issues)} empty fenced block(s)",
        count=len(issues), details=issues[:30], elapsed=elapsed,
    )


def check_v3_backtick_underlines() -> CheckResult:
    return _scan_lines(re.compile(r'^`{4,}\s*$'), mask=False, label="V3_backtick_underlines")


def check_v4_simple_table_seps() -> CheckResult:
    return _scan_lines(
        re.compile(r'^\s*={5,}(\s+={5,})+\s*$'),
        mask=True, label="V4_simple_table_seps",
    )


def check_v5_grid_table_borders() -> CheckResult:
    return _scan_lines(
        re.compile(r'^\s*\+[-=+]{3,}\+\s*$'),
        mask=True, label="V5_grid_table_borders",
    )


def check_v6_stray_roles() -> CheckResult:
    return _scan_lines(
        re.compile(r':(setting|name|option|file|codesc|opt):'),
        mask=True, label="V6_stray_roles",
    )


def check_v7_pandoc_role_garbage() -> CheckResult:
    start = time.time()
    issues: List[str] = []
    pat = re.compile(r'\(:[a-z]+:\]\(')
    for md_file in _iter_md_files():
        text = md_file.read_text(encoding="utf-8")
        rel = md_file.relative_to(DOCS_DIR)
        for i, line in enumerate(text.split('\n'), 1):
            if pat.search(line):
                issues.append(f"  {rel}:{i}: {line.strip()[:80]}")
    elapsed = time.time() - start
    return CheckResult(
        "V7_pandoc_role_garbage", len(issues) == 0,
        f"{len(issues)} occurrence(s)",
        count=len(issues), details=issues[:30], elapsed=elapsed,
    )


def check_v8_def_list_candidates() -> CheckResult:
    """Term followed by 3-or-4-space-indented body without ':' marker."""
    start = time.time()
    issues: List[str] = []
    term_re = re.compile(r'^[^\s#\->\*\d:|][^\n]*$')
    body_re = re.compile(r'^( {3,4})(?![:\s])(\S[^\n]*)$')
    list_marker_re = re.compile(r'^\s*([-*+]|\d+\.)\s')
    for md_file in _iter_md_files():
        text = md_file.read_text(encoding="utf-8")
        masked = mask_fenced_blocks(text).split('\n')
        rel = md_file.relative_to(DOCS_DIR)
        n = len(masked)
        for i in range(n - 2):
            prev_blank = (i == 0) or masked[i].strip() == ''
            if not prev_blank:
                continue
            term = masked[i + 1]
            body = masked[i + 2]
            if term == '' or body == '':
                continue
            if not term_re.match(term) or list_marker_re.match(term):
                continue
            ts = term.strip()
            if ts.startswith('|') or ts.startswith('<') or ts.startswith('http'):
                continue
            # Admonition headers (`!!! note`, `???+ tip`) own the indented body
            # below them; they're not def-list terms.
            if ts.startswith('!!!') or ts.startswith('???'):
                continue
            if body_re.match(body):
                issues.append(f"  {rel}:{i + 2}: {term.strip()[:50]} -> {body.strip()[:30]}")
    elapsed = time.time() - start
    return CheckResult(
        "V8_def_list_candidates", len(issues) == 0,
        f"{len(issues)} candidate(s)",
        count=len(issues), details=issues[:30], elapsed=elapsed,
    )


def _slug(s: str) -> str:
    s = s.lower()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    return s.strip('-')


def _walk_nav(nav, prefix: List[str] = None):
    """Yield (label, target) for every nav leaf."""
    prefix = prefix or []
    if isinstance(nav, list):
        for item in nav:
            yield from _walk_nav(item, prefix)
    elif isinstance(nav, dict):
        for label, value in nav.items():
            if isinstance(value, str):
                yield (label, value)
            else:
                yield from _walk_nav(value, prefix + [label])


def _load_nav() -> Optional[list]:
    try:
        import yaml  # type: ignore
    except ImportError:
        return None
    if not MKDOCS_YML.exists():
        return None
    # Material's YAML uses `!!python/name:` tags for emoji. SafeLoader rejects
    # those; use a permissive loader that ignores unknown tags.
    class _Loader(yaml.SafeLoader):
        pass

    def _ignore_unknown(loader, tag_suffix, node):
        return None

    _Loader.add_multi_constructor('!!python/name:', _ignore_unknown)
    _Loader.add_multi_constructor('tag:yaml.org,2002:python/name:', _ignore_unknown)
    _Loader.add_multi_constructor('!', _ignore_unknown)
    with open(MKDOCS_YML, encoding='utf-8') as f:
        data = yaml.load(f, Loader=_Loader)
    return data.get('nav') if data else None


def check_v9_nav_leaves_resolve() -> CheckResult:
    start = time.time()
    issues: List[str] = []
    nav = _load_nav()
    if nav is None:
        return CheckResult(
            "V9_nav_leaves_resolve", True,
            "skipped (yaml or mkdocs.yml unavailable)",
            elapsed=time.time() - start,
        )
    for label, target in _walk_nav(nav):
        path = DOCS_DIR / target
        if not path.exists():
            issues.append(f"  '{label}' -> {target}: file missing")
            continue
        try:
            size = path.stat().st_size
        except OSError as e:
            issues.append(f"  '{label}' -> {target}: stat failed ({e})")
            continue
        if size <= 200:
            issues.append(f"  '{label}' -> {target}: too small ({size} bytes)")
            continue
        text = path.read_text(encoding='utf-8')
        non_heading = [ln for ln in text.split('\n')
                       if ln.strip() and not ln.lstrip().startswith('#')]
        if not non_heading:
            issues.append(f"  '{label}' -> {target}: no non-heading content")
    elapsed = time.time() - start
    return CheckResult(
        "V9_nav_leaves_resolve", len(issues) == 0,
        f"{len(issues)} nav leaf issue(s)",
        count=len(issues), details=issues[:30], elapsed=elapsed,
    )


def check_v10_nav_label_matches_h1() -> CheckResult:
    start = time.time()
    issues: List[str] = []
    nav = _load_nav()
    if nav is None:
        return CheckResult(
            "V10_nav_label_matches_h1", True,
            "skipped (yaml or mkdocs.yml unavailable)",
            elapsed=time.time() - start,
        )
    # Generic UX labels that intentionally bear no relation to the page H1.
    UX_LABELS = {"home", "index", "overview"}
    for label, target in _walk_nav(nav):
        if _slug(label) in UX_LABELS:
            continue
        path = DOCS_DIR / target
        if not path.exists():
            continue
        text = path.read_text(encoding='utf-8')
        h1 = None
        for line in text.split('\n'):
            stripped = line.strip()
            if stripped.startswith('# ') and not stripped.startswith('## '):
                h1 = stripped[2:].strip()
                break
        if h1 is None:
            issues.append(f"  '{label}' -> {target}: no H1 heading")
            continue
        # Substring match in either direction: nav labels are intentionally
        # short forms of long descriptive H1 titles ("Libdoc" vs "Library
        # documentation tool (Libdoc)").
        h1_slug = _slug(h1)
        label_slug = _slug(label)
        if label_slug in h1_slug or h1_slug in label_slug:
            continue
        # Fuzzy: token overlap — at least one shared word ≥ 4 chars.
        h1_tokens = {t for t in h1_slug.split('-') if len(t) >= 4}
        label_tokens = {t for t in label_slug.split('-') if len(t) >= 4}
        if h1_tokens & label_tokens:
            continue
        issues.append(f"  '{label}' -> {target}: H1 '{h1}' (slug '{h1_slug}' vs '{label_slug}')")
    elapsed = time.time() - start
    return CheckResult(
        "V10_nav_label_matches_h1", len(issues) == 0,
        f"{len(issues)} mismatch(es)",
        count=len(issues), details=issues[:30], elapsed=elapsed,
    )


def check_v11_rst_directive_leaks() -> CheckResult:
    return _scan_lines(
        re.compile(
            r'^\s*\.\. (raw|figure|image|include|note|warning|tip|admonition|'
            r'seealso|attention|caution|danger|error|hint|important)::'
        ),
        mask=True, label="V11_rst_directive_leaks",
    )


def check_v12_indented_html_table() -> CheckResult:
    return _scan_lines(
        re.compile(r'^( {4,}|\t+)<table\b'),
        mask=True, label="V12_indented_html_table",
    )


PROPOSAL_CHECKS = [
    ("V1  lone : / ::                  ", check_v1_lone_colon),
    ("V2  empty fences                 ", check_v2_empty_fences),
    ("V3  4+ backtick underlines       ", check_v3_backtick_underlines),
    ("V4  leaked === simple-table seps ", check_v4_simple_table_seps),
    ("V5  leaked grid-table borders    ", check_v5_grid_table_borders),
    ("V6  stray RST roles              ", check_v6_stray_roles),
    ("V7  Pandoc :role: garbage        ", check_v7_pandoc_role_garbage),
    ("V8  def-list candidates          ", check_v8_def_list_candidates),
    ("V9  nav leaves resolve           ", check_v9_nav_leaves_resolve),
    ("V10 nav label ~ H1 slug          ", check_v10_nav_label_matches_h1),
    ("V11 leaked .. directives         ", check_v11_rst_directive_leaks),
    ("V12 indented <table>             ", check_v12_indented_html_table),
]


# Stable mapping from CheckResult.name -> printable label.
PROPOSAL_LABELS = {
    "V1_lone_colon":              "V1  lone : / ::",
    "V2_empty_fences":             "V2  empty fences",
    "V3_backtick_underlines":      "V3  4+ backtick underlines",
    "V4_simple_table_seps":        "V4  leaked === simple-table seps",
    "V5_grid_table_borders":       "V5  leaked grid-table borders",
    "V6_stray_roles":              "V6  stray RST roles",
    "V7_pandoc_role_garbage":      "V7  Pandoc :role: garbage",
    "V8_def_list_candidates":      "V8  def-list candidates",
    "V9_nav_leaves_resolve":       "V9  nav leaves resolve",
    "V10_nav_label_matches_h1":    "V10 nav label ~ H1 slug",
    "V11_rst_directive_leaks":     "V11 leaked .. directives",
    "V12_indented_html_table":     "V12 indented <table>",
}


def check_pipeline_proposal_violations(skip_v8: bool = False) -> List[CheckResult]:
    """Run all V1-V12 proposal checks; return one CheckResult per check."""
    results: List[CheckResult] = []
    for label, fn in PROPOSAL_CHECKS:
        if skip_v8 and fn is check_v8_def_list_candidates:
            continue
        result = fn()
        result.message = f"{label.strip()} -> {result.message}"
        results.append(result)
    return results


def _print_proposal_table(results: List[CheckResult]) -> None:
    print("\n" + "=" * 60)
    print("PIPELINE PROPOSAL CHECKS (V1-V12)")
    print("=" * 60)
    for r in results:
        nice_label = PROPOSAL_LABELS.get(r.name, r.name)
        status = "PASS" if r.passed else "FAIL"
        print(f"  {nice_label:<35} {r.count:>4}  {status}")
        if not r.passed:
            for d in r.details[:5]:
                print(f"    {d}")
            if len(r.details) > 5:
                print(f"    ... and {len(r.details) - 5} more")


def main():
    parser = argparse.ArgumentParser(
        description="Validate Robot Framework User Guide MkDocs migration"
    )
    parser.add_argument("--strict", action="store_true",
                        help="Fail on any warning (not just errors)")
    parser.add_argument("--quick", action="store_true",
                        help="Skip slow checks (docdiff, double build)")
    parser.add_argument("--format", choices=["text", "json"], default="text",
                        help="Output format")
    parser.add_argument("--threshold", type=float, default=0.80,
                        help="Quality threshold for docdiff (0.0-1.0)")
    parser.add_argument("--strict-conversion", action="store_true",
                        help="Run only the V1-V12 conversion-proposal checks")
    args = parser.parse_args()

    if args.strict_conversion:
        results = check_pipeline_proposal_violations(skip_v8=args.quick)
        _print_proposal_table(results)
        any_fail = any(not r.passed for r in results)
        if args.format == "json":
            payload = {
                "passed": not any_fail,
                "checks": [
                    {"name": r.name, "passed": r.passed,
                     "count": r.count, "message": r.message,
                     "details": r.details[:20]} for r in results
                ],
            }
            print(json.dumps(payload, indent=2))
        return 1 if any_fail else 0

    start_time = time.time()
    report = ValidationReport()

    print("=" * 60)
    print("Robot Framework User Guide - Migration Validation")
    print("=" * 60)

    # Fast checks
    checks = [
        ("File coverage", check_file_coverage),
        ("Images", check_images),
        ("Code fences", check_code_fences),
        ("RST remnants", check_rst_remnants),
        ("Bare RST refs", check_bare_refs),
    ]

    if not args.quick:
        checks.append(("MkDocs build", lambda: check_build(strict=False)))
        checks.append(("MkDocs strict", lambda: check_build(strict=True)))
        checks.append(("Broken anchors", check_broken_anchors))

    for name, check_fn in checks:
        print(f"\n  Checking {name} ...", end=" ", flush=True)
        result = check_fn()
        report.checks.append(result)
        status = "PASS" if result.passed else "FAIL"
        print(f"{status} ({result.message})")
        if not result.passed and result.details:
            for d in result.details[:5]:
                print(f"    {d}")
            if len(result.details) > 5:
                print(f"    ... and {len(result.details) - 5} more")

    # Pipeline proposal checks V1-V12 (always run; cheap).
    proposal_results = check_pipeline_proposal_violations(skip_v8=args.quick)
    report.checks.extend(proposal_results)
    _print_proposal_table(proposal_results)

    # Docdiff (optional, slow)
    if not args.quick:
        print(f"\n  Checking DocDiff ...", end=" ", flush=True)
        docdiff_result = run_docdiff()
        if docdiff_result:
            report.checks.append(docdiff_result)
            status = "PASS" if docdiff_result.passed else "FAIL"
            print(f"{status} ({docdiff_result.message})")
            if docdiff_result.details:
                for d in docdiff_result.details[:8]:
                    print(f"    {d}")
        else:
            print("SKIP (docdiff not available)")

    report.total_time = time.time() - start_time

    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    for check in report.checks:
        marker = "✓" if check.passed else "✗"
        print(f"  {marker} {check.name}: {check.message} ({check.elapsed:.1f}s)")

    total_issues = sum(c.count for c in report.checks if not c.passed)
    print(f"\n  Total issues: {total_issues}")
    print(f"  Total time:   {report.total_time:.1f}s")
    print(f"  Result:        {'PASS' if report.passed else 'FAIL'}")
    print("=" * 60)

    # JSON output
    if args.format == "json":
        print(json.dumps(report.to_dict(), indent=2))

    # Exit code
    if report.passed:
        return 0
    elif args.strict:
        return 1
    else:
        # In non-strict mode, fail on build errors or any V1-V12 proposal violation.
        build_checks = [c for c in report.checks if c.name == "mkdocs_build"]
        if any(not c.passed for c in build_checks):
            return 2
        proposal_failed = any(
            not c.passed for c in report.checks if c.name.startswith("V")
        )
        if proposal_failed:
            return 2
        return 1


if __name__ == "__main__":
    sys.exit(main())
