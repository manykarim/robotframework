#!/usr/bin/env python3
"""Convert Robot Framework User Guide RST files to Markdown for MkDocs."""

import os
import re
import shutil
from pathlib import Path

# Source and destination directories
SRC_DIR = Path(__file__).parent.parent.parent / "userguide" / "src"
DOCS_DIR = Path(__file__).parent.parent / "docs"

# Section mapping from RST structure
SECTIONS = {
    "GettingStarted": "getting-started",
    "CreatingTestData": "creating-test-data",
    "ExecutingTestCases": "executing-tests",
    "ExtendingRobotFramework": "extending",
    "SupportingTools": "supporting-tools",
    "Appendices": "appendices",
}

# File ordering within sections (based on master RST includes)
FILE_ORDER = {
    "getting-started": [
        "Introduction.rst",
        "CopyrightAndLicense.rst",
        "Demonstration.rst",
    ],
    "creating-test-data": [
        "TestDataSyntax.rst",
        "CreatingTestCases.rst",
        "CreatingTasks.rst",
        "CreatingTestSuites.rst",
        "UsingTestLibraries.rst",
        "Variables.rst",
        "CreatingUserKeywords.rst",
        "ResourceAndVariableFiles.rst",
        "ControlStructures.rst",
        "AdvancedFeatures.rst",
    ],
    "executing-tests": [
        "BasicUsage.rst",
        "ConfiguringExecution.rst",
        "OutputFiles.rst",
        "PostProcessing.rst",
    ],
    "extending": [
        "CreatingTestLibraries.rst",
        "RemoteLibrary.rst",
        "ListenerInterface.rst",
        "ParserInterface.rst",
    ],
    "supporting-tools": [
        "Libdoc.rst",
        "Testdoc.rst",
        "Tidy.rst",
        "OtherTools.rst",
    ],
    "appendices": [
        "AvailableSettings.rst",
        "CommandLineOptions.rst",
        "Translations.rst",
        "DocumentationFormatting.rst",
        "TimeFormat.rst",
        "BooleanArguments.rst",
        "EvaluatingExpressions.rst",
        "Registrations.rst",
    ],
}


def rst_to_md(content: str, filename: str = "") -> str:
    """Convert RST content to Markdown."""
    lines = content.split('\n')
    result = []
    in_code_block = False
    code_lang = ""
    in_table = False
    table_lines = []
    skip_until_blank = False

    i = 0
    while i < len(lines):
        line = lines[i]

        # Skip RST directives we don't need
        if skip_until_blank:
            if line.strip() == "":
                skip_until_blank = False
            i += 1
            continue

        # Skip includes and other directives
        if line.strip().startswith(".. include::"):
            i += 1
            continue

        if line.strip().startswith(".. contents::"):
            skip_until_blank = True
            i += 1
            continue

        if line.strip().startswith(".. sectnum::"):
            skip_until_blank = True
            i += 1
            continue

        # Handle code blocks
        if line.strip().startswith(".. code::") or line.strip().startswith(".. sourcecode::"):
            match = re.match(r'\.\. (?:code|sourcecode)::\s*(\w+)?', line.strip())
            code_lang = match.group(1) if match and match.group(1) else ""
            result.append(f"```{code_lang}")
            in_code_block = True
            i += 1
            # Skip blank line after directive if present
            if i < len(lines) and lines[i].strip() == "":
                i += 1
            continue

        # Handle literal blocks (::)
        if line.rstrip().endswith("::"):
            result.append(line.rstrip()[:-2] + ":")
            result.append("")
            result.append("```")
            in_code_block = True
            code_lang = ""
            i += 1
            # Skip blank line after ::
            if i < len(lines) and lines[i].strip() == "":
                i += 1
            continue

        # End code block when indentation ends
        if in_code_block:
            if line.strip() == "" and i + 1 < len(lines) and not lines[i + 1].startswith("   "):
                result.append("```")
                result.append("")
                in_code_block = False
            elif line.strip() != "" and not line.startswith("   ") and not line.startswith("\t"):
                result.append("```")
                result.append("")
                in_code_block = False
                # Don't skip this line, process it
                continue
            else:
                # Remove leading indentation (typically 3-4 spaces)
                if line.startswith("    "):
                    result.append(line[4:])
                elif line.startswith("   "):
                    result.append(line[3:])
                else:
                    result.append(line)
                i += 1
                continue

        # Handle RST section headers (underlines)
        if i + 1 < len(lines) and len(lines[i + 1].strip()) > 0:
            next_line = lines[i + 1]
            if set(next_line.strip()) <= {'=', '-', '~', '^', '"', "'", '*', '+'}:
                if len(next_line.strip()) >= len(line.strip()) - 2:
                    # Determine heading level based on character
                    char = next_line.strip()[0]
                    if char == '=':
                        level = 1
                    elif char == '-':
                        level = 2
                    elif char == '~':
                        level = 2
                    elif char == '^':
                        level = 3
                    else:
                        level = 4
                    result.append("")
                    result.append(f"{'#' * level} {line.strip()}")
                    result.append("")
                    i += 2
                    continue

        # Handle overlined headers (line before title that matches)
        if (set(line.strip()) <= {'=', '-', '~', '^'} and
            len(line.strip()) > 3 and
            i + 2 < len(lines)):
            next_line = lines[i + 1]
            after_line = lines[i + 2]
            if (set(after_line.strip()) <= {'=', '-', '~', '^'} and
                line.strip()[0] == after_line.strip()[0]):
                char = line.strip()[0]
                if char == '=':
                    level = 1
                elif char == '~':
                    level = 2
                else:
                    level = 3
                result.append("")
                result.append(f"{'#' * level} {next_line.strip()}")
                result.append("")
                i += 3
                continue

        # Handle RST links: `text <url>`_ or `text`_
        line = re.sub(r'`([^`<]+)\s+<([^>]+)>`_', r'[\1](\2)', line)
        line = re.sub(r'`([^`]+)`_(?!_)', r'[\1](#\1)', line)

        # Handle RST inline literals: ``text`` -> `text`
        line = re.sub(r'``([^`]+)``', r'`\1`', line)

        # Handle RST bold: **text** (same in MD)
        # Handle RST italic: *text* (same in MD)

        # Handle RST roles: :role:`text` -> appropriate MD
        line = re.sub(r':code:`([^`]+)`', r'`\1`', line)
        line = re.sub(r':file:`([^`]+)`', r'`\1`', line)
        line = re.sub(r':ref:`([^`]+)`', r'[\1](#\1)', line)
        line = re.sub(r':doc:`([^`]+)`', r'[\1](\1.md)', line)
        line = re.sub(r':py:(\w+):`([^`]+)`', r'`\2`', line)
        line = re.sub(r':(\w+):`([^`]+)`', r'`\2`', line)  # Generic role handler

        # Handle footnotes: [#name]_ -> [^name]
        line = re.sub(r'\[#(\w+)\]_', r'[^\1]', line)

        # Handle note/warning/tip admonitions
        if line.strip().startswith(".. note::"):
            result.append("")
            result.append("!!! note")
            i += 1
            continue
        if line.strip().startswith(".. warning::"):
            result.append("")
            result.append("!!! warning")
            i += 1
            continue
        if line.strip().startswith(".. tip::"):
            result.append("")
            result.append("!!! tip")
            i += 1
            continue
        if line.strip().startswith(".. important::"):
            result.append("")
            result.append("!!! important")
            i += 1
            continue

        # Handle images
        if line.strip().startswith(".. image::") or line.strip().startswith(".. figure::"):
            match = re.match(r'\.\. (?:image|figure)::\s*(.+)', line.strip())
            if match:
                img_path = match.group(1)
                result.append(f"![{img_path}]({img_path})")
            i += 1
            # Skip image options
            while i < len(lines) and (lines[i].startswith("   :") or lines[i].strip() == ""):
                if lines[i].strip() == "" and i + 1 < len(lines) and not lines[i + 1].startswith("   :"):
                    break
                i += 1
            continue

        # Handle simple tables (basic conversion)
        if line.strip().startswith("+") and "-" in line and "+" in line[1:]:
            # Grid table - convert to simple markdown table
            in_table = True
            table_lines = []
            while i < len(lines) and (lines[i].strip().startswith("+") or lines[i].strip().startswith("|")):
                if lines[i].strip().startswith("|"):
                    table_lines.append(lines[i])
                elif lines[i].strip().startswith("+") and "=" in lines[i]:
                    # Header separator
                    pass
                i += 1
            # Convert table
            if table_lines:
                for j, tl in enumerate(table_lines):
                    cells = [c.strip() for c in tl.split("|")[1:-1]]
                    result.append("| " + " | ".join(cells) + " |")
                    if j == 0:
                        result.append("|" + "|".join(["---"] * len(cells)) + "|")
            result.append("")
            in_table = False
            continue

        # Handle bullet lists
        if line.strip().startswith("- ") or line.strip().startswith("* "):
            # Already valid markdown
            pass

        # Handle numbered lists: #. -> 1.
        line = re.sub(r'^(\s*)#\.\s', r'\g<1>1. ', line)

        # Handle definition lists (term followed by indented definition)
        # These become bold term followed by definition

        result.append(line)
        i += 1

    # Close any unclosed code block
    if in_code_block:
        result.append("```")

    return '\n'.join(result)


def create_index_md():
    """Create the main index.md file."""
    content = """# Robot Framework User Guide

Welcome to the Robot Framework User Guide. This guide covers all aspects of using Robot Framework for test automation.

## Sections

- [Getting Started](getting-started/index.md) - Introduction and installation
- [Creating Test Data](creating-test-data/index.md) - Test syntax, cases, and keywords
- [Executing Tests](executing-tests/index.md) - Running tests and configuration
- [Extending Robot Framework](extending/index.md) - Creating libraries and listeners
- [Supporting Tools](supporting-tools/index.md) - Libdoc, Testdoc, and utilities
- [Appendices](appendices/index.md) - Settings, options, and reference

## About

Robot Framework is a generic open source automation framework for acceptance testing,
acceptance test driven development (ATDD), and robotic process automation (RPA).

- Version: 7.0
- License: Apache License 2.0
- Website: [robotframework.org](https://robotframework.org)
"""
    return content


def create_section_index(section_name: str, files: list) -> str:
    """Create an index.md for a section."""
    titles = {
        "getting-started": "Getting Started",
        "creating-test-data": "Creating Test Data",
        "executing-tests": "Executing Test Cases",
        "extending": "Extending Robot Framework",
        "supporting-tools": "Supporting Tools",
        "appendices": "Appendices",
    }

    title = titles.get(section_name, section_name.replace("-", " ").title())

    lines = [f"# {title}", ""]

    for f in files:
        name = Path(f).stem
        # Convert CamelCase to readable title
        readable = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
        md_name = name.lower().replace(" ", "-") + ".md"
        lines.append(f"- [{readable}]({md_name})")

    return '\n'.join(lines)


def convert_file(src_path: Path, dest_path: Path):
    """Convert a single RST file to Markdown."""
    print(f"Converting: {src_path.name} -> {dest_path.name}")

    with open(src_path, 'r', encoding='utf-8') as f:
        content = f.read()

    md_content = rst_to_md(content, src_path.name)

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(dest_path, 'w', encoding='utf-8') as f:
        f.write(md_content)


def copy_assets(src_section: str, dest_section: str):
    """Copy images and other assets."""
    src_path = SRC_DIR / src_section
    dest_path = DOCS_DIR / dest_section

    for ext in ['*.png', '*.jpg', '*.gif', '*.svg', '*.html']:
        for asset in src_path.glob(ext):
            dest_file = dest_path / asset.name
            print(f"Copying asset: {asset.name}")
            shutil.copy2(asset, dest_file)


def main():
    """Main conversion function."""
    print("Converting Robot Framework User Guide RST to Markdown...")
    print(f"Source: {SRC_DIR}")
    print(f"Destination: {DOCS_DIR}")
    print()

    # Create docs directory
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    # Create main index
    index_path = DOCS_DIR / "index.md"
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(create_index_md())
    print(f"Created: {index_path}")

    # Process each section
    for src_section, dest_section in SECTIONS.items():
        src_path = SRC_DIR / src_section
        dest_path = DOCS_DIR / dest_section
        dest_path.mkdir(parents=True, exist_ok=True)

        print(f"\nProcessing section: {src_section} -> {dest_section}")

        # Get file order for this section
        ordered_files = FILE_ORDER.get(dest_section, [])

        # Convert RST files
        for rst_file in src_path.glob("*.rst"):
            md_name = rst_file.stem.lower().replace(" ", "-") + ".md"
            # Use CamelCase to kebab-case conversion
            md_name = re.sub(r'([a-z])([A-Z])', r'\1-\2', rst_file.stem).lower() + ".md"
            dest_file = dest_path / md_name
            convert_file(rst_file, dest_file)

        # Create section index
        section_files = ordered_files if ordered_files else [f.name for f in src_path.glob("*.rst")]
        index_content = create_section_index(dest_section, section_files)
        with open(dest_path / "index.md", 'w', encoding='utf-8') as f:
            f.write(index_content)

        # Copy assets
        copy_assets(src_section, dest_section)

    print("\n" + "=" * 50)
    print("Conversion complete!")
    print(f"Total markdown files: {len(list(DOCS_DIR.glob('**/*.md')))}")


if __name__ == "__main__":
    main()
