"""HTML content extractor for the docdiff comparison tool.

This module provides a robust HTML parser using Python's stdlib html.parser
to extract structured content from Robot Framework User Guide HTML files.
"""

import html
import re
from html.parser import HTMLParser
from typing import Optional, Any

from ..models import Block, BlockType, Section


class HTMLContentExtractor(HTMLParser):
    """Parser that extracts structured content from HTML documentation.

    This parser extracts:
    - Headings (h1-h6) with their text, id/anchor, and level
    - Paragraphs as text blocks
    - Lists (ul, ol) with proper nesting levels
    - Code blocks (pre/code) preserving whitespace
    - Tables as matrix of cell contents
    - Admonitions/notes (div.note, div.warning, etc.)
    - Links with text and href
    - Images with src and alt text
    """

    # Tags that we track for content extraction
    HEADING_TAGS = {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}
    BLOCK_TAGS = {'p', 'pre', 'code', 'ul', 'ol', 'li', 'table', 'tr', 'td', 'th',
                  'div', 'blockquote', 'a', 'img'}
    INLINE_TAGS = {'em', 'strong', 'b', 'i', 'span', 'code', 'kbd', 'var', 'samp'}
    # Tags whose content we skip - only script and style have content we truly want to skip
    SKIP_TAGS = {'script', 'style'}
    # Tags that we ignore but don't skip their content (navigation, etc.)
    IGNORE_TAGS = {'nav', 'header', 'footer', 'aside', 'head', 'meta', 'link', 'svg', 'path'}

    # Admonition types to look for
    ADMONITION_CLASSES = {'note', 'warning', 'tip', 'important', 'caution',
                          'danger', 'error', 'hint', 'attention', 'admonition'}

    def __init__(self):
        super().__init__()
        self.reset_state()

    def reset_state(self):
        """Reset the parser state for a new document."""
        # Extracted content
        self.headings: list = []  # List of heading dicts
        self.blocks: list = []    # List of Block objects

        # Current parsing state
        self._tag_stack: list = []  # Stack of open tags
        self._current_text: list = []  # Accumulating text
        self._skip_tag: Optional[str] = None  # Currently skipping content of this tag

        # Code block state
        self._in_code = False
        self._code_text: list = []
        self._code_language: Optional[str] = None
        self._pending_code_language: Optional[str] = None  # Language from parent div
        self._in_pre = False

        # List state
        self._in_list = False
        self._list_stack: list = []  # Stack of (list_type, items)
        self._current_list_item: list = []

        # Table state
        self._in_table = False
        self._table_rows: list = []
        self._current_row: list = []
        self._current_cell: list = []
        self._in_header_row = False

        # Admonition state
        self._in_admonition = False
        self._admonition_type: Optional[str] = None
        self._admonition_text: list = []
        self._admonition_title: Optional[str] = None

        # Link state
        self._in_link = False
        self._link_href: Optional[str] = None
        self._link_text: list = []

        # Heading state
        self._in_heading = False
        self._heading_level = 0
        self._heading_anchor: Optional[str] = None
        self._heading_text: list = []

        # Line tracking
        self._current_line = 1

    def handle_starttag(self, tag: str, attrs: list):
        """Handle opening tags."""
        tag = tag.lower()
        attrs_dict = dict(attrs)

        # Track line numbers (approximate)
        self._update_line_number()

        # Skip script and style content entirely
        if tag in self.SKIP_TAGS:
            self._skip_tag = tag
            return

        # If we're skipping, ignore everything until the closing tag
        if self._skip_tag is not None:
            return

        # Ignore navigation/metadata tags but process their children
        if tag in self.IGNORE_TAGS:
            return

        self._tag_stack.append(tag)

        # Handle headings
        if tag in self.HEADING_TAGS:
            self._in_heading = True
            self._heading_level = int(tag[1])
            self._heading_anchor = attrs_dict.get('id') or attrs_dict.get('name')
            self._heading_text = []
            return

        # Handle code blocks
        if tag == 'pre':
            self._in_pre = True
            # Check for language class (e.g., language-python, highlight-python)
            class_attr = attrs_dict.get('class', '')
            lang = self._extract_language(class_attr)
            # Use pending language from parent div if available
            self._code_language = lang or self._pending_code_language
            self._code_text = []
            return

        if tag == 'code':
            if self._in_pre:
                # Part of a code block
                class_attr = attrs_dict.get('class', '')
                lang = self._extract_language(class_attr)
                if lang:
                    self._code_language = lang
            else:
                # Inline code - just track it
                self._in_code = True
            return

        # Handle lists
        if tag in ('ul', 'ol'):
            list_type = 'ordered' if tag == 'ol' else 'unordered'
            self._list_stack.append({'type': list_type, 'items': []})
            self._in_list = True
            return

        if tag == 'li':
            self._current_list_item = []
            return

        # Handle tables
        if tag == 'table':
            self._in_table = True
            self._table_rows = []
            return

        if tag == 'tr':
            self._current_row = []
            self._in_header_row = False
            return

        if tag in ('td', 'th'):
            self._current_cell = []
            if tag == 'th':
                self._in_header_row = True
            return

        # Handle admonitions (div.note, div.warning, etc.) and code block wrappers
        if tag == 'div':
            class_attr = attrs_dict.get('class', '')

            # Check for admonition
            admonition_type = self._detect_admonition(class_attr)
            if admonition_type:
                self._in_admonition = True
                self._admonition_type = admonition_type
                self._admonition_text = []
                self._admonition_title = None
                return

            # Check for code block wrapper with language (e.g., "language-python highlight")
            lang = self._extract_language(class_attr)
            if lang or 'highlight' in class_attr.lower():
                self._pending_code_language = lang
                return

        # Handle links
        if tag == 'a':
            self._in_link = True
            self._link_href = attrs_dict.get('href')
            self._link_text = []
            return

        # Handle images
        if tag == 'img':
            src = attrs_dict.get('src', '')
            alt = attrs_dict.get('alt', '')
            if src:
                block = Block(
                    block_type=BlockType.IMAGE,
                    content=f"![{alt}]({src})",
                    metadata={'src': src, 'alt': alt},
                    line_number=self._current_line
                )
                self.blocks.append(block)
            return

        # Handle paragraphs
        if tag == 'p':
            # Check if this is an admonition title
            class_attr = attrs_dict.get('class', '')
            if 'admonition-title' in class_attr and self._in_admonition:
                # Will be captured as admonition title
                pass
            return

    def handle_endtag(self, tag: str):
        """Handle closing tags."""
        tag = tag.lower()

        # Handle skip tags
        if self._skip_tag is not None:
            if tag == self._skip_tag:
                self._skip_tag = None
            return

        # Ignore navigation/metadata tags
        if tag in self.IGNORE_TAGS:
            return

        # Pop from tag stack
        if self._tag_stack and self._tag_stack[-1] == tag:
            self._tag_stack.pop()

        # Handle headings
        if tag in self.HEADING_TAGS and self._in_heading:
            text = self._normalize_text(''.join(self._heading_text))
            if text:
                self.headings.append({
                    'level': self._heading_level,
                    'text': text,
                    'anchor': self._heading_anchor,
                    'line': self._current_line
                })
                # Also create a heading block
                block = Block(
                    block_type=BlockType.HEADING,
                    content=text,
                    metadata={'level': self._heading_level, 'anchor': self._heading_anchor},
                    line_number=self._current_line
                )
                self.blocks.append(block)
            self._in_heading = False
            self._heading_text = []
            return

        # Handle code blocks
        if tag == 'pre' and self._in_pre:
            text = ''.join(self._code_text)
            if text.strip():
                block = Block(
                    block_type=BlockType.CODE,
                    content=text,
                    metadata={'language': self._code_language},
                    line_number=self._current_line
                )
                self.blocks.append(block)
            self._in_pre = False
            self._code_text = []
            self._code_language = None
            return

        if tag == 'code' and not self._in_pre:
            self._in_code = False
            return

        # Handle lists
        if tag in ('ul', 'ol') and self._list_stack:
            list_data = self._list_stack.pop()
            if list_data['items']:
                content = '\n'.join(
                    item if isinstance(item, str) else str(item)
                    for item in list_data['items']
                )
                block = Block(
                    block_type=BlockType.LIST,
                    content=content,
                    metadata={
                        'type': list_data['type'],
                        'items': list_data['items'],
                        'level': len(self._list_stack)
                    },
                    line_number=self._current_line
                )
                if self._list_stack:
                    # Nested list - add to parent
                    self._list_stack[-1]['items'].append(block)
                else:
                    self.blocks.append(block)
            self._in_list = bool(self._list_stack)
            return

        if tag == 'li' and self._list_stack:
            item_text = self._normalize_text(''.join(self._current_list_item))
            if item_text:
                self._list_stack[-1]['items'].append(item_text)
            self._current_list_item = []
            return

        # Handle tables
        if tag == 'table' and self._in_table:
            if self._table_rows:
                content = '\n'.join(' | '.join(row) for row in self._table_rows)
                block = Block(
                    block_type=BlockType.TABLE,
                    content=content,
                    metadata={'rows': len(self._table_rows), 'data': self._table_rows},
                    line_number=self._current_line
                )
                self.blocks.append(block)
            self._in_table = False
            self._table_rows = []
            return

        if tag == 'tr' and self._in_table:
            if self._current_row:
                self._table_rows.append(self._current_row)
            self._current_row = []
            return

        if tag in ('td', 'th') and self._in_table:
            cell_text = self._normalize_text(''.join(self._current_cell))
            self._current_row.append(cell_text)
            self._current_cell = []
            return

        # Handle admonitions
        if tag == 'div' and self._in_admonition:
            # Check if we're closing the admonition div
            admonition_depth = sum(1 for t in self._tag_stack if t == 'div')
            if admonition_depth == 0:
                text = self._normalize_text(''.join(self._admonition_text))
                if text or self._admonition_title:
                    full_text = f"{self._admonition_title}\n{text}" if self._admonition_title else text
                    block = Block(
                        block_type=BlockType.ADMONITION,
                        content=full_text,
                        metadata={'type': self._admonition_type},
                        line_number=self._current_line
                    )
                    self.blocks.append(block)
                self._in_admonition = False
                self._admonition_text = []
                self._admonition_type = None
                self._admonition_title = None
            return

        # Handle links
        if tag == 'a' and self._in_link:
            text = self._normalize_text(''.join(self._link_text))
            if text and self._link_href:
                block = Block(
                    block_type=BlockType.LINK,
                    content=f"[{text}]({self._link_href})",
                    metadata={'href': self._link_href, 'text': text},
                    line_number=self._current_line
                )
                self.blocks.append(block)
            self._in_link = False
            self._link_text = []
            self._link_href = None
            return

        # Handle paragraphs
        if tag == 'p':
            text = self._normalize_text(''.join(self._current_text))
            if text and not self._in_admonition and not self._in_list and not self._in_table:
                block = Block(
                    block_type=BlockType.PARAGRAPH,
                    content=text,
                    metadata={},
                    line_number=self._current_line
                )
                self.blocks.append(block)
            self._current_text = []
            return

        # Handle div closing for code language reset
        if tag == 'div':
            self._pending_code_language = None

    def handle_data(self, data: str):
        """Handle text content."""
        if self._skip_tag is not None:
            return

        # Route text to appropriate collector
        if self._in_heading:
            self._heading_text.append(data)
        elif self._in_pre:
            self._code_text.append(data)
        elif self._in_link:
            self._link_text.append(data)
        elif self._in_list and self._current_list_item is not None:
            self._current_list_item.append(data)
        elif self._in_table:
            self._current_cell.append(data)
        elif self._in_admonition:
            self._admonition_text.append(data)
        else:
            self._current_text.append(data)

    def handle_entityref(self, name: str):
        """Handle named character references like &nbsp;"""
        char = html.unescape(f'&{name};')
        self.handle_data(char)

    def handle_charref(self, name: str):
        """Handle numeric character references like &#160;"""
        if name.startswith('x'):
            char = chr(int(name[1:], 16))
        else:
            char = chr(int(name))
        self.handle_data(char)

    def _extract_language(self, class_attr: str) -> Optional[str]:
        """Extract programming language from class attribute."""
        if not class_attr:
            return None

        # Common patterns: language-python, highlight-python, lang-python
        patterns = [
            r'language-(\w+)',
            r'highlight-(\w+)',
            r'lang-(\w+)',
            r'brush:\s*(\w+)',
            r'sourceCode\s+(\w+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, class_attr, re.IGNORECASE)
            if match:
                lang = match.group(1).lower()
                # Normalize common language names
                lang_map = {
                    'robotframework': 'robotframework',
                    'robot': 'robotframework',
                    'py': 'python',
                    'js': 'javascript',
                    'ts': 'typescript',
                    'rb': 'ruby',
                    'sh': 'bash',
                    'shell': 'bash',
                    'text': None,  # Plain text
                }
                return lang_map.get(lang, lang)

        return None

    def _detect_admonition(self, class_attr: str) -> Optional[str]:
        """Detect if a div is an admonition and return its type."""
        if not class_attr:
            return None

        classes = class_attr.lower().split()
        for cls in classes:
            if cls in self.ADMONITION_CLASSES:
                return cls

        # Check for mkdocs-material style admonitions
        if 'admonition' in classes:
            for cls in classes:
                if cls not in ('admonition', 'inline', 'end'):
                    return cls

        return None

    def _normalize_text(self, text: str) -> str:
        """Normalize text by collapsing whitespace and stripping."""
        # Decode any remaining entities
        text = html.unescape(text)
        # Remove pilcrow/paragraph symbols (often used for header links)
        text = text.replace('\u00b6', '')  # Pilcrow
        text = text.replace('\u00a7', '')  # Section sign
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text)
        # Strip leading/trailing whitespace
        return text.strip()

    def _update_line_number(self):
        """Approximate line number tracking."""
        pos = self.getpos()
        if pos:
            self._current_line = pos[0]

    def extract(self, html_content: str) -> list:
        """Extract sections from HTML content.

        Args:
            html_content: The HTML content to parse.

        Returns:
            List of Section objects.
        """
        self.reset_state()
        try:
            self.feed(html_content)
        except Exception:
            # Be lenient with malformed HTML
            pass

        return _build_section_hierarchy(self.headings, self.blocks)


def extract_sections_from_html(html_content: str) -> list:
    """Extract sections from HTML content.

    This function parses HTML and builds a hierarchy of Section objects
    based on heading levels.

    Args:
        html_content: The HTML content to parse.

    Returns:
        List of top-level Section objects with nested children.
    """
    parser = HTMLContentExtractor()
    return parser.extract(html_content)


def _build_section_hierarchy(headings: list, blocks: list) -> list:
    """Build a section hierarchy from extracted headings and blocks.

    Args:
        headings: List of heading dictionaries with level, text, anchor, line.
        blocks: List of Block objects.

    Returns:
        List of top-level Section objects.
    """
    if not headings:
        # No headings - create a single section with all blocks
        if blocks:
            return [Section(
                number="",
                title="(Document)",
                level=0,
                key="document",
                blocks=blocks,
                line_number=1
            )]
        return []

    # Create sections from headings
    sections_flat: list = []
    for heading in headings:
        # Extract section number from title if present
        title = heading['text']
        number, clean_title = _extract_section_number(title)

        section = Section(
            number=number or "",
            title=clean_title,
            level=heading['level'],
            key=_normalize_key(clean_title),
            blocks=[],
            line_number=heading.get('line')
        )

        sections_flat.append({
            'section': section,
            'heading': heading,
            'blocks': []
        })

    # Assign blocks to sections based on position
    blocks_by_line = sorted(blocks, key=lambda b: b.line_number or 0)
    headings_sorted = sorted(headings, key=lambda h: h.get('line', 0))

    current_section_idx = -1
    for block in blocks_by_line:
        block_line = block.line_number or 0

        # Find which section this block belongs to
        for i, h in enumerate(headings_sorted):
            h_line = h.get('line', 0)
            if block_line >= h_line:
                current_section_idx = i
            else:
                break

        if current_section_idx >= 0 and current_section_idx < len(sections_flat):
            # Skip heading blocks (they're already captured as sections)
            if block.block_type != BlockType.HEADING:
                sections_flat[current_section_idx]['blocks'].append(block)

    # Assign blocks to sections
    for item in sections_flat:
        item['section'].blocks = item['blocks']

    # Build hierarchy
    root_sections: list = []
    section_stack: list = []  # Stack of (level, section) for building hierarchy

    for item in sections_flat:
        section = item['section']
        level = section.level

        # Find parent by popping sections of equal or higher level
        while section_stack and section_stack[-1][0] >= level:
            section_stack.pop()

        if section_stack:
            # Add as child of parent
            parent_section = section_stack[-1][1]
            section.parent = parent_section
            parent_section.subsections.append(section)
        else:
            # Top-level section
            root_sections.append(section)

        section_stack.append((level, section))

    return root_sections


def _extract_section_number(title: str) -> tuple:
    """Extract section number prefix from title.

    Args:
        title: The section title text.

    Returns:
        Tuple of (number, clean_title) where number may be None.
    """
    # Match patterns like "2.1.3 Section Title" or "2.1.3. Section Title"
    match = re.match(r'^(\d+(?:\.\d+)*\.?)\s+(.+)$', title)
    if match:
        number = match.group(1).rstrip('.')
        clean_title = match.group(2)
        return number, clean_title
    return None, title


def _normalize_key(text: str) -> str:
    """Generate a normalized key from text for section matching.

    Args:
        text: The text to normalize.

    Returns:
        A lowercase key with special characters removed and spaces as hyphens.
    """
    # Remove section numbers
    text = re.sub(r'^\d+(\.\d+)*\.?\s*', '', text)
    # Convert to lowercase
    text = text.lower()
    # Remove special characters except spaces and hyphens
    text = re.sub(r'[^\w\s-]', '', text)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Replace spaces with hyphens
    text = text.replace(' ', '-')
    return text


def extract_from_file(filepath: str) -> list:
    """Extract sections from an HTML file.

    Args:
        filepath: Path to the HTML file to parse.

    Returns:
        List of Section objects representing the document structure.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        IOError: If the file cannot be read.
    """
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        html_content = f.read()

    return extract_sections_from_html(html_content)
