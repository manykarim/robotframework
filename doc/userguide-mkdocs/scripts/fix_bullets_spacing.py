#!/usr/bin/env python3
"""Fix bullet spacing - ensure each bullet is on a new line."""

import re

def fix_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Fix bullets that are concatenated without <br>
    # Pattern: .• ` (period followed by bullet followed by backtick - indicating new attribute)
    content = re.sub(r'\.• `', '.<br>• `', content)

    # Fix other patterns where bullet follows text without <br>
    # Pattern: text• ` where text doesn't end with <br>
    content = re.sub(r'([^>])• `', r'\1<br>• `', content)

    # Clean up any double <br>
    content = re.sub(r'<br><br>•', '<br>•', content)

    with open(filepath, 'w') as f:
        f.write(content)

    print(f"Fixed {filepath}")


if __name__ == '__main__':
    fix_file('/home/many/workspace/robotframework/doc/userguide-mkdocs/docs/extending/listener-interface.md')
