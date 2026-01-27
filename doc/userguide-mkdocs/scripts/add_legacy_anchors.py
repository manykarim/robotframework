#!/usr/bin/env python3
"""
Legacy Anchor Aliasing Script for Robot Framework User Guide Migration

This script adds invisible HTML anchor elements to MkDocs markdown files
to preserve backward compatibility with deep links from the legacy single-page
User Guide (RobotFrameworkUserGuide.html#AnchorName).

The anchors are added as HTML `<a id="AnchorName"></a>` elements just before
the relevant heading or section, allowing legacy URLs to continue working.

Usage:
    python add_legacy_anchors.py [--dry-run] [--verbose]

Options:
    --dry-run   Show what would be changed without modifying files
    --verbose   Print detailed information about changes
"""

import os
import re
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Mapping of legacy anchor names to:
# - file: the markdown file where the anchor should be placed
# - section: the heading text to match (case-insensitive)
# - aliases: list of anchor names that should point to this location
#
# Format: {
#     'primary_anchor': {
#         'file': 'relative/path/to/file.md',
#         'heading': 'Heading Text to Match',
#         'aliases': ['AltAnchor1', 'AltAnchor2']
#     }
# }

ANCHOR_MAPPINGS = {
    # Getting Started
    'Introduction': {
        'file': 'getting-started/introduction.md',
        'heading': 'Introduction',
        'aliases': []
    },
    'WhyRobotFramework': {
        'file': 'getting-started/introduction.md',
        'heading': 'Why Robot Framework',
        'aliases': ['Why Robot Framework?']
    },
    'High-levelarchitecture': {
        'file': 'getting-started/introduction.md',
        'heading': 'High-level architecture',
        'aliases': ['HighLevelArchitecture']
    },
    'Mailinglists': {
        'file': 'getting-started/introduction.md',
        'heading': 'Mailing lists',
        'aliases': ['mailing list']
    },
    'Installation': {
        'file': 'getting-started/installation.md',
        'heading': 'Installation',
        'aliases': ['Installationinstructions']
    },

    # Test Data Syntax
    'Testdatasyntax': {
        'file': 'creating-test-data/syntax.md',
        'heading': 'Test Data Syntax',
        'aliases': ['TestDataSyntax', 'general parsing rules']
    },
    'Testdatasections': {
        'file': 'creating-test-data/syntax.md',
        'heading': 'Test data sections',
        'aliases': ['Testdatatables', 'test data tables', 'section headers']
    },
    'Spaceseparatedformat': {
        'file': 'creating-test-data/syntax.md',
        'heading': 'Space separated format',
        'aliases': ['plain text format', 'space separated plain text format']
    },
    'Pipeseparatedformat': {
        'file': 'creating-test-data/syntax.md',
        'heading': 'Pipe separated format',
        'aliases': []
    },
    'reStructuredTextformat': {
        'file': 'creating-test-data/syntax.md',
        'heading': 'reStructuredText format',
        'aliases': []
    },
    'JSONformat': {
        'file': 'creating-test-data/syntax.md',
        'heading': 'JSON format',
        'aliases': []
    },
    'Escaping': {
        'file': 'creating-test-data/syntax.md',
        'heading': 'Escaping',
        'aliases': ['escape sequence', 'escape sequences']
    },
    'Localization': {
        'file': 'creating-test-data/syntax.md',
        'heading': 'Localization',
        'aliases': ['localized']
    },

    # Creating Test Cases
    'Creatingtestcases': {
        'file': 'creating-test-data/test-cases.md',
        'heading': 'Creating test cases',
        'aliases': ['Creating tests', 'test case', 'test cases']
    },
    'Testcasesyntax': {
        'file': 'creating-test-data/test-cases.md',
        'heading': 'Test case syntax',
        'aliases': []
    },
    'example-tests': {
        'file': 'creating-test-data/test-cases.md',
        'heading': 'Basic syntax',
        'aliases': []
    },
    'positional argument': {
        'file': 'creating-test-data/test-cases.md',
        'heading': 'Positional arguments',
        'aliases': ['Positionalarguments']
    },
    'varargs-usage': {
        'file': 'creating-test-data/test-cases.md',
        'heading': 'Variable number of arguments',
        'aliases': ['Variablenumberofarguments']
    },
    'named argument': {
        'file': 'creating-test-data/test-cases.md',
        'heading': 'Named arguments',
        'aliases': ['Namedarguments', 'named argument syntax']
    },
    'kwargs-usage': {
        'file': 'creating-test-data/test-cases.md',
        'heading': 'Free named arguments',
        'aliases': ['Freenamedarguments', 'free named argument examples']
    },
    'test case tags': {
        'file': 'creating-test-data/test-cases.md',
        'heading': 'Tagging test cases',
        'aliases': ['Taggingtestcases', 'tag', 'tags']
    },
    'Testsetupandteardown': {
        'file': 'creating-test-data/test-cases.md',
        'heading': 'Test setup and teardown',
        'aliases': ['test setup', 'test teardown', 'teardown', 'teardowns']
    },
    'Testtemplates': {
        'file': 'creating-test-data/test-cases.md',
        'heading': 'Test templates',
        'aliases': ['test template', 'template keyword']
    },
    'Keyword-drivenstyle': {
        'file': 'creating-test-data/test-cases.md',
        'heading': 'Keyword-driven style',
        'aliases': ['keyword-driven']
    },
    'Data-drivenstyle': {
        'file': 'creating-test-data/test-cases.md',
        'heading': 'Data-driven style',
        'aliases': ['data-driven', 'data-driven approach']
    },
    'Behavior-drivenstyle': {
        'file': 'creating-test-data/test-cases.md',
        'heading': 'Behavior-driven style',
        'aliases': []
    },

    # Creating Test Suites
    'Creatingtestsuites': {
        'file': 'creating-test-data/test-cases.md',
        'heading': 'Creating test suites',
        'aliases': ['test suite', 'test suites']
    },
    'Suitefiles': {
        'file': 'creating-test-data/test-cases.md',
        'heading': 'Suite files',
        'aliases': ['suite file']
    },
    'Suitedirectories': {
        'file': 'creating-test-data/test-cases.md',
        'heading': 'Suite directories',
        'aliases': ['suite directory']
    },
    'Suiteinitializationfiles': {
        'file': 'creating-test-data/test-cases.md',
        'heading': 'Suite initialization files',
        'aliases': ['initialization file', 'suite initialization file']
    },
    'Suitesetupandteardown': {
        'file': 'creating-test-data/test-cases.md',
        'heading': 'Suite setup and teardown',
        'aliases': ['suite setup', 'suite teardown']
    },

    # Using Test Libraries
    'Usingtestlibraries': {
        'file': 'creating-test-data/test-cases.md',
        'heading': 'Using test libraries',
        'aliases': ['test libraries', 'test library', 'libraries', 'library keyword', 'library keywords']
    },

    # Creating Tasks (RPA)
    'Creatingtasks': {
        'file': 'creating-test-data/tasks.md',
        'heading': 'Creating tasks',
        'aliases': ['rpa']
    },

    # Variables
    'Variables': {
        'file': 'creating-test-data/variables.md',
        'heading': 'Variables',
        'aliases': ['variable']
    },
    'scalar variable': {
        'file': 'creating-test-data/variables.md',
        'heading': 'Scalar variables',
        'aliases': ['Scalarvariables', 'scalar variables']
    },
    'list variable': {
        'file': 'creating-test-data/variables.md',
        'heading': 'List variables',
        'aliases': ['Listvariables', 'list variables', 'list expansion']
    },
    'dictionary variable': {
        'file': 'creating-test-data/variables.md',
        'heading': 'Dictionary variables',
        'aliases': ['Dictionaryvariables', 'dictionary variables', 'dictionary expansion']
    },
    'environment variable': {
        'file': 'creating-test-data/variables.md',
        'heading': 'Environment variables',
        'aliases': ['Environmentvariables']
    },
    'Variable sections': {
        'file': 'creating-test-data/variables.md',
        'heading': 'Variable section',
        'aliases': ['Variablesection', 'Variable table']
    },
    'built-in variable': {
        'file': 'creating-test-data/variables.md',
        'heading': 'Built-in variables',
        'aliases': ['Built-invariables']
    },
    'Automaticvariables': {
        'file': 'creating-test-data/variables.md',
        'heading': 'Automatic variables',
        'aliases': ['automatic variable']
    },
    'Extendedvariablesyntax': {
        'file': 'creating-test-data/variables.md',
        'heading': 'Extended variable syntax',
        'aliases': []
    },
    'inline Python evaluation': {
        'file': 'creating-test-data/variables.md',
        'heading': 'Inline Python evaluation',
        'aliases': ['InlinePythonevaluation']
    },

    # Creating User Keywords
    'Creatinguserkeywords': {
        'file': 'creating-test-data/keywords.md',
        'heading': 'Creating user keywords',
        'aliases': ['user keyword', 'user keywords', 'higher-level keywords']
    },
    'User keyword documentation': {
        'file': 'creating-test-data/keywords.md',
        'heading': 'User keyword documentation',
        'aliases': ['Userkeyworddocumentation']
    },
    'Embedded argument syntax': {
        'file': 'creating-test-data/keywords.md',
        'heading': 'Embedding arguments into keyword name',
        'aliases': ['Embeddingargumentsintokeywordname', 'Embeddedargumentsyntax']
    },
    'RETURN': {
        'file': 'creating-test-data/keywords.md',
        'heading': 'RETURN statement',
        'aliases': []
    },
    'Userkeywordtimeout': {
        'file': 'creating-test-data/keywords.md',
        'heading': 'User keyword timeout',
        'aliases': ['user keyword timeouts', 'keyword timeout']
    },

    # Control Structures
    'for': {
        'file': 'creating-test-data/keywords.md',
        'heading': 'FOR loops',
        'aliases': ['for loop', 'FORloops']
    },
    'WHILE': {
        'file': 'creating-test-data/keywords.md',
        'heading': 'WHILE loops',
        'aliases': ['WHILEloops']
    },
    'if': {
        'file': 'creating-test-data/keywords.md',
        'heading': 'IF/ELSE structures',
        'aliases': ['if/else', 'if/else structures', 'IF/ELSEstructures']
    },
    'inline if': {
        'file': 'creating-test-data/keywords.md',
        'heading': 'Inline IF',
        'aliases': ['InlineIF']
    },
    'try/except': {
        'file': 'creating-test-data/keywords.md',
        'heading': 'TRY/EXCEPT',
        'aliases': ['TRY/EXCEPT', 'tryexcept']
    },
    'BREAK': {
        'file': 'creating-test-data/keywords.md',
        'heading': 'BREAK and CONTINUE',
        'aliases': ['CONTINUE']
    },

    # Resource and Variable Files
    'Resourceandvariablefiles': {
        'file': 'creating-test-data/resource-files.md',
        'heading': 'Resource and variable files',
        'aliases': []
    },
    'Resourcefiles': {
        'file': 'creating-test-data/resource-files.md',
        'heading': 'Resource files',
        'aliases': []
    },
    'Variablefiles': {
        'file': 'creating-test-data/resource-files.md',
        'heading': 'Variable files',
        'aliases': []
    },

    # Advanced Features
    'library search order': {
        'file': 'creating-test-data/advanced.md',
        'heading': 'Library search order',
        'aliases': ['Librarysearchorder']
    },
    'Testcasetimeout': {
        'file': 'creating-test-data/advanced.md',
        'heading': 'Test case timeout',
        'aliases': ['test case timeouts', 'test timeout']
    },
    'continue on failure': {
        'file': 'creating-test-data/advanced.md',
        'heading': 'Continue on failure',
        'aliases': ['Continuingonfailure', 'Continueonfailure']
    },

    # Basic Usage
    'executing test cases': {
        'file': 'executing-tests/basic-usage.md',
        'heading': 'Starting test execution',
        'aliases': ['Executingtestcases', 'Startingtestexecution', 'test execution']
    },
    'wildcards': {
        'file': 'executing-tests/basic-usage.md',
        'heading': 'Simple patterns',
        'aliases': ['Simplepatterns', 'simple pattern']
    },
    'start-up script': {
        'file': 'executing-tests/basic-usage.md',
        'heading': 'Creating start-up scripts',
        'aliases': ['start-up scripts', 'Creatingstart-upscripts']
    },
    'Returncodes': {
        'file': 'executing-tests/basic-usage.md',
        'heading': 'Return codes',
        'aliases': ['return code']
    },
    'Errorsandwarningsduringexecution': {
        'file': 'executing-tests/basic-usage.md',
        'heading': 'Errors and warnings',
        'aliases': ['execution errors', 'test execution errors']
    },

    # Test Execution
    'skipped': {
        'file': 'executing-tests/test-execution.md',
        'heading': 'Skipping tests',
        'aliases': ['Skippingtests']
    },
    'executing tasks': {
        'file': 'executing-tests/test-execution.md',
        'heading': 'Task execution',
        'aliases': ['Taskexecution']
    },

    # Post-processing
    'rebot': {
        'file': 'executing-tests/post-processing.md',
        'heading': 'Using Rebot',
        'aliases': ['Post-processingoutputs', 'post-process outputs']
    },

    # Configuring Execution
    'module search path': {
        'file': 'executing-tests/configuration.md',
        'heading': 'Module search path',
        'aliases': ['Modulesearchpath']
    },
    'pre-run modifier': {
        'file': 'executing-tests/configuration.md',
        'heading': 'Pre-run modifier',
        'aliases': ['pre-run modifiers', 'Pre-runmodifier']
    },

    # Output Files
    'output.xml': {
        'file': 'executing-tests/output-files.md',
        'heading': 'Output file',
        'aliases': ['Outputfile', 'output', 'outputs', 'output files', 'XML output files']
    },
    'Logfile': {
        'file': 'executing-tests/output-files.md',
        'heading': 'Log file',
        'aliases': ['log', 'logs', 'log files', 'test logs']
    },
    'Reportfile': {
        'file': 'executing-tests/output-files.md',
        'heading': 'Report file',
        'aliases': ['report', 'reports', 'report files', 'test reports']
    },
    'xunit': {
        'file': 'executing-tests/output-files.md',
        'heading': 'XUnit compatible result file',
        'aliases': ['xunit file', 'XUnitcompatibleresultfile']
    },
    'Debugfile': {
        'file': 'executing-tests/output-files.md',
        'heading': 'Debug file',
        'aliases': ['debug files']
    },
    'Loglevels': {
        'file': 'executing-tests/output-files.md',
        'heading': 'Log levels',
        'aliases': ['log level']
    },
    'Systemlog': {
        'file': 'executing-tests/output-files.md',
        'heading': 'System log',
        'aliases': ['syslog']
    },
    'pre-Rebot modifier': {
        'file': 'executing-tests/output-files.md',
        'heading': 'Pre-Rebot modifier',
        'aliases': ['Pre-Rebotmodifier']
    },

    # Creating Test Libraries
    'Creatingtestlibraries': {
        'file': 'extending/library-api.md',
        'heading': 'Creating test libraries',
        'aliases': ['library API', 'static library API']
    },
    'Libraryscope': {
        'file': 'extending/library-api.md',
        'heading': 'Library scope',
        'aliases': []
    },
    'varargs-library': {
        'file': 'extending/library-api.md',
        'heading': 'Variable number of arguments',
        'aliases': []
    },
    'kwargs-library': {
        'file': 'extending/library-api.md',
        'heading': 'Free keyword arguments',
        'aliases': []
    },
    'Dynamic library': {
        'file': 'extending/library-api.md',
        'heading': 'Dynamic library API',
        'aliases': ['Dynamiclibraryapi']
    },
    'Getting dynamic keyword names': {
        'file': 'extending/library-api.md',
        'heading': 'Getting dynamic keyword names',
        'aliases': ['Gettingdynamickeywordnames']
    },
    'Running dynamic keywords': {
        'file': 'extending/library-api.md',
        'heading': 'Running dynamic keywords',
        'aliases': ['Runningdynamickeywords']
    },

    # Listener Interface
    'Listenerinterface': {
        'file': 'extending/listener-interface.md',
        'heading': 'Listener interface',
        'aliases': ['listener interface', 'listener', 'listeners']
    },
    'library listeners': {
        'file': 'extending/listener-interface.md',
        'heading': 'Libraries as listeners',
        'aliases': ['Librariesaslisteners']
    },

    # Supporting Tools
    'libdoc': {
        'file': 'supporting-tools/builtin-tools.md',
        'heading': 'Libdoc',
        'aliases': ['Libdoc']
    },
    'internal linking': {
        'file': 'supporting-tools/builtin-tools.md',
        'heading': 'Internal linking',
        'aliases': ['Internallinking']
    },
    'testdoc': {
        'file': 'supporting-tools/builtin-tools.md',
        'heading': 'Testdoc',
        'aliases': ['Testdoc']
    },
    'tidy': {
        'file': 'supporting-tools/builtin-tools.md',
        'heading': 'Tidy',
        'aliases': ['Tidy']
    },

    # Appendices
    'Availablesettings': {
        'file': 'appendices/settings.md',
        'heading': 'Available settings',
        'aliases': ['settings']
    },
    'Documentation syntax': {
        'file': 'appendices/doc-formatting.md',
        'heading': 'Documentation formatting',
        'aliases': ['Documentationformatting', 'HTML formatting']
    },
}


def slugify(text: str) -> str:
    """Convert heading text to a slug similar to mkdocs toc anchors."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = text.strip('-')
    return text


def find_heading_line(content: str, heading: str) -> Optional[int]:
    """Find the line number of a heading in markdown content."""
    lines = content.split('\n')
    heading_lower = heading.lower()

    for i, line in enumerate(lines):
        # Match markdown headings (# to ######)
        match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if match:
            heading_text = match.group(2).strip()
            if heading_text.lower() == heading_lower:
                return i
            # Also try without punctuation
            heading_text_clean = re.sub(r'[^\w\s]', '', heading_text).lower()
            heading_clean = re.sub(r'[^\w\s]', '', heading).lower()
            if heading_text_clean == heading_clean:
                return i
    return None


def create_anchor_html(anchor_names: List[str]) -> str:
    """Create HTML anchor elements for the given anchor names."""
    anchors = []
    for name in anchor_names:
        # Use single line format for cleaner output
        anchors.append(f'<a id="{name}"></a>')
    return '\n'.join(anchors)


def add_anchors_to_file(filepath: Path, anchors: Dict[str, str],
                         dry_run: bool = False, verbose: bool = False) -> List[str]:
    """
    Add legacy anchors to a markdown file.

    Returns list of changes made (or would be made in dry run).
    """
    changes = []

    if not filepath.exists():
        if verbose:
            print(f"  Skipping {filepath} - file does not exist")
        return changes

    content = filepath.read_text(encoding='utf-8')
    lines = content.split('\n')
    modified = False

    # Build mapping of headings to anchors to add
    heading_anchors: Dict[int, List[str]] = {}

    for anchor_name, heading in anchors.items():
        line_num = find_heading_line(content, heading)
        if line_num is not None:
            if line_num not in heading_anchors:
                heading_anchors[line_num] = []
            heading_anchors[line_num].append(anchor_name)
            changes.append(f"  + Adding anchor '{anchor_name}' before heading '{heading}' at line {line_num + 1}")
        else:
            if verbose:
                print(f"  Warning: Could not find heading '{heading}' for anchor '{anchor_name}' in {filepath}")

    if not heading_anchors:
        return changes

    # Insert anchors in reverse order to preserve line numbers
    for line_num in sorted(heading_anchors.keys(), reverse=True):
        anchor_names = heading_anchors[line_num]
        anchor_html = create_anchor_html(anchor_names)

        # Check if anchors already exist
        if line_num > 0:
            prev_line = lines[line_num - 1]
            existing = False
            for name in anchor_names:
                if f'id="{name}"' in prev_line:
                    existing = True
                    break
            if existing:
                continue

        # Insert anchor line(s) before the heading
        lines.insert(line_num, anchor_html)
        lines.insert(line_num, '')  # Add blank line before anchors
        modified = True

    if modified and not dry_run:
        new_content = '\n'.join(lines)
        filepath.write_text(new_content, encoding='utf-8')

    return changes


def process_all_files(docs_dir: Path, dry_run: bool = False, verbose: bool = False) -> None:
    """Process all markdown files and add legacy anchors."""

    # Group anchors by file
    file_anchors: Dict[str, Dict[str, str]] = {}

    for primary_anchor, info in ANCHOR_MAPPINGS.items():
        filepath = info['file']
        heading = info['heading']
        aliases = info.get('aliases', [])

        if filepath not in file_anchors:
            file_anchors[filepath] = {}

        # Add primary anchor
        file_anchors[filepath][primary_anchor] = heading

        # Add aliases
        for alias in aliases:
            file_anchors[filepath][alias] = heading

    total_changes = []

    for relative_path, anchors in file_anchors.items():
        filepath = docs_dir / relative_path
        if verbose:
            print(f"\nProcessing: {filepath}")

        changes = add_anchors_to_file(filepath, anchors, dry_run, verbose)
        total_changes.extend(changes)

        if changes:
            for change in changes:
                print(change)

    action = "Would add" if dry_run else "Added"
    print(f"\n{action} {len(total_changes)} anchor(s) total")


def generate_anchor_report(docs_dir: Path) -> None:
    """Generate a report of all legacy anchors and their mappings."""
    print("\n" + "=" * 80)
    print("LEGACY ANCHOR MAPPING REPORT")
    print("=" * 80)
    print("\nThis report shows all legacy anchors and where they map in the new structure.\n")

    # Group by section
    sections = {}
    for anchor, info in sorted(ANCHOR_MAPPINGS.items()):
        section = info['file'].split('/')[0]
        if section not in sections:
            sections[section] = []
        sections[section].append((anchor, info))

    for section, items in sorted(sections.items()):
        print(f"\n## {section.replace('-', ' ').title()}")
        print("-" * 40)

        for anchor, info in items:
            filepath = info['file']
            heading = info['heading']
            aliases = info.get('aliases', [])

            print(f"\n  Anchor: {anchor}")
            print(f"  File: {filepath}")
            print(f"  Heading: {heading}")
            if aliases:
                print(f"  Aliases: {', '.join(aliases)}")


def main():
    parser = argparse.ArgumentParser(
        description='Add legacy anchors to MkDocs markdown files for backward compatibility'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without modifying files'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print detailed information about changes'
    )
    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate a report of all legacy anchor mappings'
    )
    parser.add_argument(
        '--docs-dir',
        type=Path,
        default=None,
        help='Path to the docs directory (default: auto-detect)'
    )

    args = parser.parse_args()

    # Find docs directory
    if args.docs_dir:
        docs_dir = args.docs_dir
    else:
        # Try to find it relative to script location
        script_dir = Path(__file__).parent
        docs_dir = script_dir.parent / 'docs'

        if not docs_dir.exists():
            # Try current directory
            docs_dir = Path.cwd() / 'docs'

    if not docs_dir.exists():
        print(f"Error: Could not find docs directory at {docs_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Using docs directory: {docs_dir}")

    if args.report:
        generate_anchor_report(docs_dir)
    else:
        if args.dry_run:
            print("\n*** DRY RUN - No files will be modified ***\n")

        process_all_files(docs_dir, args.dry_run, args.verbose)


if __name__ == '__main__':
    main()
