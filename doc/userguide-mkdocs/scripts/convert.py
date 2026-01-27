#!/usr/bin/env python3
"""
RST to Markdown converter for Robot Framework User Guide.

This converter handles Robot Framework-specific RST constructs including:
- Custom roles: :setting:, :option:, :name:, :file:, :codesc:
- Sourcecode directives with language specifications (399 instances)
- reST admonitions (note, warning, tip, etc.) (211 instances)
- Cross-references and link targets (280 definitions, 1630 references)
- Tables (grid and simple formats) (19 instances)
- Figures and images (13 instances)

Usage:
    python convert.py [--single FILE] [--output DIR] [--dry-run]

Examples:
    python convert.py                           # Convert all files
    python convert.py --single Introduction.rst # Convert single file
    python convert.py --dry-run                 # Preview without writing
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, List, Tuple


@dataclass
class ConversionStats:
    """Track conversion statistics."""
    files_processed: int = 0
    custom_roles_converted: int = 0
    code_blocks_converted: int = 0
    admonitions_converted: int = 0
    cross_refs_converted: int = 0
    tables_converted: int = 0
    figures_converted: int = 0
    warnings: List[str] = field(default_factory=list)


class RstToMarkdownConverter:
    """Convert Robot Framework RST documentation to MkDocs Markdown."""

    # Source and target directories
    SOURCE_DIR = Path(__file__).parent.parent.parent / "userguide" / "src"
    TARGET_DIR = Path(__file__).parent.parent / "docs"

    # RST section level characters (in order of nesting as used in RF docs)
    SECTION_CHARS = ['=', '-', '~', '^', '"', "'"]

    # Custom role mappings for Robot Framework User Guide
    # :setting:`value` -> `value` (code) - 110 usages
    # :option:`value` -> `value` (code) - 207 usages
    # :name:`value` -> *value* (emphasis) - 197 usages
    # :file:`value` -> *value* (emphasis) - 100 usages
    # :codesc:`value` -> `value` (code, with escape handling)
    ROLE_PATTERNS = {
        'setting': ('`', '`'),      # backticks for settings
        'option': ('`', '`'),       # backticks for options
        'name': ('*', '*'),         # italics for names (keywords, etc.)
        'file': ('*', '*'),         # italics for file paths
        'codesc': ('`', '`'),       # code with escape support
    }

    # Admonition mappings: RST directive -> MkDocs admonition type
    ADMONITION_TYPES = {
        'note': 'note',
        'warning': 'warning',
        'tip': 'tip',
        'important': 'important',
        'caution': 'warning',
        'danger': 'danger',
        'attention': 'warning',
        'hint': 'tip',
        'error': 'danger',
    }

    # Language mapping for code blocks
    LANG_MAP = {
        'robotframework': 'robotframework',
        'robot': 'robotframework',
        'rest': 'rst',
        'bash': 'bash',
        'shell': 'bash',
        'console': 'bash',
        'python': 'python',
        'java': 'java',
        'xml': 'xml',
        'html': 'html',
        'json': 'json',
        'none': '',
        'text': 'text',
    }

    def __init__(self, source_dir: Optional[Path] = None, target_dir: Optional[Path] = None):
        self.source_dir = source_dir or self.SOURCE_DIR
        self.target_dir = target_dir or self.TARGET_DIR
        self.stats = ConversionStats()
        self.anchor_map: Dict[str, str] = {}  # RST label -> MD anchor
        self.link_targets: Dict[str, str] = {}  # Reference name -> URL/anchor
        self.section_chars_seen: List[str] = []  # Track section char order per file

    def reset_file_state(self):
        """Reset per-file state for new file processing."""
        self.section_chars_seen = []
        self.anonymous_targets = []
        self.anonymous_target_index = 0

    def convert_custom_roles(self, content: str) -> str:
        """
        Convert Robot Framework custom roles to Markdown.

        Handles:
        - :setting:`Library` -> `Library`
        - :option:`--output` -> `--output`
        - :name:`Log` -> *Log*
        - :file:`output.xml` -> *output.xml*
        - :codesc:`\\n` -> `\\n` (preserves escapes)
        """
        for role, (prefix, suffix) in self.ROLE_PATTERNS.items():
            # Pattern matches :role:`content` - use non-greedy match
            # Handle content that might contain escaped backticks
            pattern = rf':{role}:`([^`]+)`'

            def replace_role(match, p=prefix, s=suffix, r=role):
                inner = match.group(1)
                # For codesc, handle escape sequences
                if r == 'codesc':
                    # Convert RST escapes like \` to just `
                    inner = inner.replace(r'\`', '`')
                self.stats.custom_roles_converted += 1
                return f'{p}{inner}{s}'

            content = re.sub(pattern, replace_role, content)

        # Also handle standard RST roles
        content = re.sub(r':strong:`([^`]+)`', r'**\1**', content)
        content = re.sub(r':emphasis:`([^`]+)`', r'*\1*', content)
        content = re.sub(r':literal:`([^`]+)`', r'`\1`', content)
        content = re.sub(r':code:`([^`]+)`', r'`\1`', content)
        content = re.sub(r':ref:`([^`]+)`', r'[\1](#\1)', content)

        return content

    def convert_inline_code(self, content: str) -> str:
        """
        Convert RST inline literals to Markdown code.

        RST: ``code``
        MD:  `code`
        """
        # Double backticks to single backticks
        content = re.sub(r'``([^`]+)``', r'`\1`', content)
        return content

    def convert_admonitions(self, content: str) -> str:
        """
        Convert RST admonitions to MkDocs format.

        RST:
            .. note:: This is a note.

            .. warning::
               Multi-line warning
               content here.

        MkDocs:
            !!! note
                This is a note.

            !!! warning
                Multi-line warning
                content here.
        """
        for rst_type, mkdocs_type in self.ADMONITION_TYPES.items():
            # Pattern 1: Block admonition with content on following lines only
            # .. type::
            #    content here
            block_pattern = rf'\.\.\s+{rst_type}::\s*\n((?:[ \t]+[^\n]*\n)+)'

            def replace_block(match, mtype=mkdocs_type):
                text = match.group(1)
                self.stats.admonitions_converted += 1
                return self._format_admonition(mtype, text)

            content = re.sub(block_pattern, replace_block, content)

            # Pattern 2: Inline admonition - content starts on same line, may continue
            # .. type:: content here
            #           more content (indented continuation)
            inline_pattern = rf'\.\.\s+{rst_type}::\s+([^\n]+(?:\n[ \t]+[^\n]+)*)'

            def replace_inline(match, mtype=mkdocs_type):
                text = match.group(1)
                self.stats.admonitions_converted += 1
                return self._format_admonition(mtype, text)

            content = re.sub(inline_pattern, replace_inline, content)

        return content

    def _format_admonition(self, admon_type: str, text: str) -> str:
        """Format admonition content with proper indentation."""
        lines = text.rstrip('\n').split('\n')

        # Find minimum indentation (excluding empty lines and first line)
        min_indent = float('inf')
        for i, line in enumerate(lines):
            if line.strip():
                indent = len(line) - len(line.lstrip())
                # First line might not have indent if it's inline style
                if i == 0:
                    min_indent = 0
                else:
                    min_indent = min(min_indent, indent)

        if min_indent == float('inf'):
            min_indent = 0

        # Re-indent with 4 spaces
        processed_lines = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped:
                processed_lines.append('    ' + stripped)
            elif processed_lines:  # Keep empty lines in middle
                processed_lines.append('')

        # Remove trailing empty lines
        while processed_lines and not processed_lines[-1].strip():
            processed_lines.pop()

        return f'!!! {admon_type}\n' + '\n'.join(processed_lines) + '\n'

    def convert_code_blocks(self, content: str) -> str:
        """
        Convert RST sourcecode/code-block directives to Markdown fenced code blocks.

        RST:
            .. sourcecode:: python

               def example():
                   pass

        MD:
            ```python
            def example():
                pass
            ```
        """
        # Pattern for sourcecode/code-block/code directives
        pattern = r'\.\.\s+(?:sourcecode|code-block|code)::\s*(\w*)\s*\n((?:\s*\n|\s+[^\n]*\n)*)'

        def replace_code_block(match):
            lang = match.group(1).lower().strip() if match.group(1) else ''
            code = match.group(2)

            # Map language if needed
            lang = self.LANG_MAP.get(lang, lang)

            self.stats.code_blocks_converted += 1

            # Find minimum indentation in code block
            lines = code.split('\n')
            min_indent = float('inf')
            for line in lines:
                if line.strip():
                    indent = len(line) - len(line.lstrip())
                    min_indent = min(min_indent, indent)

            if min_indent == float('inf'):
                min_indent = 0

            # Remove the common indentation
            processed_lines = []
            started = False
            for line in lines:
                if line.strip():
                    started = True
                if started:
                    if len(line) >= min_indent:
                        processed_lines.append(line[min_indent:])
                    else:
                        processed_lines.append(line.lstrip())

            # Remove trailing empty lines
            while processed_lines and not processed_lines[-1].strip():
                processed_lines.pop()

            code_content = '\n'.join(processed_lines)

            return f'```{lang}\n{code_content}\n```\n'

        content = re.sub(pattern, replace_code_block, content)
        return content

    def extract_link_targets(self, content: str) -> str:
        """
        Extract RST link targets and store them for later reference resolution.

        RST:
            .. _label: URL or
            .. _label:
            __ URL (anonymous)

        Stores mapping for cross-reference conversion.
        """
        # Extract anonymous targets: __ URL
        # These are used with `text`__ references
        anon_pattern = r'^__\s+(https?://[^\s]+)\s*$'
        self.anonymous_targets = re.findall(anon_pattern, content, re.MULTILINE)
        self.anonymous_target_index = 0

        # External link targets: .. _name: URL
        ext_pattern = r'\.\.\s+_([^:]+):\s+(https?://[^\s]+)\s*\n'

        for match in re.finditer(ext_pattern, content):
            name = match.group(1).strip()
            url = match.group(2).strip()
            self.link_targets[name.lower()] = url

        # Remove link target definitions from content
        content = re.sub(ext_pattern, '', content)

        # Internal anchor targets: .. _label:
        anchor_pattern = r'\.\.\s+_([^:]+):\s*\n(?!\s*https?://)'

        for match in re.finditer(anchor_pattern, content):
            label = match.group(1).strip()
            # Create slug from label
            slug = self._create_slug(label)
            self.anchor_map[label.lower()] = slug

        # Convert internal anchor targets to HTML anchors
        def replace_anchor(match):
            label = match.group(1).strip()
            slug = self._create_slug(label)
            return f'<a id="{slug}"></a>\n'

        content = re.sub(anchor_pattern, replace_anchor, content)

        return content

    def convert_cross_references(self, content: str) -> str:
        """
        Convert RST cross-references to Markdown links.

        RST: `Link Text`_
        MD:  [Link Text](#slug) or [Link Text](url)

        RST: `text <target>`_
        MD:  [text](#slug) or [text](url)
        """
        # Pattern for `text <target>`_ style references
        explicit_pattern = r'`([^<`]+)\s+<([^>]+)>`_'

        def replace_explicit_ref(match):
            text = match.group(1).strip()
            target = match.group(2).strip()
            self.stats.cross_refs_converted += 1

            # Check if target is a URL
            if target.startswith('http://') or target.startswith('https://'):
                return f'[{text}]({target})'

            # Check if target is in link targets
            target_lower = target.lower()
            if target_lower in self.link_targets:
                return f'[{text}]({self.link_targets[target_lower]})'

            # Otherwise treat as internal anchor
            slug = self._create_slug(target)
            return f'[{text}](#{slug})'

        content = re.sub(explicit_pattern, replace_explicit_ref, content)

        # Pattern for `text`_ style references (backticked)
        backtick_pattern = r'`([^`]+)`_(?!_)'

        def replace_backtick_ref(match):
            text = match.group(1).strip()
            self.stats.cross_refs_converted += 1

            text_lower = text.lower()

            # Check if it's in link targets
            if text_lower in self.link_targets:
                return f'[{text}]({self.link_targets[text_lower]})'

            # Check if it's in anchor map
            if text_lower in self.anchor_map:
                return f'[{text}](#{self.anchor_map[text_lower]})'

            # Default to creating a slug
            slug = self._create_slug(text)
            return f'[{text}](#{slug})'

        content = re.sub(backtick_pattern, replace_backtick_ref, content)

        # Anonymous references: `text`__ and word__
        # These link to anonymous targets (__URL) in document order.
        # We do a proper two-pass resolution here.
        content = self._resolve_anonymous_references(content)

        # Pattern for word_ style references (without backticks)
        # Match simple word references like Python_ or BuiltIn_
        # Don't match across lines, don't match dunder methods
        word_pattern = r'(?<![`\w_])(\w+)_(?![_\w`])'

        def replace_word_ref(match):
            text = match.group(1).strip()

            # Skip if it looks like a Python dunder or internal name
            if text.startswith('_') or text.endswith('_'):
                return match.group(0)

            self.stats.cross_refs_converted += 1

            text_lower = text.lower()

            if text_lower in self.link_targets:
                return f'[{text}]({self.link_targets[text_lower]})'

            if text_lower in self.anchor_map:
                return f'[{text}](#{self.anchor_map[text_lower]})'

            slug = self._create_slug(text)
            return f'[{text}](#{slug})'

        content = re.sub(word_pattern, replace_word_ref, content)

        return content

    def _resolve_anonymous_references(self, content: str) -> str:
        """
        Resolve RST anonymous references (`text`__ and word__) with their targets.

        RST anonymous references are resolved in document order - the first
        reference matches the first target, etc.
        """
        # Find all anonymous reference positions
        backtick_pattern = r'`([^`]+)`__'
        word_pattern = r'(?<![`\w])(\w+)__(?![_\w])'

        # Collect all reference positions with their matched text
        refs = []
        for m in re.finditer(backtick_pattern, content):
            refs.append((m.start(), m.end(), m.group(1), 'backtick'))
        for m in re.finditer(word_pattern, content):
            refs.append((m.start(), m.end(), m.group(1), 'word'))

        # Sort by position
        refs.sort(key=lambda x: x[0])

        # Get anonymous targets in order
        targets = getattr(self, 'anonymous_targets', [])

        # Build replacement content
        result = []
        last_end = 0

        for i, (start, end, text, ref_type) in enumerate(refs):
            # Add content before this reference
            result.append(content[last_end:start])

            # Get the target URL (or fallback to anchor)
            if i < len(targets):
                url = targets[i]
                result.append(f'[{text}]({url})')
            else:
                slug = self._create_slug(text)
                result.append(f'[{text}](#{slug})')

            self.stats.cross_refs_converted += 1
            last_end = end

        # Add remaining content
        result.append(content[last_end:])

        return ''.join(result)

    def convert_sections(self, content: str) -> str:
        """
        Convert RST section headers to Markdown headers.

        RST uses underlines (and optionally overlines) with =, -, ~, etc.
        """
        lines = content.split('\n')
        result = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # Check for overline + title + underline pattern
            if i + 2 < len(lines):
                next_line = lines[i + 1]
                after_line = lines[i + 2]

                # Overlined header: === / Title / ===
                if (self._is_section_line(line) and
                    next_line.strip() and
                    self._is_section_line(after_line) and
                    line[0] == after_line[0] and
                    len(line.rstrip()) >= len(next_line.strip())):

                    char = line[0]
                    level = self._get_section_level(char)
                    title = next_line.strip()
                    result.append(f'{"#" * level} {title}')
                    result.append('')
                    i += 3
                    continue

            # Check for title + underline pattern
            if i + 1 < len(lines):
                next_line = lines[i + 1]

                if (line.strip() and
                    not line.startswith(' ') and
                    not line.startswith('.') and
                    not line.startswith('|') and
                    self._is_section_line(next_line) and
                    len(next_line.rstrip()) >= len(line.rstrip())):

                    char = next_line[0]
                    level = self._get_section_level(char)
                    title = line.strip()
                    result.append(f'{"#" * level} {title}')
                    result.append('')
                    i += 2
                    continue

            result.append(line)
            i += 1

        return '\n'.join(result)

    def convert_tables(self, content: str) -> str:
        """
        Convert RST tables to Markdown tables.

        Handles grid tables with +---+ borders, optionally indented.
        """
        # Find grid tables by looking for the characteristic +---+ pattern
        # A grid table consists of:
        # 1. A top border line: +---+---+
        # 2. Content lines: | x | y |
        # 3. Separator lines: +---+---+ or +===+===+
        # 4. A bottom border line: +---+---+

        lines = content.split('\n')
        result = []
        i = 0

        while i < len(lines):
            line = lines[i]
            stripped = line.lstrip()

            # Check if this looks like the start of a grid table
            if stripped.startswith('+') and re.match(r'^\+[-=+]+\+$', stripped):
                # Try to parse as a grid table
                table_lines, table_end = self._extract_grid_table(lines, i)
                if table_lines:
                    md_table = self._parse_grid_table_v2(table_lines)
                    result.append(md_table)
                    i = table_end
                    continue

            result.append(line)
            i += 1

        return '\n'.join(result)

    def _extract_grid_table(self, lines: List[str], start: int) -> Tuple[List[str], int]:
        """Extract a complete grid table from lines starting at given index."""
        table_lines = []
        i = start

        # Get the indentation of the first line
        first_line = lines[i]
        indent = len(first_line) - len(first_line.lstrip())
        first_border = first_line.lstrip()

        # Count the number of columns from the first border
        expected_cols = first_border.count('+') - 1

        table_lines.append(first_border)
        i += 1
        found_header_sep = False
        found_final_border = False

        while i < len(lines):
            line = lines[i]

            # Check if line is empty
            if not line.strip():
                # Empty line - if we've seen content and a border, table is done
                if len(table_lines) > 1 and table_lines[-1].startswith('+'):
                    found_final_border = True
                    break
                i += 1
                continue

            line_stripped = line.lstrip()
            line_indent = len(line) - len(line_stripped)

            # Table lines should be at the same indentation
            if line_indent != indent:
                break

            # Table lines must start with + or |
            if not (line_stripped.startswith('+') or line_stripped.startswith('|')):
                break

            table_lines.append(line_stripped)

            # Track if we've seen the header separator (with =)
            if line_stripped.startswith('+') and '=' in line_stripped:
                found_header_sep = True

            i += 1

        # Verify we have a valid table (at least header + separator + one row + footer)
        if len(table_lines) >= 4 and table_lines[0].startswith('+') and table_lines[-1].startswith('+'):
            self.stats.tables_converted += 1
            return table_lines, i

        # Didn't find a valid table
        return [], start

    def _parse_grid_table_v2(self, table_lines: List[str]) -> str:
        """Parse RST grid table lines and convert to Markdown."""
        if not table_lines:
            return ''

        # Find column positions from the first border line
        first_border = table_lines[0]
        col_positions = []
        for i, char in enumerate(first_border):
            if char == '+':
                col_positions.append(i)

        if len(col_positions) < 2:
            return '\n'.join(table_lines)  # Not a valid table

        # Extract cell contents
        rows = []
        current_row = [''] * (len(col_positions) - 1)
        header_row_idx = -1

        for line in table_lines:
            if line.startswith('+'):
                # This is a separator line
                if current_row and any(cell.strip() for cell in current_row):
                    rows.append(current_row)
                    current_row = [''] * (len(col_positions) - 1)

                # Check if it's a header separator (uses =)
                if '=' in line and rows:
                    header_row_idx = len(rows) - 1
            elif line.startswith('|'):
                # This is a content line - extract cells by position
                for col_idx in range(len(col_positions) - 1):
                    start = col_positions[col_idx] + 1
                    end = col_positions[col_idx + 1]
                    if end <= len(line):
                        cell_content = line[start:end].strip()
                        # Remove the trailing |
                        if cell_content.endswith('|'):
                            cell_content = cell_content[:-1].strip()

                        # Handle RST line block markers (| at start of cell)
                        if cell_content.startswith('|'):
                            cell_content = cell_content[1:].strip()
                        if cell_content.startswith('| '):
                            cell_content = cell_content[2:].strip()

                        # Append to existing cell content
                        if current_row[col_idx]:
                            current_row[col_idx] += ' ' + cell_content
                        else:
                            current_row[col_idx] = cell_content

        if not rows:
            return '\n'.join(table_lines)

        # Build markdown table
        md_lines = []
        num_cols = len(col_positions) - 1

        for idx, row in enumerate(rows):
            # Clean cells
            cleaned = [cell.strip() for cell in row]
            md_lines.append('| ' + ' | '.join(cleaned) + ' |')

            # Add separator after header row
            if idx == header_row_idx or (header_row_idx == -1 and idx == 0):
                md_lines.append('| ' + ' | '.join(['---'] * num_cols) + ' |')

        return '\n'.join(md_lines)

        return '\n'.join(md_lines) + '\n'

    def convert_figures(self, content: str) -> str:
        """
        Convert RST figures to Markdown images.

        RST:
            .. figure:: path/to/image.png

               Caption text

        MD:
            ![Caption text](path/to/image.png)
        """
        # Figure with caption
        pattern = r'\.\.\s+figure::\s*([^\n]+)\n(?:\s*:[^:]+:[^\n]*\n)*(?:\s*\n)?\s*([^\n]*)'

        def replace_figure(match):
            path = match.group(1).strip()
            caption = match.group(2).strip() if match.group(2) else ''
            self.stats.figures_converted += 1

            # Adjust path if needed (remove src/ prefix if present for MkDocs)
            if path.startswith('src/'):
                path = '../assets/images/' + path[4:]

            alt_text = caption if caption else 'Figure'

            if caption:
                return f'![{alt_text}]({path})\n\n*{caption}*\n'
            else:
                return f'![{alt_text}]({path})\n'

        content = re.sub(pattern, replace_figure, content)

        # Simple image directive
        img_pattern = r'\.\.\s+image::\s*([^\n]+)'
        content = re.sub(img_pattern, r'![](\1)', content)

        return content

    def convert_lists(self, content: str) -> str:
        """
        Convert RST lists to Markdown lists.

        RST uses various bullet characters and #. for numbered lists.
        """
        # Numbered list with #.
        content = re.sub(r'^#\.\s+', '1. ', content, flags=re.MULTILINE)

        return content

    def remove_rst_directives(self, content: str) -> str:
        """Remove or convert remaining RST directives."""
        # Remove anonymous reference targets: __ URL or __ `text`_
        content = re.sub(r'^__\s+https?://[^\s]+\s*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'^__\s+`[^`]+`_\s*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'^__\s+\[[^\]]+\]\([^)]+\)\s*$', '', content, flags=re.MULTILINE)

        # Remove table of contents directive
        content = re.sub(r'\.\.\s+contents::.*?(?=\n\n|\n[^\s]|\Z)', '', content, flags=re.DOTALL)

        # Remove sectnum directive
        content = re.sub(r'\.\.\s+sectnum::.*?(?=\n\n|\n[^\s]|\Z)', '', content, flags=re.DOTALL)

        # Remove include directives (we handle file inclusion separately)
        content = re.sub(r'\.\.\s+include::.*\n', '', content)

        # Remove default-role directive
        content = re.sub(r'\.\.\s+default-role::.*\n', '', content)

        # Remove role definitions
        content = re.sub(r'\.\.\s+role::.*\n', '', content)

        # Remove footer directive
        content = re.sub(r'\.\.\s+footer::.*\n', '', content)

        # Remove class directive from tables
        content = re.sub(r'\s+:class:\s+\w+', '', content)

        # Remove raw directives
        content = re.sub(r'\.\.\s+raw::.*?(?=\n\n|\n[^\s]|\Z)', '', content, flags=re.DOTALL)

        # Remove table directives (just the directive, keep content)
        content = re.sub(r'\.\.\s+table::[^\n]*\n', '', content)

        return content

    def convert_substitutions(self, content: str) -> str:
        """Convert RST substitution references."""
        # |version| -> will be handled by MkDocs variables
        content = re.sub(r'\|version\|', '{{ version }}', content)
        content = re.sub(r'\|copy\|', '(C)', content)

        return content

    def _is_section_line(self, line: str) -> bool:
        """Check if line is a section underline/overline."""
        line = line.rstrip()
        if not line or len(line) < 3:
            return False
        char = line[0]
        return char in self.SECTION_CHARS and all(c == char for c in line)

    def _get_section_level(self, char: str) -> int:
        """Get Markdown header level from RST section character."""
        # Track order of section characters as they appear
        if char not in self.section_chars_seen:
            self.section_chars_seen.append(char)
        return self.section_chars_seen.index(char) + 1

    def _create_slug(self, text: str) -> str:
        """Create a URL-friendly slug from text."""
        # Convert to lowercase
        slug = text.lower()
        # Replace spaces and underscores with hyphens
        slug = re.sub(r'[\s_]+', '-', slug)
        # Remove non-alphanumeric characters except hyphens
        slug = re.sub(r'[^a-z0-9-]', '', slug)
        # Remove multiple consecutive hyphens
        slug = re.sub(r'-+', '-', slug)
        # Remove leading/trailing hyphens
        slug = slug.strip('-')
        return slug

    def convert_file(self, rst_path: Path, md_path: Optional[Path] = None) -> str:
        """
        Convert a single RST file to Markdown.

        Args:
            rst_path: Path to RST file
            md_path: Optional path for output (defaults to target dir)

        Returns:
            Converted Markdown content
        """
        self.reset_file_state()
        content = rst_path.read_text(encoding='utf-8')

        # Apply conversions in order
        content = self.extract_link_targets(content)
        content = self.convert_custom_roles(content)
        content = self.convert_inline_code(content)
        content = self.convert_code_blocks(content)
        content = self.convert_admonitions(content)
        content = self.convert_sections(content)
        content = self.convert_figures(content)
        content = self.convert_tables(content)
        content = self.convert_cross_references(content)
        content = self.convert_substitutions(content)
        content = self.remove_rst_directives(content)
        content = self.convert_lists(content)

        # Clean up multiple blank lines
        content = re.sub(r'\n{3,}', '\n\n', content)

        self.stats.files_processed += 1

        return content

    def convert_all(self, dry_run: bool = False) -> ConversionStats:
        """
        Convert all RST files in the source directory.

        Args:
            dry_run: If True, don't write files, just process

        Returns:
            Conversion statistics
        """
        # Ensure target directory exists
        if not dry_run:
            self.target_dir.mkdir(parents=True, exist_ok=True)

        # Find all RST files
        rst_files = list(self.source_dir.rglob('*.rst'))

        # First pass: collect all link targets from all files
        print("Pass 1: Collecting link targets...")
        for rst_file in rst_files:
            if rst_file.name in ('roles.rst', 'version.rst'):
                continue  # Skip utility files
            content = rst_file.read_text(encoding='utf-8')
            self.extract_link_targets(content)

        print(f"  Found {len(self.link_targets)} external link targets")
        print(f"  Found {len(self.anchor_map)} internal anchors")

        # Reset stats for actual conversion
        self.stats = ConversionStats()

        # Second pass: convert files
        print("\nPass 2: Converting files...")
        for rst_file in rst_files:
            if rst_file.name in ('roles.rst', 'version.rst'):
                continue  # Skip utility files

            # Determine output path
            rel_path = rst_file.relative_to(self.source_dir)
            md_path = self.target_dir / rel_path.with_suffix('.md')

            # Convert
            md_content = self.convert_file(rst_file)

            # Write if not dry run
            if not dry_run:
                md_path.parent.mkdir(parents=True, exist_ok=True)
                md_path.write_text(md_content, encoding='utf-8')
                print(f"  Converted: {rel_path} -> {md_path.name}")
            else:
                print(f"  Would convert: {rel_path}")

        return self.stats


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Convert Robot Framework RST documentation to MkDocs Markdown'
    )
    parser.add_argument(
        '--single',
        type=str,
        help='Convert a single file (provide filename or path)'
    )
    parser.add_argument(
        '--source', '-s',
        type=str,
        help='Source directory (default: userguide/src)'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output directory (default: userguide-mkdocs/docs)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview conversion without writing files'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Print detailed conversion statistics'
    )

    args = parser.parse_args()

    # Set up converter
    source_dir = Path(args.source) if args.source else None
    target_dir = Path(args.output) if args.output else None
    converter = RstToMarkdownConverter(source_dir=source_dir, target_dir=target_dir)

    if args.single:
        # Convert single file
        rst_path = Path(args.single)
        if not rst_path.is_absolute():
            rst_path = converter.source_dir / rst_path

        if not rst_path.exists():
            # Try to find it
            matches = list(converter.source_dir.rglob(f'*{args.single}*'))
            if matches:
                rst_path = matches[0]
            else:
                print(f"Error: File not found: {args.single}")
                sys.exit(1)

        # First collect all link targets
        for rst_file in converter.source_dir.rglob('*.rst'):
            if rst_file.name not in ('roles.rst', 'version.rst'):
                content = rst_file.read_text(encoding='utf-8')
                converter.extract_link_targets(content)

        md_content = converter.convert_file(rst_path)

        if args.dry_run:
            print(f"=== Converted content for {rst_path.name} ===\n")
            print(md_content[:5000])  # Print first 5000 chars
            if len(md_content) > 5000:
                print(f"\n... ({len(md_content) - 5000} more characters)")
        else:
            md_path = rst_path.with_suffix('.md')
            if target_dir:
                md_path = target_dir / md_path.name
            else:
                md_path = converter.target_dir / rst_path.relative_to(converter.source_dir).with_suffix('.md')
            md_path.parent.mkdir(parents=True, exist_ok=True)
            md_path.write_text(md_content, encoding='utf-8')
            print(f"Converted: {rst_path} -> {md_path}")
    else:
        # Convert all files
        converter.convert_all(dry_run=args.dry_run)

    # Print statistics
    if args.stats or args.dry_run:
        print("\n=== Conversion Statistics ===")
        print(f"Files processed: {converter.stats.files_processed}")
        print(f"Custom roles converted: {converter.stats.custom_roles_converted}")
        print(f"Code blocks converted: {converter.stats.code_blocks_converted}")
        print(f"Admonitions converted: {converter.stats.admonitions_converted}")
        print(f"Cross-references converted: {converter.stats.cross_refs_converted}")
        print(f"Tables converted: {converter.stats.tables_converted}")
        print(f"Figures converted: {converter.stats.figures_converted}")

        if converter.stats.warnings:
            print("\nWarnings:")
            for warning in converter.stats.warnings:
                print(f"  - {warning}")


if __name__ == '__main__':
    main()
