"""Markdown extractor for docdiff comparison tool.

This module provides robust Markdown parsing using only Python stdlib (re module)
to extract structured content from MkDocs Markdown files.
"""

import os
import re
from typing import Dict, List, Optional, Tuple

from ..models import Block, BlockType, Section


def generate_anchor(heading_text: str) -> str:
    """Convert heading text to MkDocs-style anchor.

    Args:
        heading_text: The heading text to convert.

    Returns:
        A lowercase anchor with spaces replaced by hyphens and special chars removed.

    Examples:
        >>> generate_anchor("Hello World")
        'hello-world'
        >>> generate_anchor("1.2.3 Section Title!")
        '123-section-title'
    """
    # Lowercase the text
    anchor = heading_text.lower()
    # Remove common special characters (keep alphanumeric, spaces, hyphens)
    anchor = re.sub(r'[^\w\s-]', '', anchor)
    # Replace multiple spaces/underscores with single hyphen
    anchor = re.sub(r'[\s_]+', '-', anchor)
    # Remove leading/trailing hyphens
    anchor = anchor.strip('-')
    # Collapse multiple consecutive hyphens
    anchor = re.sub(r'-+', '-', anchor)
    return anchor


def _extract_section_number(text: str) -> Tuple[Optional[str], str]:
    """Extract section number prefix from heading text if present.

    Args:
        text: The heading text.

    Returns:
        Tuple of (number, remaining_text). Number is None if not found.

    Examples:
        >>> _extract_section_number("1.2.3 Section Title")
        ('1.2.3', 'Section Title')
        >>> _extract_section_number("Introduction")
        (None, 'Introduction')
    """
    # Match patterns like "1.", "1.2", "1.2.3", etc. at start
    match = re.match(r'^(\d+(?:\.\d+)*\.?)\s+(.*)$', text.strip())
    if match:
        number = match.group(1).rstrip('.')
        remaining = match.group(2).strip()
        return number, remaining
    return None, text.strip()


def _generate_section_key(heading_text: str) -> str:
    """Generate a unique section key from heading text.

    Args:
        heading_text: The heading text.

    Returns:
        A normalized key (lowercase, punctuation removed, spaces collapsed).
    """
    # Remove section numbers first
    _, text = _extract_section_number(heading_text)
    # Lowercase
    key = text.lower()
    # Remove punctuation except spaces
    key = re.sub(r'[^\w\s]', '', key)
    # Collapse whitespace
    key = re.sub(r'\s+', ' ', key).strip()
    # Replace spaces with underscores for key format
    key = key.replace(' ', '_')
    return key


class MarkdownExtractor:
    """Parses Markdown content and extracts structured blocks.

    This extractor handles:
    - ATX headings (# through ######)
    - Setext headings (=== and --- underlines)
    - Paragraphs (text blocks separated by blank lines)
    - Lists (-, *, + for unordered; 1. 2. for ordered) with nesting
    - Fenced code blocks (```lang ... ```) with language tags
    - Tables (pipe tables with | header | separator |)
    - Material for MkDocs admonitions (!!! note, !!! warning, ???)
    - Links [text](href) and images ![alt](src)
    - Inline code `code` within paragraphs
    """

    # Regex patterns for block-level elements
    FRONTMATTER_PATTERN = re.compile(r'^---\s*\n.*?\n---\s*\n', re.DOTALL)
    ATX_HEADING_PATTERN = re.compile(r'^(#{1,6})\s+(.+?)(?:\s+#*)?$', re.MULTILINE)
    SETEXT_H1_PATTERN = re.compile(r'^(.+)\n=+\s*$', re.MULTILINE)
    SETEXT_H2_PATTERN = re.compile(r'^(.+)\n-+\s*$', re.MULTILINE)
    FENCED_CODE_PATTERN = re.compile(
        r'^(`{3,}|~{3,})(\w*)[ \t]*\n(.*?)^\1\s*$',
        re.MULTILINE | re.DOTALL
    )
    ADMONITION_PATTERN = re.compile(
        r'^(!{3}|\?{3}\+?)\s+(\w+)(?:\s+"([^"]*)")?\s*\n((?:[ \t]+.+\n?)*)',
        re.MULTILINE
    )
    TABLE_PATTERN = re.compile(
        r'^(\|.+\|)\s*\n(\|[-:| ]+\|)\s*\n((?:\|.+\|\s*\n?)+)',
        re.MULTILINE
    )
    UNORDERED_LIST_PATTERN = re.compile(r'^([ \t]*)[-*+]\s+(.+)$', re.MULTILINE)
    ORDERED_LIST_PATTERN = re.compile(r'^([ \t]*)(\d+)[.)]\s+(.+)$', re.MULTILINE)

    # Inline patterns
    LINK_PATTERN = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    IMAGE_PATTERN = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
    INLINE_CODE_PATTERN = re.compile(r'`([^`]+)`')

    def __init__(self):
        """Initialize the Markdown extractor."""
        self.blocks: List[Block] = []
        self.current_line: int = 0

    def extract(self, content: str) -> List[Block]:
        """Extract all content blocks from Markdown content.

        Args:
            content: The Markdown content to parse.

        Returns:
            List of Block objects representing the parsed content.
        """
        self.blocks = []
        self.current_line = 1

        # Remove frontmatter if present
        content = self._remove_frontmatter(content)

        # Track positions of already-processed content
        processed_ranges: List[Tuple[int, int]] = []

        # Extract fenced code blocks first (they may contain other patterns)
        content, processed_ranges = self._extract_fenced_code_blocks(
            content, processed_ranges
        )

        # Extract admonitions
        content, processed_ranges = self._extract_admonitions(
            content, processed_ranges
        )

        # Extract tables
        content, processed_ranges = self._extract_tables(content, processed_ranges)

        # Now process remaining content line by line
        self._extract_remaining_content(content, processed_ranges)

        return self.blocks

    def _remove_frontmatter(self, content: str) -> str:
        """Remove YAML frontmatter from the beginning of content."""
        if content.startswith('---'):
            match = re.match(r'^---\s*\n.*?\n---\s*\n', content, re.DOTALL)
            if match:
                # Count lines in frontmatter to adjust line numbers
                frontmatter_lines = match.group(0).count('\n')
                self.current_line = frontmatter_lines + 1
                return content[match.end():]
        return content

    def _extract_fenced_code_blocks(
        self, content: str, processed_ranges: List[Tuple[int, int]]
    ) -> Tuple[str, List[Tuple[int, int]]]:
        """Extract fenced code blocks and mark their positions."""
        for match in self.FENCED_CODE_PATTERN.finditer(content):
            start, end = match.span()
            processed_ranges.append((start, end))

            language = match.group(2) or None
            code_content = match.group(3)

            # Calculate line number
            line_num = content[:start].count('\n') + self.current_line

            self.blocks.append(Block(
                text=code_content.rstrip('\n'),
                block_type="code_block",
                language=language,
                source_line=line_num
            ))

        return content, processed_ranges

    def _extract_admonitions(
        self, content: str, processed_ranges: List[Tuple[int, int]]
    ) -> Tuple[str, List[Tuple[int, int]]]:
        """Extract Material for MkDocs admonitions."""
        for match in self.ADMONITION_PATTERN.finditer(content):
            start, end = match.span()

            # Skip if already processed
            if self._is_in_processed_range(start, end, processed_ranges):
                continue

            processed_ranges.append((start, end))

            marker = match.group(1)  # !!! or ??? or ???+
            admon_type = match.group(2)
            title = match.group(3) or admon_type.capitalize()
            body = match.group(4)

            # Dedent body content
            body_lines = body.split('\n')
            dedented_body = []
            for line in body_lines:
                # Remove leading indentation (typically 4 spaces)
                dedented_body.append(re.sub(r'^[ \t]{1,4}', '', line))
            body_text = '\n'.join(dedented_body).strip()

            line_num = content[:start].count('\n') + self.current_line

            # Determine if collapsible
            is_collapsible = marker.startswith('???')
            is_expanded = marker == '???+'

            self.blocks.append(Block(
                text=f"{title}\n{body_text}" if body_text else title,
                block_type="admonition",
                admonition_type=admon_type,
                source_line=line_num
            ))

        return content, processed_ranges

    def _extract_tables(
        self, content: str, processed_ranges: List[Tuple[int, int]]
    ) -> Tuple[str, List[Tuple[int, int]]]:
        """Extract Markdown tables."""
        for match in self.TABLE_PATTERN.finditer(content):
            start, end = match.span()

            # Skip if already processed
            if self._is_in_processed_range(start, end, processed_ranges):
                continue

            processed_ranges.append((start, end))

            header = match.group(1)
            separator = match.group(2)
            body = match.group(3)

            # Parse table into rows
            rows = []
            rows.append(self._parse_table_row(header))
            for row_line in body.strip().split('\n'):
                if row_line.strip():
                    rows.append(self._parse_table_row(row_line))

            line_num = content[:start].count('\n') + self.current_line

            self.blocks.append(Block(
                text=match.group(0).strip(),
                block_type="table",
                items=[str(row) for row in rows],
                source_line=line_num
            ))

        return content, processed_ranges

    def _parse_table_row(self, row: str) -> List[str]:
        """Parse a table row, handling escaped pipes."""
        # Replace escaped pipes temporarily
        row = row.replace('\\|', '\x00')
        # Split on unescaped pipes
        cells = row.split('|')
        # Restore escaped pipes and strip whitespace
        cells = [cell.replace('\x00', '|').strip() for cell in cells]
        # Remove empty first/last elements from leading/trailing pipes
        if cells and not cells[0]:
            cells = cells[1:]
        if cells and not cells[-1]:
            cells = cells[:-1]
        return cells

    def _is_in_processed_range(
        self, start: int, end: int, processed_ranges: List[Tuple[int, int]]
    ) -> bool:
        """Check if a position overlaps with already processed ranges."""
        for proc_start, proc_end in processed_ranges:
            if not (end <= proc_start or start >= proc_end):
                return True
        return False

    def _extract_remaining_content(
        self, content: str, processed_ranges: List[Tuple[int, int]]
    ) -> None:
        """Process remaining content for headings, lists, paragraphs, etc."""
        lines = content.split('\n')
        i = 0
        paragraph_buffer: List[str] = []
        paragraph_start_line: Optional[int] = None

        while i < len(lines):
            line = lines[i]
            line_num = self.current_line + i

            # Check if this position is in a processed range
            pos = sum(len(lines[j]) + 1 for j in range(i))
            if self._is_position_processed(pos, processed_ranges):
                i += 1
                continue

            # Check for ATX heading
            atx_match = re.match(r'^(#{1,6})\s+(.+?)(?:\s+#*)?$', line)
            if atx_match:
                self._flush_paragraph(paragraph_buffer, paragraph_start_line)
                paragraph_buffer = []
                paragraph_start_line = None

                level = len(atx_match.group(1))
                text = atx_match.group(2).strip()
                anchor = generate_anchor(text)

                self.blocks.append(Block(
                    text=text,
                    block_type="heading",
                    level=level,
                    anchor=anchor,
                    source_line=line_num
                ))
                i += 1
                continue

            # Check for setext heading (requires looking ahead)
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                if re.match(r'^=+\s*$', next_line) and line.strip():
                    self._flush_paragraph(paragraph_buffer, paragraph_start_line)
                    paragraph_buffer = []
                    paragraph_start_line = None

                    text = line.strip()
                    anchor = generate_anchor(text)

                    self.blocks.append(Block(
                        text=text,
                        block_type="heading",
                        level=1,
                        anchor=anchor,
                        source_line=line_num
                    ))
                    i += 2
                    continue
                elif re.match(r'^-+\s*$', next_line) and line.strip() and not re.match(r'^[-*+]\s', line):
                    self._flush_paragraph(paragraph_buffer, paragraph_start_line)
                    paragraph_buffer = []
                    paragraph_start_line = None

                    text = line.strip()
                    anchor = generate_anchor(text)

                    self.blocks.append(Block(
                        text=text,
                        block_type="heading",
                        level=2,
                        anchor=anchor,
                        source_line=line_num
                    ))
                    i += 2
                    continue

            # Check for list item
            list_match = re.match(r'^([ \t]*)[-*+]\s+(.+)$', line)
            ordered_match = re.match(r'^([ \t]*)(\d+)[.)]\s+(.+)$', line)

            if list_match or ordered_match:
                self._flush_paragraph(paragraph_buffer, paragraph_start_line)
                paragraph_buffer = []
                paragraph_start_line = None

                # Collect entire list
                list_items, list_type, lines_consumed = self._collect_list(
                    lines, i
                )
                self.blocks.append(Block(
                    text='\n'.join(list_items),
                    block_type="list",
                    list_type=list_type,
                    items=list_items,
                    source_line=line_num
                ))
                i += lines_consumed
                continue

            # Check for blank line
            if not line.strip():
                self._flush_paragraph(paragraph_buffer, paragraph_start_line)
                paragraph_buffer = []
                paragraph_start_line = None
                i += 1
                continue

            # Otherwise, accumulate paragraph content
            if paragraph_start_line is None:
                paragraph_start_line = line_num
            paragraph_buffer.append(line)
            i += 1

        # Flush any remaining paragraph
        self._flush_paragraph(paragraph_buffer, paragraph_start_line)

    def _is_position_processed(
        self, pos: int, processed_ranges: List[Tuple[int, int]]
    ) -> bool:
        """Check if a character position is within a processed range."""
        for start, end in processed_ranges:
            if start <= pos < end:
                return True
        return False

    def _flush_paragraph(
        self, buffer: List[str], start_line: Optional[int]
    ) -> None:
        """Flush accumulated paragraph content as a block."""
        if not buffer:
            return

        text = '\n'.join(buffer).strip()
        if not text:
            return

        # Extract inline elements
        links = self.LINK_PATTERN.findall(text)
        images = self.IMAGE_PATTERN.findall(text)

        # Create separate blocks for images
        for alt_text, src in images:
            self.blocks.append(Block(
                text=alt_text,
                block_type="image",
                alt_text=alt_text,
                src=src,
                source_line=start_line
            ))

        # Create paragraph block (keeping the text with inline elements)
        self.blocks.append(Block(
            text=text,
            block_type="paragraph",
            source_line=start_line
        ))

    def _collect_list(
        self, lines: List[str], start_idx: int
    ) -> Tuple[List[str], str, int]:
        """Collect all items in a list including nested items.

        This collects only items of the same type (ordered or unordered).
        A different list type at the same indent level ends the current list.

        Returns:
            Tuple of (list_items, list_type, lines_consumed)
        """
        items: List[str] = []
        list_type: Optional[str] = None
        i = start_idx
        current_item_lines: List[str] = []
        base_indent: Optional[int] = None

        while i < len(lines):
            line = lines[i]

            # Check if it's a list item line
            unordered_match = re.match(r'^([ \t]*)[-*+]\s+(.+)$', line)
            ordered_match = re.match(r'^([ \t]*)(\d+)[.)]\s+(.+)$', line)

            if unordered_match:
                indent = len(unordered_match.group(1).replace('\t', '    '))
                content = unordered_match.group(2)

                if base_indent is None:
                    base_indent = indent
                    list_type = "unordered"
                elif list_type == "ordered" and indent == base_indent:
                    # Different list type at same level - end this list
                    break

                # Flush previous item
                if current_item_lines:
                    items.append('\n'.join(current_item_lines))

                current_item_lines = [content]
                i += 1

            elif ordered_match:
                indent = len(ordered_match.group(1).replace('\t', '    '))
                content = ordered_match.group(3)

                if base_indent is None:
                    base_indent = indent
                    list_type = "ordered"
                elif list_type == "unordered" and indent == base_indent:
                    # Different list type at same level - end this list
                    break

                # Flush previous item
                if current_item_lines:
                    items.append('\n'.join(current_item_lines))

                current_item_lines = [content]
                i += 1

            elif line.strip() == '':
                # Blank line might continue the list or end it
                # Look ahead to see if list continues with SAME type
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    next_unordered = re.match(r'^[ \t]*[-*+]\s', next_line)
                    next_ordered = re.match(r'^[ \t]*\d+[.)]\s', next_line)

                    # Only continue if same list type or continuation indent
                    if (list_type == "unordered" and next_unordered) or \
                       (list_type == "ordered" and next_ordered) or \
                       (next_line.startswith('    ') or next_line.startswith('\t')):
                        current_item_lines.append('')
                        i += 1
                        continue
                # End of list
                break

            elif line.startswith('    ') or line.startswith('\t'):
                # Continuation of current item (multi-line item)
                # Remove one level of indentation
                dedented = re.sub(r'^(    |\t)', '', line)
                current_item_lines.append(dedented)
                i += 1

            else:
                # End of list
                break

        # Flush last item
        if current_item_lines:
            items.append('\n'.join(current_item_lines))

        return items, list_type or "unordered", i - start_idx


def extract_sections_from_markdown(
    md_content: str, source_path: str
) -> List[Section]:
    """Extract sections from Markdown content.

    Uses MarkdownExtractor to parse the Markdown and extracts ALL headings
    as individual sections. Returns a flat list of all sections for comparison.

    Args:
        md_content: The Markdown content to parse.
        source_path: Path to the source file (for reference).

    Returns:
        Flat list of Section objects, one for each heading in the document.
    """
    extractor = MarkdownExtractor()
    blocks = extractor.extract(md_content)

    # Build flat list of all sections (one per heading)
    all_sections: List[Section] = []
    section_stack: List[Section] = []  # Stack to track hierarchy for parent refs

    # Track current section for content accumulation
    current_section: Optional[Section] = None
    pending_blocks: List[Block] = []

    for block in blocks:
        # Check if block is a heading
        if block.block_type == BlockType.HEADING:
            level = block.level or 1
            text = block.text or ""
            anchor = block.anchor or generate_anchor(text)
            number, title = _extract_section_number(text)

            # Use anchor format for key (lowercase, hyphens) for MkDocs matching
            key = anchor

            # Create new section with blocks list for content
            new_section = Section(
                title=title,
                key=key,
                level=level,
                number=number if number else "",
                content="",
                source_type="markdown",
                source_path=source_path,
                anchor=anchor,
                line_number=block.source_line
            )

            # Pop sections from stack until we find parent (lower level)
            while section_stack and section_stack[-1].level >= level:
                section_stack.pop()

            if section_stack:
                # Set parent reference
                parent = section_stack[-1]
                new_section.parent = parent
                parent.children.append(new_section)

            # Add to flat list and push onto stack
            all_sections.append(new_section)
            section_stack.append(new_section)
            current_section = new_section
            pending_blocks = []

        else:
            # Accumulate content and blocks for current section
            if current_section:
                # Add to content string
                block_text = block.text or block.content or ""
                if block_text:
                    if current_section.content:
                        current_section.content += '\n\n' + block_text
                    else:
                        current_section.content = block_text
                # Add block to blocks list
                current_section.blocks.append(block)
            else:
                pending_blocks.append(block)

    # If there's content before any heading, create a preamble section
    if pending_blocks:
        preamble_content = '\n\n'.join(
            (b.text or b.content or "") for b in pending_blocks if (b.text or b.content)
        )
        if preamble_content:
            preamble_section = Section(
                title="",
                key="_preamble",
                level=0,
                content=preamble_content,
                source_type="markdown",
                source_path=source_path,
                blocks=pending_blocks
            )
            all_sections.insert(0, preamble_section)

    return all_sections


def extract_from_directory(dir_path: str) -> Dict[str, List[Section]]:
    """Recursively extract sections from all Markdown files in a directory.

    Args:
        dir_path: Path to the directory to scan.

    Returns:
        Dict mapping file paths (relative to dir_path) to lists of sections.
    """
    results: Dict[str, List[Section]] = {}

    for root, dirs, files in os.walk(dir_path):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]

        for filename in files:
            if filename.endswith('.md'):
                filepath = os.path.join(root, filename)
                rel_path = os.path.relpath(filepath, dir_path)

                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    sections = extract_sections_from_markdown(content, rel_path)
                    results[rel_path] = sections
                except Exception as e:
                    # Log error but continue processing other files
                    print(f"Warning: Error processing {rel_path}: {e}")

    return results


def extract_links_from_content(content: str) -> List[Tuple[str, str]]:
    """Extract all links from Markdown content.

    Args:
        content: The Markdown content.

    Returns:
        List of (text, href) tuples.
    """
    return MarkdownExtractor.LINK_PATTERN.findall(content)


def extract_images_from_content(content: str) -> List[Tuple[str, str]]:
    """Extract all images from Markdown content.

    Args:
        content: The Markdown content.

    Returns:
        List of (alt_text, src) tuples.
    """
    return MarkdownExtractor.IMAGE_PATTERN.findall(content)


def extract_inline_code_from_content(content: str) -> List[str]:
    """Extract all inline code spans from content.

    Args:
        content: The Markdown content.

    Returns:
        List of code snippets.
    """
    return MarkdownExtractor.INLINE_CODE_PATTERN.findall(content)
