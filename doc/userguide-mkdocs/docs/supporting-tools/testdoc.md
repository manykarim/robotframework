<a id="testdoc"></a>
# Test data documentation tool (Testdoc)

!!! warning
    The built-in Testdoc tool is deprecated and will be removed in Robot
    Framework 8.0. Use the [external Testdoc tool](https://marvkler.github.io/robotframework-testdoc) instead.

Testdoc is Robot Framework's built-in tool for generating high level
documentation based on test cases. The created documentation is in HTML
format and it includes name, documentation and other metadata of each
test suite and test case, as well as the top-level keywords and their
arguments.

## General usage

### Synopsis

```
python -m robot.testdoc [options] data_sources output_file
```

### Options

`-T, --title <title>`{.option}
:   Set the title of the generated documentation. Underscores in the title are converted to spaces. The default title is the name of the top level suite.

`-N, --name <name>`{.option}
:   Override the name of the top level test suite.

`-D, --doc <doc>`{.option}
:   Override the documentation of the top level test suite.

`-M, --metadata <name:value>`{.option}
:   Set/override free metadata of the top level test suite.

`-G, --settag <tag>`{.option}
:   Set given tag(s) to all test cases.

`-t, --test <name>`{.option}
:   Include tests by name.

`-s, --suite <name>`{.option}
:   Include suites by name.

`-i, --include <tag>`{.option}
:   Include tests by tags.

`-e, --exclude <tag>`{.option}
:   Exclude tests by tags.

`-A, --argumentfile <path>`{.option}
:   Text file to read more arguments from. Works exactly like [argument files](../executing-tests/basic-usage.md#argument-files) when running tests.

`-h, --help`{.option}
:   Print this help in the console.

All options except `--title`{.option} have exactly the same semantics as same
options have when [executing test cases](../executing-tests/configuring-execution.md#configuring-execution).

## Generating documentation

Data can be given as a single file, directory, or as multiple files and
directories. In all these cases, the last argument must be the file where
to write the output.

Testdoc can be executed as an installed module like
`python -m robot.testdoc` or as a script like `python path/robot/testdoc.py`.

Examples:

```
python -m robot.testdoc my_test.robot testdoc.html
python path/to/robot/testdoc.py --name "Smoke tests" --include smoke path/to/tests smoke.html
```
