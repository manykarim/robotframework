#!/usr/bin/env python3
"""Fix broken links and references in Robot Framework User Guide.

This script fixes:
1. API reference links like [running.TestSuite](running.TestSuite_)_
2. Underscore-suffixed references like Secret_, pathlib_, ListenerV2_
3. RST-style anonymous link targets like __ [...]
4. Malformed RST backtick links like `text <target_>`__
"""
import re
from pathlib import Path
from typing import Dict, List, Tuple

# API documentation base URLs
API_BASE = "https://robot-framework.readthedocs.io/en/latest/autodoc/"

# Mapping of API references to their full URLs
API_LINKS: Dict[str, str] = {
    # running module
    "running.TestSuite": f"{API_BASE}robot.running.html#robot.running.model.TestSuite",
    "running.TestCase": f"{API_BASE}robot.running.html#robot.running.model.TestCase",
    "running.Keyword": f"{API_BASE}robot.running.html#robot.running.model.Keyword",
    "running.TestLibrary": f"{API_BASE}robot.running.html#robot.running.model.TestLibrary",
    "running.ResourceFile": f"{API_BASE}robot.running.html#robot.running.model.ResourceFile",
    "running.Import": f"{API_BASE}robot.running.html#robot.running.model.Import",
    "running.UserKeyword": f"{API_BASE}robot.running.html#robot.running.model.UserKeyword",
    "running.LibraryKeyword": f"{API_BASE}robot.running.html#robot.running.model.LibraryKeyword",
    "running.InvalidKeyword": f"{API_BASE}robot.running.html#robot.running.model.InvalidKeyword",
    # result module
    "result.TestSuite": f"{API_BASE}robot.result.html#robot.result.model.TestSuite",
    "result.TestCase": f"{API_BASE}robot.result.html#robot.result.model.TestCase",
    "result.Keyword": f"{API_BASE}robot.result.html#robot.result.model.Keyword",
    "result.Message": f"{API_BASE}robot.result.html#robot.result.model.Message",
}

# Internal cross-references with underscore suffix
# Maps reference_name -> (file_path, anchor)
INTERNAL_REFS: Dict[str, Tuple[str, str]] = {
    # Listener interfaces
    "ListenerV2": ("https://robot-framework.readthedocs.io/en/latest/autodoc/robot.api.html#robot.api.interfaces.ListenerV2", None),
    "ListenerV3": ("https://robot-framework.readthedocs.io/en/latest/autodoc/robot.api.html#robot.api.interfaces.ListenerV3", None),
    # Python standard library
    "pathlib": ("https://docs.python.org/3/library/pathlib.html", None),
    "dt-mod": ("https://docs.python.org/3/library/datetime.html#datetime.datetime", None),
    "abc.Set": ("https://docs.python.org/3/library/collections.abc.html#collections.abc.Set", None),
    # Robot Framework types
    "Secret": ("../extending/creating-test-libraries.md", "secret-type"),
    # Internal references (relative to appendices or sections)
    "Translations": ("../appendices/translations.md", None),
    "inline styles": ("../appendices/documentation-formatting.md", "inline-styles"),
    "Simple patterns": ("../executing-tests/configuring-execution.md", "simple-patterns"),
    "Log levels": ("../executing-tests/output-files.md", "log-levels"),
    # Command line related
    "merging outputs": ("../executing-tests/post-processing.md", "merging-outputs"),
    "Console links": ("../executing-tests/output-files.md", "console-links"),
    "Stopping when first test case fails": ("../executing-tests/test-execution.md", "stopping-when-first-test-case-fails"),
    "Stopping on parsing or execution error": ("../executing-tests/test-execution.md", "stopping-on-parsing-or-execution-error"),
    "Automatically logging assigned variable value": ("../creating-test-data/variables.md", "automatically-logging-assigned-variable-value"),
}


def fix_api_links(content: str) -> str:
    """Fix malformed API reference links like [name](name_)_."""
    for name, url in API_LINKS.items():
        # Fix patterns like [name](name_)_ or [text](name_)_
        # Match: [any text](running.TestSuite_)_
        escaped_name = re.escape(name)
        pattern = rf'\[([^\]]+)\]\({escaped_name}_\)_?'
        replacement = rf'[\1]({url})'
        content = re.sub(pattern, replacement, content)

        # Fix RST-style backtick patterns like `text <name_>`__
        pattern = rf'`([^`<]+)\s*<{escaped_name}_>`__'
        replacement = rf'[\1]({url})'
        content = re.sub(pattern, replacement, content)

    return content


def fix_underscore_refs(content: str, current_file: Path) -> str:
    """Fix underscore-suffixed references."""
    for ref_name, (target_path, anchor) in INTERNAL_REFS.items():
        escaped_ref = re.escape(ref_name)

        # Build the full URL
        if target_path.startswith("http"):
            full_url = target_path
        else:
            # It's a relative path
            full_url = target_path
            if anchor:
                full_url += f"#{anchor}"

        # Fix patterns like [text](ref_name_)_
        pattern = rf'\[([^\]]+)\]\({escaped_ref}_\)_?'
        replacement = rf'[\1]({full_url})'
        content = re.sub(pattern, replacement, content)

        # Fix RST-style backtick patterns like `text <ref_name_>`__
        pattern = rf'`([^`<]+)\s*<{escaped_ref}_>`__'
        replacement = rf'[\1]({full_url})'
        content = re.sub(pattern, replacement, content)

        # Fix standalone ref_name_ at word boundaries (more careful matching)
        # Only match when it's clearly a reference, not part of code
        pattern = rf'(?<![`\w]){escaped_ref}_(?![`\w])'
        replacement = f'[{ref_name}]({full_url})'
        content = re.sub(pattern, replacement, content)

    return content


def fix_anonymous_links(content: str) -> str:
    """Remove RST-style anonymous link targets (__ [...])."""
    # These lines are RST link targets that should be removed
    # Pattern: line starting with __ followed by [...] or http
    lines = content.split('\n')
    cleaned_lines = []

    for line in lines:
        stripped = line.strip()
        # Skip RST anonymous link target lines
        if stripped.startswith('__ [') or stripped.startswith('__ http'):
            continue
        # Also remove RST named link targets like .. _name: url
        if stripped.startswith('.. _') and ':' in stripped:
            continue
        cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)


def fix_rst_backtick_links(content: str) -> str:
    """Fix remaining RST-style backtick link patterns."""
    # Pattern: `text <target>`__ or `text <target>`_
    # These should become [text](target)

    # First, handle links to internal anchors like `text <#anchor>`__
    pattern = r'`([^`<]+)\s*<#([^>]+)>`__?_?'
    content = re.sub(pattern, r'[\1](#\2)', content)

    # Handle links to URLs like `text <http...>`__
    pattern = r'`([^`<]+)\s*<(https?://[^>]+)>`__?_?'
    content = re.sub(pattern, r'[\1](\2)', content)

    # Handle links to files like `text <file.md>`__
    pattern = r'`([^`<]+)\s*<([^>]+\.md[^>]*)>`__?_?'
    content = re.sub(pattern, r'[\1](\2)', content)

    return content


def process_file(filepath: Path) -> bool:
    """Process a single markdown file. Returns True if changes were made."""
    content = filepath.read_text(encoding='utf-8')
    original = content

    # Apply all fixes
    content = fix_api_links(content)
    content = fix_underscore_refs(content, filepath)
    content = fix_anonymous_links(content)
    content = fix_rst_backtick_links(content)

    if content != original:
        filepath.write_text(content, encoding='utf-8')
        return True
    return False


def main():
    """Process all markdown files in the docs directory."""
    docs_dir = Path(__file__).parent.parent / "docs"

    if not docs_dir.exists():
        print(f"Error: docs directory not found at {docs_dir}")
        return 1

    md_files = list(docs_dir.rglob("*.md"))
    modified_count = 0

    print(f"Processing {len(md_files)} markdown files...")

    for filepath in md_files:
        if process_file(filepath):
            print(f"  Modified: {filepath.relative_to(docs_dir)}")
            modified_count += 1

    print(f"\nDone. Modified {modified_count} files.")
    return 0


if __name__ == "__main__":
    exit(main())
