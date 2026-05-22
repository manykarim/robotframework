"""Content extractors for HTML and Markdown documents.

This package provides extractors for parsing documentation from various
formats and converting them into a common Section/Block structure for
comparison.
"""

import re
from typing import Any

from ..models import Block, BlockType, Section

# Import HTML extractor from dedicated module
from .html_extractor import (
    HTMLContentExtractor,
    extract_from_file as extract_from_html_file,
    extract_sections_from_html,
)

# Import Markdown extractor from dedicated module
from .md_extractor import (
    extract_from_directory,
    extract_sections_from_markdown,
    generate_anchor,
)


class MarkdownExtractor:
    """Extract structured content from Markdown documents."""

    # Patterns for Markdown elements
    HEADING_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    CODE_BLOCK_PATTERN = re.compile(r'```(\w*)\n(.*?)```', re.DOTALL)
    INLINE_CODE_PATTERN = re.compile(r'`([^`]+)`')
    TABLE_PATTERN = re.compile(r'^\|(.+)\|$', re.MULTILINE)
    LINK_PATTERN = re.compile(r'\[([^\]]*)\]\(([^)]+)\)')
    IMAGE_PATTERN = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
    LIST_ITEM_PATTERN = re.compile(r'^(\s*)([-*+]|\d+\.)\s+(.+)$', re.MULTILINE)
    ADMONITION_PATTERN = re.compile(r'^!!!\s+(\w+)(?:\s+"([^"]*)")?\s*$', re.MULTILINE)

    def __init__(self):
        self.sections: list[Section] = []
        self.section_stack: list[Section] = []

    def extract(self, content: str) -> list[Section]:
        """Extract sections from Markdown content."""
        self.sections = []
        self.section_stack = []

        lines = content.split('\n')
        current_blocks: list[Block] = []
        current_text: list[str] = []
        in_code_block = False
        code_language: str | None = None
        code_content: list[str] = []
        in_table = False
        table_lines: list[str] = []

        for line_num, line in enumerate(lines, 1):
            # Handle code blocks
            if line.startswith('```'):
                if in_code_block:
                    # End of code block
                    block = Block(
                        block_type=BlockType.CODE,
                        content='\n'.join(code_content),
                        metadata={'language': code_language},
                        line_number=line_num - len(code_content) - 1,
                    )
                    current_blocks.append(block)
                    in_code_block = False
                    code_content = []
                    code_language = None
                else:
                    # Start of code block
                    self._flush_text(current_text, current_blocks, line_num)
                    in_code_block = True
                    code_language = line[3:].strip() or None
                continue

            if in_code_block:
                code_content.append(line)
                continue

            # Handle tables
            if line.strip().startswith('|') and line.strip().endswith('|'):
                if not in_table:
                    self._flush_text(current_text, current_blocks, line_num)
                    in_table = True
                table_lines.append(line)
                continue
            elif in_table:
                # End of table
                self._add_table_block(table_lines, current_blocks, line_num - len(table_lines))
                table_lines = []
                in_table = False

            # Handle headings
            heading_match = self.HEADING_PATTERN.match(line)
            if heading_match:
                # Finish current text
                self._flush_text(current_text, current_blocks, line_num)

                # Add blocks to previous section
                if self.sections:
                    self.sections[-1].blocks.extend(current_blocks)
                current_blocks = []

                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()
                key = self._generate_key(title)

                section = Section(
                    number=self._generate_number(level),
                    title=title,
                    level=level,
                    key=key,
                    line_number=line_num,
                )
                self._add_section(section)
                continue

            # Handle list items
            list_match = self.LIST_ITEM_PATTERN.match(line)
            if list_match:
                self._flush_text(current_text, current_blocks, line_num)
                indent = len(list_match.group(1))
                marker = list_match.group(2)
                text = list_match.group(3)
                list_type = 'ol' if marker[0].isdigit() else 'ul'

                block = Block(
                    block_type=BlockType.LIST,
                    content=text,
                    metadata={
                        'type': list_type,
                        'indent': indent,
                        'marker': marker,
                    },
                    line_number=line_num,
                )
                current_blocks.append(block)
                continue

            # Regular text
            current_text.append(line)

        # Handle remaining content
        if in_code_block:
            block = Block(
                block_type=BlockType.CODE,
                content='\n'.join(code_content),
                metadata={'language': code_language},
                line_number=len(lines) - len(code_content),
            )
            current_blocks.append(block)

        if in_table:
            self._add_table_block(table_lines, current_blocks, len(lines) - len(table_lines) + 1)

        self._flush_text(current_text, current_blocks, len(lines))

        if self.sections:
            self.sections[-1].blocks.extend(current_blocks)

        # Extract links and images from all blocks
        self._extract_links_and_images()

        return self.sections

    def _flush_text(self, text_lines: list[str], blocks: list[Block], line_num: int):
        """Flush accumulated text as a paragraph block."""
        text = '\n'.join(text_lines).strip()
        if text:
            # Check for images
            for match in self.IMAGE_PATTERN.finditer(text):
                alt, src = match.groups()
                block = Block(
                    block_type=BlockType.IMAGE,
                    content=match.group(0),
                    metadata={'src': src, 'alt': alt},
                    line_number=line_num,
                )
                blocks.append(block)

            # Add as paragraph if not just images
            remaining = self.IMAGE_PATTERN.sub('', text).strip()
            if remaining:
                block = Block(
                    block_type=BlockType.PARAGRAPH,
                    content=text,
                    metadata={},
                    line_number=line_num - len(text_lines),
                )
                blocks.append(block)
        text_lines.clear()

    def _add_table_block(self, table_lines: list[str], blocks: list[Block], line_num: int):
        """Add a table block from parsed lines."""
        if not table_lines:
            return

        rows: list[list[str]] = []
        for line in table_lines:
            # Skip separator lines
            if re.match(r'^\|[\s\-:|]+\|$', line):
                continue
            cells = [cell.strip() for cell in line.strip('|').split('|')]
            rows.append(cells)

        content = '\n'.join(' | '.join(row) for row in rows)
        block = Block(
            block_type=BlockType.TABLE,
            content=content,
            metadata={'rows': len(rows), 'data': rows},
            line_number=line_num,
        )
        blocks.append(block)

    def _add_section(self, section: Section):
        """Add a section to the hierarchy."""
        while self.section_stack and self.section_stack[-1].level >= section.level:
            self.section_stack.pop()

        if self.section_stack:
            section.parent = self.section_stack[-1]
            self.section_stack[-1].subsections.append(section)

        self.sections.append(section)
        self.section_stack.append(section)

    def _generate_key(self, title: str) -> str:
        """Generate a normalized key from a title."""
        key = title.lower()
        key = re.sub(r'[^\w\s-]', '', key)
        key = re.sub(r'\s+', '-', key)
        return key.strip('-')

    def _generate_number(self, level: int) -> str:
        """Generate a section number based on current hierarchy."""
        # Count sections at each level
        counts = [0] * 6
        for section in self.sections:
            counts[section.level - 1] += 1
        counts[level - 1] += 1

        # Build number string
        parts = []
        for i in range(level):
            if counts[i] > 0:
                parts.append(str(counts[i]))
        return '.'.join(parts) if parts else '1'

    def _extract_links_and_images(self):
        """Extract links and images from paragraph content."""
        for section in self.sections:
            new_blocks: list[Block] = []
            for block in section.blocks:
                if block.block_type == BlockType.PARAGRAPH:
                    # Extract links
                    for match in self.LINK_PATTERN.finditer(block.content):
                        text, href = match.groups()
                        link_block = Block(
                            block_type=BlockType.LINK,
                            content=match.group(0),
                            metadata={'href': href, 'text': text},
                            line_number=block.line_number,
                        )
                        new_blocks.append(link_block)
                new_blocks.append(block)
            section.blocks = new_blocks


def extract_html(content: str) -> list[Section]:
    """Extract sections from HTML content."""
    return extract_sections_from_html(content)


def extract_markdown(content: str) -> list[Section]:
    """Extract sections from Markdown content."""
    extractor = MarkdownExtractor()
    return extractor.extract(content)


# Export all public symbols
__all__ = [
    # HTML extractor
    'HTMLContentExtractor',
    'extract_sections_from_html',
    'extract_from_html_file',
    'extract_html',
    # Markdown extractor
    'MarkdownExtractor',
    'extract_markdown',
    'extract_from_directory',
    'extract_sections_from_markdown',
    'generate_anchor',
]
