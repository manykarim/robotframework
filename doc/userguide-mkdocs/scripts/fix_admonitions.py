#!/usr/bin/env python3
"""
Fix truncated admonitions in converted Robot Framework User Guide Markdown files.

Problem: During RST to MD conversion, many admonitions were truncated because:
1. Inline admonitions (content starting on same line as directive) lost their first line
2. Only continuation lines were captured, with wrong indentation
3. Some admonitions ended up completely empty

This script:
1. Parses original RST files to extract full admonition content
2. Matches MD admonitions to RST by sequential order (same type, same position)
3. Replaces truncated content with properly formatted content (4-space indentation)

Usage:
    python fix_admonitions.py [--dry-run] [--verbose]
"""

import argparse
import re
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class Admonition:
    """Represents an admonition found in a document."""
    type: str
    content: str
    line_number: int
    raw_lines: List[str] = None  # Original lines for reference


# RST to Markdown directory mapping
RST_TO_MD_MAP = {
    'ExtendingRobotFramework/CreatingTestLibraries.rst': 'extending/creating-test-libraries.md',
    'ExtendingRobotFramework/ListenerInterface.rst': 'extending/listener-interface.md',
    'ExtendingRobotFramework/ParserInterface.rst': 'extending/parser-interface.md',
    'ExtendingRobotFramework/RemoteLibrary.rst': 'extending/remote-library.md',
    'CreatingTestData/TestDataSyntax.rst': 'creating-test-data/test-data-syntax.md',
    'CreatingTestData/CreatingTestCases.rst': 'creating-test-data/creating-test-cases.md',
    'CreatingTestData/CreatingUserKeywords.rst': 'creating-test-data/creating-user-keywords.md',
    'CreatingTestData/ResourceAndVariableFiles.rst': 'creating-test-data/resource-and-variable-files.md',
    'CreatingTestData/VariableSection.rst': 'creating-test-data/variable-section.md',
    'CreatingTestData/AdvancedFeatures.rst': 'creating-test-data/advanced-features.md',
    'ExecutingTestCases/ConfiguringExecution.rst': 'executing-tests/configuring-execution.md',
    'ExecutingTestCases/TestExecution.rst': 'executing-tests/test-execution.md',
    'ExecutingTestCases/OutputFiles.rst': 'executing-tests/output-files.md',
    'ExecutingTestCases/PostProcessingOutputs.rst': 'executing-tests/post-processing-outputs.md',
    'GettingStarted/Introduction.rst': 'getting-started/introduction.md',
    'Appendices/BooleanArguments.rst': 'appendices/boolean-arguments.md',
    'Appendices/CommandLineOptions.rst': 'appendices/command-line-options.md',
    'Appendices/DocumentationFormatting.rst': 'appendices/documentation-formatting.md',
    'Appendices/TimeFormat.rst': 'appendices/time-format.md',
    'Appendices/Translations.rst': 'appendices/translations.md',
    'SupportingTools/Libdoc.rst': 'supporting-tools/libdoc.md',
    'SupportingTools/Testdoc.rst': 'supporting-tools/testdoc.md',
}

# RST admonition type -> MD admonition type
ADMON_TYPE_MAP = {
    'note': 'note',
    'warning': 'warning',
    'tip': 'tip',
    'important': 'important',
    'caution': 'warning',
    'danger': 'danger',
    'attention': 'warning',
    'hint': 'tip',
}

# Reverse mapping for MD -> possible RST types
MD_TO_RST_TYPES = defaultdict(list)
for rst, md in ADMON_TYPE_MAP.items():
    MD_TO_RST_TYPES[md].append(rst)


class AdmonitionFixer:
    """Fix truncated admonitions by cross-referencing with original RST."""

    def __init__(self, rst_dir: Path, md_dir: Path, verbose: bool = False):
        self.rst_dir = rst_dir
        self.md_dir = md_dir
        self.verbose = verbose
        self.stats = {
            'files_processed': 0,
            'admonitions_found_rst': 0,
            'admonitions_found_md': 0,
            'truncated_fixed': 0,
            'empty_fixed': 0,
            'already_correct': 0,
            'unmatched': 0,
        }

    def extract_rst_admonitions(self, rst_content: str) -> List[Admonition]:
        """Extract all admonitions from RST content with their full text."""
        admonitions = []
        lines = rst_content.split('\n')

        i = 0
        while i < len(lines):
            line = lines[i]

            # Match RST admonition directive: .. type:: [optional inline content]
            match = re.match(r'^\.\.\s+(note|warning|tip|important|caution|danger|attention|hint)::\s*(.*?)$',
                           line, re.IGNORECASE)

            if match:
                rst_type = match.group(1).lower()
                md_type = ADMON_TYPE_MAP.get(rst_type, rst_type)
                inline_content = match.group(2).strip()
                content_lines = []
                raw_lines = [line]

                if inline_content:
                    content_lines.append(inline_content)

                # Collect continuation lines (indented lines following)
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]

                    # Empty line might be part of content or end of admonition
                    if not next_line.strip():
                        # Check if more indented content follows
                        if j + 1 < len(lines) and lines[j + 1].startswith((' ', '\t')) and lines[j + 1].strip():
                            content_lines.append('')
                            raw_lines.append(next_line)
                            j += 1
                            continue
                        else:
                            break

                    # If line is indented, it's continuation
                    if next_line.startswith((' ', '\t')):
                        content_lines.append(next_line.strip())
                        raw_lines.append(next_line)
                        j += 1
                    else:
                        break

                # Build the full content, preserving paragraph breaks
                full_content = self._join_content_lines(content_lines)

                admonitions.append(Admonition(
                    type=md_type,
                    content=full_content,
                    line_number=i + 1,
                    raw_lines=raw_lines
                ))
                self.stats['admonitions_found_rst'] += 1

                i = j
            else:
                i += 1

        return admonitions

    def _join_content_lines(self, content_lines: List[str]) -> str:
        """Join content lines, preserving paragraph structure."""
        if not content_lines:
            return ""

        # Join lines, collapsing multiple spaces but preserving paragraph breaks
        result = []
        current_para = []

        for line in content_lines:
            if not line:
                if current_para:
                    result.append(' '.join(current_para))
                    current_para = []
            else:
                current_para.append(line)

        if current_para:
            result.append(' '.join(current_para))

        return '\n\n'.join(result)

    def extract_md_admonitions(self, md_content: str) -> List[Tuple[int, int, str, str, bool]]:
        """
        Extract admonitions from MD content.
        Returns: List of (start_line, end_line, type, current_content, is_truncated)
        """
        admonitions = []
        lines = md_content.split('\n')

        i = 0
        while i < len(lines):
            line = lines[i]

            # Match MkDocs admonition: !!! type
            match = re.match(r'^!!!\s+(\w+)\s*$', line)
            if match:
                admon_type = match.group(1)
                content_lines = []
                start_line = i

                # Collect content lines
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]

                    if not next_line.strip():
                        # Empty line - check if more indented content follows
                        if j + 1 < len(lines) and lines[j + 1].startswith((' ', '\t')) and lines[j + 1].strip():
                            content_lines.append('')
                            j += 1
                            continue
                        else:
                            break
                    elif next_line.startswith((' ', '\t')):
                        content_lines.append(next_line)
                        j += 1
                    else:
                        break

                end_line = j
                current_content = '\n'.join(content_lines)

                # Detect if truncated
                is_truncated = self._is_truncated(content_lines)

                admonitions.append((start_line, end_line, admon_type, current_content, is_truncated))
                self.stats['admonitions_found_md'] += 1

                i = j
            else:
                i += 1

        return admonitions

    def _is_truncated(self, content_lines: List[str]) -> bool:
        """Check if admonition content appears to be truncated."""
        if not content_lines:
            # Completely empty
            return True

        first_line = content_lines[0] if content_lines else ""
        if not first_line.strip():
            return True

        # Check indentation - should be exactly 4 spaces
        indent = len(first_line) - len(first_line.lstrip())
        if indent != 4:
            return True

        # Check if content looks like a sentence fragment (starts with lowercase, suggesting missing beginning)
        stripped = first_line.strip()
        if stripped:
            # Starts with lowercase and not a typical starting word
            if stripped[0].islower():
                # Allow certain patterns that legitimately start lowercase
                if not re.match(r'^(a |an |the |if |when |for |to |or |and |e\.g\.|i\.e\.)', stripped, re.I):
                    return True

            # Starts with punctuation that suggests continuation
            if stripped[0] in ',;:)]}':
                return True

        return False

    def format_admonition_content(self, content: str) -> List[str]:
        """Format content with proper 4-space indentation."""
        if not content:
            return []

        output_lines = []
        paragraphs = content.split('\n\n')

        for para_idx, paragraph in enumerate(paragraphs):
            # Clean up paragraph
            paragraph = re.sub(r'\s+', ' ', paragraph.strip())

            if not paragraph:
                continue

            # Wrap at ~76 chars (80 - 4 for indent)
            words = paragraph.split()
            current_line = []
            current_length = 0

            for word in words:
                if current_length + len(word) + 1 > 76 and current_line:
                    output_lines.append('    ' + ' '.join(current_line))
                    current_line = [word]
                    current_length = len(word)
                else:
                    current_line.append(word)
                    current_length += len(word) + (1 if current_line else 0)

            if current_line:
                output_lines.append('    ' + ' '.join(current_line))

            # Add blank line between paragraphs
            if para_idx < len(paragraphs) - 1:
                output_lines.append('')

        return output_lines

    def fix_file(self, rst_path: Path, md_path: Path, dry_run: bool = False) -> int:
        """Fix admonitions in a single MD file using RST as reference."""
        if not rst_path.exists():
            if self.verbose:
                print(f"  Warning: RST file not found: {rst_path}")
            return 0

        if not md_path.exists():
            if self.verbose:
                print(f"  Warning: MD file not found: {md_path}")
            return 0

        rst_content = rst_path.read_text(encoding='utf-8')
        md_content = md_path.read_text(encoding='utf-8')

        rst_admons = self.extract_rst_admonitions(rst_content)
        md_admons = self.extract_md_admonitions(md_content)

        if self.verbose:
            print(f"  Found {len(rst_admons)} RST admonitions, {len(md_admons)} MD admonitions")

        # Match admonitions by sequential order within each type
        # Group by type
        rst_by_type = defaultdict(list)
        for admon in rst_admons:
            rst_by_type[admon.type].append(admon)

        md_by_type = defaultdict(list)
        for admon in md_admons:
            md_by_type[admon[2]].append(admon)

        fixes = []
        for admon_type in md_by_type:
            md_list = md_by_type[admon_type]
            rst_list = rst_by_type.get(admon_type, [])

            if len(md_list) != len(rst_list):
                if self.verbose:
                    print(f"    Warning: Type '{admon_type}' count mismatch: {len(md_list)} MD vs {len(rst_list)} RST")

            # Match by position in sequence
            for idx, md_admon in enumerate(md_list):
                start_line, end_line, mtype, current_content, is_truncated = md_admon

                if not is_truncated:
                    self.stats['already_correct'] += 1
                    continue

                if idx < len(rst_list):
                    rst_match = rst_list[idx]
                    new_content_lines = self.format_admonition_content(rst_match.content)

                    if not current_content.strip():
                        self.stats['empty_fixed'] += 1
                    else:
                        self.stats['truncated_fixed'] += 1

                    fixes.append((start_line, end_line, mtype, new_content_lines))

                    if self.verbose:
                        old_preview = current_content.replace('\n', ' ')[:50]
                        new_preview = ' '.join(new_content_lines)[:50] if new_content_lines else "(empty)"
                        print(f"    Line {start_line + 1}: {mtype}")
                        print(f"      OLD: {old_preview}...")
                        print(f"      NEW: {new_preview}...")
                else:
                    self.stats['unmatched'] += 1
                    if self.verbose:
                        print(f"    Line {start_line + 1}: {mtype} - NO RST MATCH")

        if fixes and not dry_run:
            # Apply fixes to the file
            lines = md_content.split('\n')

            # Sort fixes in reverse order to not invalidate line numbers
            for start_line, end_line, admon_type, new_content_lines in sorted(fixes, key=lambda x: x[0], reverse=True):
                # Build replacement
                new_lines = [f'!!! {admon_type}']
                new_lines.extend(new_content_lines)

                # Replace lines
                lines = lines[:start_line] + new_lines + [''] + lines[end_line:]

            md_path.write_text('\n'.join(lines), encoding='utf-8')

        return len(fixes)

    def fix_all(self, dry_run: bool = False) -> None:
        """Fix admonitions in all mapped files."""
        print("Fixing truncated admonitions...")
        print(f"  RST source: {self.rst_dir}")
        print(f"  MD target: {self.md_dir}")
        print()

        total_fixes = 0

        for rst_rel, md_rel in RST_TO_MD_MAP.items():
            rst_path = self.rst_dir / rst_rel
            md_path = self.md_dir / md_rel

            print(f"Processing: {md_rel}")

            fixes = self.fix_file(rst_path, md_path, dry_run)
            total_fixes += fixes
            self.stats['files_processed'] += 1

            if fixes:
                print(f"  Fixed {fixes} admonitions")

        print()
        print("=" * 60)
        print("Summary:")
        print(f"  Files processed: {self.stats['files_processed']}")
        print(f"  RST admonitions found: {self.stats['admonitions_found_rst']}")
        print(f"  MD admonitions found: {self.stats['admonitions_found_md']}")
        print(f"  Empty admonitions fixed: {self.stats['empty_fixed']}")
        print(f"  Truncated admonitions fixed: {self.stats['truncated_fixed']}")
        print(f"  Already correct: {self.stats['already_correct']}")
        print(f"  Unmatched (no RST): {self.stats['unmatched']}")
        print(f"  Total fixes: {total_fixes}")

        if dry_run:
            print("\n  (DRY RUN - no files modified)")


def main():
    parser = argparse.ArgumentParser(description='Fix truncated admonitions in MD files')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without modifying files')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed output')
    parser.add_argument('--rst-dir', type=Path, help='RST source directory')
    parser.add_argument('--md-dir', type=Path, help='MD target directory')

    args = parser.parse_args()

    # Default paths relative to script location
    script_dir = Path(__file__).parent
    rst_dir = args.rst_dir or script_dir.parent.parent / "userguide" / "src"
    md_dir = args.md_dir or script_dir.parent / "docs"

    fixer = AdmonitionFixer(rst_dir, md_dir, verbose=args.verbose)
    fixer.fix_all(dry_run=args.dry_run)


if __name__ == '__main__':
    main()
