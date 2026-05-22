"""Enable running docdiff as a module: python -m docdiff"""

import sys

from docdiff.cli import main

if __name__ == "__main__":
    sys.exit(main())
