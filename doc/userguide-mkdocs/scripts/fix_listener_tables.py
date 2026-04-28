#!/usr/bin/env python3
"""Fix Markdown tables with continuation rows by consolidating into single rows."""

import re
from pathlib import Path

def consolidate_table(lines):
    """Consolidate continuation rows into single rows with <br> tags."""
    result = []
    current_method = None
    current_args = None
    current_docs = []

    for line in lines:
        line = line.rstrip()

        # Skip empty lines
        if not line.strip():
            continue

        # Header row or separator
        if line.startswith('|') and ('Method' in line or '---' in line):
            if current_method:
                # Flush previous method
                doc_text = '<br>'.join(current_docs) if current_docs else ''
                result.append(f"| {current_method} | {current_args} | {doc_text} |")
                current_method = None
                current_args = None
                current_docs = []
            result.append(line)
            continue

        # Parse table row
        if line.startswith('|'):
            parts = [p.strip() for p in line.split('|')]
            # parts[0] is empty (before first |), parts[-1] is empty (after last |)
            if len(parts) >= 4:
                method = parts[1].strip()
                args = parts[2].strip()
                doc = parts[3].strip() if len(parts) > 3 else ''

                if method:  # New method row
                    # Flush previous method
                    if current_method:
                        doc_text = '<br>'.join(current_docs) if current_docs else ''
                        result.append(f"| {current_method} | {current_args} | {doc_text} |")

                    current_method = method
                    current_args = args
                    current_docs = [doc] if doc else []
                else:  # Continuation row
                    if doc:
                        current_docs.append(doc)

    # Flush last method
    if current_method:
        doc_text = '<br>'.join(current_docs) if current_docs else ''
        result.append(f"| {current_method} | {current_args} | {doc_text} |")

    return result


def fix_listener_interface(filepath):
    """Fix the listener-interface.md file tables."""
    with open(filepath, 'r') as f:
        content = f.read()

    lines = content.split('\n')

    # Find table sections
    result = []
    in_table = False
    table_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # Detect start of table (header row with Method)
        if '|' in line and ('Method' in line and 'Arguments' in line and 'Documentation' in line):
            in_table = True
            table_lines = [line]
            i += 1
            continue

        if in_table:
            # Still in table if line starts with |
            if line.strip().startswith('|'):
                table_lines.append(line)
                i += 1
                continue
            else:
                # End of table - consolidate and add
                consolidated = consolidate_table(table_lines)
                result.extend(consolidated)
                result.append('')  # Add blank line after table
                in_table = False
                table_lines = []
                result.append(line)
                i += 1
                continue

        result.append(line)
        i += 1

    # Handle table at end of file
    if in_table and table_lines:
        consolidated = consolidate_table(table_lines)
        result.extend(consolidated)

    return '\n'.join(result)


if __name__ == '__main__':
    filepath = '/home/many/workspace/robotframework/doc/userguide-mkdocs/docs/extending/listener-interface.md'
    new_content = fix_listener_interface(filepath)

    # Write output
    with open(filepath, 'w') as f:
        f.write(new_content)

    print(f"Fixed {filepath}")
