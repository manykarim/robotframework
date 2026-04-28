#!/usr/bin/env python3
"""Fix bullet points in table cells by:
1. Removing broken HTML list tags
2. Converting * to • (Unicode bullet)
"""

import re

def fix_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Step 1: Remove all the broken HTML list tags
    content = re.sub(r'<ul><li>', '• ', content)
    content = re.sub(r'</li><li>', '• ', content)
    content = re.sub(r'</li></ul>', '', content)
    content = re.sub(r'<ul>', '', content)
    content = re.sub(r'</ul>', '', content)
    content = re.sub(r'<li>', '• ', content)
    content = re.sub(r'</li>', '', content)

    # Step 2: Convert any remaining * at start of bullet patterns to •
    # Pattern: <br>* `something` or <br>* text
    content = re.sub(r'<br>\* ', '<br>• ', content)

    # Step 3: Clean up any double bullets or spacing issues
    content = re.sub(r'• • ', '• ', content)
    content = re.sub(r'<br><br>• ', '<br>• ', content)

    # Step 4: Remove stray bullets that might have been created
    content = re.sub(r'\| • ', '| ', content)  # Don't start table cell with bullet

    with open(filepath, 'w') as f:
        f.write(content)

    print(f"Fixed {filepath}")


if __name__ == '__main__':
    fix_file('/home/many/workspace/robotframework/doc/userguide-mkdocs/docs/extending/listener-interface.md')
