#!/usr/bin/env python3
"""
convert_rst.py - Convert reST files to MkDocs-compatible Markdown

This script converts Robot Framework User Guide reST files to Markdown format
compatible with Material for MkDocs. It handles custom roles, admonitions,
code blocks, and cross-references.

Usage:
    python convert_rst.py input.rst output.md [--anchor-map anchors.json]
    python convert_rst.py --batch input_dir/ output_dir/

Requirements:
    - pandoc (system install)
    - Python 3.8+
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional


def convert_custom_roles(content: str) -> str:
    """Convert Robot Framework User Guide custom roles to Markdown.

    Custom roles defined in roles.rst:
    - :setting:`value` -> *value* (italic, for setting names)
    - :option:`value` -> `value` (inline code, for CLI options)
    - :file:`path` -> *path* (italic, for file paths)
    - :name:`value` -> *value* (italic, for test/keyword names)
    - :codesc:`value` -> `value` (inline code with escape support)
    """
    # :setting:`value` -> *value* (italic)
    content = re.sub(r':setting:`([^`]+)`', r'*\1*', content)

    # :option:`value` -> `value` (inline code)
    content = re.sub(r':option:`([^`]+)`', r'`\1`', content)

    # :file:`path` -> *path* (italic)
    content = re.sub(r':file:`([^`]+)`', r'*\1*', content)

    # :name:`value` -> *value* (italic)
    content = re.sub(r':name:`([^`]+)`', r'*\1*', content)

    # :codesc:`value` -> `value` (handles escaped backticks)
    content = re.sub(r':codesc:`([^`]+)`', r'`\1`', content)

    # Clean up any remaining role-like patterns from Pandoc output
    # e.g., <span class="setting">value</span> -> *value*
    content = re.sub(r'<span class="setting">([^<]+)</span>', r'*\1*', content)
    content = re.sub(r'<span class="option">([^<]+)</span>', r'`\1`', content)
    content = re.sub(r'<span class="file">([^<]+)</span>', r'*\1*', content)
    content = re.sub(r'<span class="name">([^<]+)</span>', r'*\1*', content)
    content = re.sub(r'<span class="codesc">([^<]+)</span>', r'`\1`', content)

    return content


def convert_admonitions(content: str) -> str:
    """Convert reST admonitions to MkDocs format.

    reST format: .. note::
                    content

    MkDocs format: !!! note
                       content
    """
    admonition_types = [
        'note', 'warning', 'tip', 'important',
        'caution', 'danger', 'attention', 'hint'
    ]

    for adm_type in admonition_types:
        # Pattern matches: .. type::\n   indented content
        pattern = rf'\.\.\s+{adm_type}::\s*\n((?:\s+.+\n?)+)'

        def replacement(match):
            content_lines = match.group(1)
            # Find minimum indentation and dedent
            lines = content_lines.split('\n')
            non_empty_lines = [l for l in lines if l.strip()]
            if non_empty_lines:
                min_indent = min(len(l) - len(l.lstrip()) for l in non_empty_lines)
            else:
                min_indent = 0

            # Dedent and re-indent with 4 spaces for MkDocs
            dedented_lines = []
            for line in lines:
                if line.strip():
                    dedented = line[min_indent:] if len(line) > min_indent else line.lstrip()
                    dedented_lines.append(f'    {dedented}')
                elif line:
                    dedented_lines.append('')

            dedented_content = '\n'.join(dedented_lines).rstrip()
            return f'!!! {adm_type}\n{dedented_content}\n'

        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)

    return content


def convert_code_blocks(content: str) -> str:
    """Ensure code blocks have proper language identifiers.

    Convert common language names to MkDocs-compatible identifiers.
    """
    # robotframework -> robot
    content = re.sub(r'```robotframework\b', '```robot', content)

    # sourcecode blocks from Pandoc
    content = re.sub(r'``` \{\.robotframework\}', '```robot', content)
    content = re.sub(r'``` \{\.python\}', '```python', content)
    content = re.sub(r'``` \{\.bash\}', '```bash', content)
    content = re.sub(r'``` \{\.console\}', '```console', content)

    return content


def add_legacy_anchors(content: str, anchor_map: dict) -> str:
    """Add HTML anchor aliases for legacy URL compatibility.

    This preserves backward compatibility with external links that
    reference the original single-page documentation anchors.
    """
    for old_anchor, heading in anchor_map.items():
        # Find the heading and add anchor before it
        # Match various heading levels
        pattern = rf'(^#{1,6}\s+{re.escape(heading)})'
        replacement = f'<a id="{old_anchor}"></a>\n\n\\1'
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

    return content


def fix_internal_links(content: str) -> str:
    """Fix internal cross-references to use correct paths.

    Convert reST-style references to Markdown links.
    """
    # Remove reference markers like :ref:`label`
    content = re.sub(r':ref:`([^`]+)`', r'[\1](#\1)', content)

    # Clean up any remaining reST link targets
    content = re.sub(r'\.\.\s+_[\w-]+:', '', content)

    return content


def clean_formatting(content: str) -> str:
    """Clean up various formatting issues from Pandoc output."""
    # Remove excessive blank lines (more than 2 consecutive)
    content = re.sub(r'\n{4,}', '\n\n\n', content)

    # Fix table alignment issues
    # Pandoc sometimes creates tables with inconsistent column widths

    # Remove trailing whitespace
    content = re.sub(r'[ \t]+$', '', content, flags=re.MULTILINE)

    # Ensure file ends with single newline
    content = content.rstrip() + '\n'

    return content


def run_pandoc(input_path: Path, output_path: Path) -> bool:
    """Run Pandoc to convert reST to Markdown."""
    try:
        cmd = [
            'pandoc',
            '-f', 'rst',
            '-t', 'gfm+pipe_tables',
            '--wrap=none',
            '-o', str(output_path),
            str(input_path)
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f'Pandoc error: {e.stderr}', file=sys.stderr)
        return False
    except FileNotFoundError:
        print('Error: pandoc not found. Please install pandoc.', file=sys.stderr)
        return False


def convert_file(
    input_path: Path,
    output_path: Path,
    anchor_map: Optional[dict] = None
) -> bool:
    """Convert a single reST file to Markdown."""

    # Step 1: Run Pandoc for initial conversion
    temp_path = output_path.with_suffix('.tmp.md')
    if not run_pandoc(input_path, temp_path):
        return False

    # Step 2: Read Pandoc output
    content = temp_path.read_text(encoding='utf-8')

    # Step 3: Apply post-processing
    content = convert_custom_roles(content)
    content = convert_admonitions(content)
    content = convert_code_blocks(content)
    content = fix_internal_links(content)

    if anchor_map:
        content = add_legacy_anchors(content, anchor_map)

    content = clean_formatting(content)

    # Step 4: Write final output
    output_path.write_text(content, encoding='utf-8')

    # Clean up temp file
    temp_path.unlink()

    print(f'Converted: {input_path} -> {output_path}')
    return True


def batch_convert(input_dir: Path, output_dir: Path, anchor_map: Optional[dict] = None):
    """Convert all reST files in a directory."""
    output_dir.mkdir(parents=True, exist_ok=True)

    success_count = 0
    fail_count = 0

    for rst_file in input_dir.glob('**/*.rst'):
        # Skip special files
        if rst_file.name in ('roles.rst', 'version.rst'):
            continue

        # Calculate output path
        relative_path = rst_file.relative_to(input_dir)
        output_file = output_dir / relative_path.with_suffix('.md')
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Convert filename to lowercase with hyphens
        new_name = re.sub(r'([a-z])([A-Z])', r'\1-\2', output_file.stem).lower()
        output_file = output_file.with_name(f'{new_name}.md')

        if convert_file(rst_file, output_file, anchor_map):
            success_count += 1
        else:
            fail_count += 1

    print(f'\nConversion complete: {success_count} succeeded, {fail_count} failed')


def main():
    parser = argparse.ArgumentParser(
        description='Convert Robot Framework User Guide reST to MkDocs Markdown'
    )
    parser.add_argument(
        'input',
        type=Path,
        help='Input reST file or directory'
    )
    parser.add_argument(
        'output',
        type=Path,
        help='Output Markdown file or directory'
    )
    parser.add_argument(
        '--anchor-map',
        type=Path,
        help='JSON file with legacy anchor mappings'
    )
    parser.add_argument(
        '--batch',
        action='store_true',
        help='Convert all .rst files in directory'
    )

    args = parser.parse_args()

    # Load anchor map if provided
    anchor_map = None
    if args.anchor_map and args.anchor_map.exists():
        anchor_map = json.loads(args.anchor_map.read_text())

    # Run conversion
    if args.batch or args.input.is_dir():
        batch_convert(args.input, args.output, anchor_map)
    else:
        if not convert_file(args.input, args.output, anchor_map):
            sys.exit(1)


if __name__ == '__main__':
    main()
