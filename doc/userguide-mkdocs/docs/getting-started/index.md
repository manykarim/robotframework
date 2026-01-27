# Getting Started

<a id="GettingStarted"></a>

This section introduces Robot Framework, covers installation, and helps you run your first tests.

## In This Section

- [Introduction](introduction.md) - What is Robot Framework and why use it
- [Copyright and License](copyright-and-license.md) - Licensing information
- [Demonstration](demonstration.md) - Quick examples to get started

## Quick Start

Robot Framework is a generic open source automation framework. Here is a minimal example of a Robot Framework test:

```robotframework
*** Test Cases ***
My First Test
    Log    Hello, Robot Framework!
    Should Be Equal    ${1 + 1}    ${2}
```

To run this test:

```bash
robot my_first_test.robot
```

## What You'll Learn

After completing this section, you will:

1. Understand what Robot Framework is and its key features
2. Have Robot Framework installed on your system
3. Know the basic structure of Robot Framework test data
4. Be able to run your first test and view results

## Prerequisites

- Python 3.8 or newer
- Basic command line knowledge
- A text editor (VS Code with Robot Framework extensions recommended)

## Next Steps

Once you've completed the Getting Started section, proceed to [Creating Test Data](../creating-test-data/index.md) to learn about test case syntax and structure in detail.
