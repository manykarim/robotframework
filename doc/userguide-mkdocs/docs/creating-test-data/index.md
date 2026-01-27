# Creating Test Data

<a id="CreatingTestData"></a>

This section covers all aspects of creating test data in Robot Framework, from basic syntax to advanced features.

## In This Section

- [Test Data Syntax](test-data-syntax.md) - File formats, tables, and syntax rules
- [Creating Test Cases](creating-test-cases.md) - Test case structure and organization
- [Creating Tasks](creating-tasks.md) - Task-based automation (RPA)
- [Creating Test Suites](creating-test-suites.md) - Suite organization and setup/teardown
- [Using Test Libraries](using-test-libraries.md) - Importing and using libraries
- [Variables](variables.md) - Variable types, scopes, and usage
- [Creating User Keywords](creating-user-keywords.md) - Custom keyword definitions
- [Resource and Variable Files](resource-and-variable-files.md) - Sharing data across files
- [Control Structures](control-structures.md) - IF/ELSE, FOR loops, TRY/EXCEPT
- [Advanced Features](advanced-features.md) - Tags, documentation, timeouts

## Overview

Robot Framework uses a simple, plain text syntax that is easy to read and write. Test data is organized in tables using a specific format.

### Basic Structure

```robotframework
*** Settings ***
Library    Collections
Suite Setup    Initialize Test Environment

*** Variables ***
${MESSAGE}    Hello World

*** Test Cases ***
Example Test
    [Documentation]    This is an example test case
    Log    ${MESSAGE}
    Should Be Equal    ${MESSAGE}    Hello World

*** Keywords ***
Initialize Test Environment
    Log    Setting up test environment
```

### Key Concepts
| Concept | Description |
|---------|-------------|
| Test Cases | Individual tests that verify specific functionality |
| Keywords | Reusable building blocks that perform actions |
| Variables | Store and pass data between keywords |
| Libraries | Collections of keywords (built-in or external) |
| Resource Files | Shared keywords and variables |

## File Formats

Robot Framework supports several file formats:

- `*.robot` - Standard Robot Framework format
- `*.resource` - Resource files containing keywords
- `*.py` - Python variable and keyword files

## Next Steps

Start with [Test Data Syntax](test-data-syntax.md) to learn about the file formats and syntax rules, then work through the remaining topics in order.
