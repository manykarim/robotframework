# Command line options


This appendix lists all the command line options that are available
when [executing test cases](../executing-tests/index.md#executing-test-cases)  and when [post-processing outputs](../executing-tests/post-processing.md#post-processing-outputs).
Also environment variables affecting execution and post-processing
are listed.


## Command line options for test execution

| Option | Description |
|--------|-------------|
| `--rpa` | Turn on [generic automation](#generic-automation) mode. |
| `--language <lang>` | Activate localization. `lang` can be a name or a code of a [built-in language](../appendices/translations.md), or a path or a module name of a custom language file. |
| `-F, --extension <value>` | [Parse only these files](#parse-only-these-files) when executing a directory. |
| `-I, --parseinclude <pattern>` | [Parse only matching files](#parse-only-matching-files) when executing a directory. |
| `-N, --name <name>` | [Sets the name](#sets-the-name) of the top-level test suite. |
| `-D, --doc <document>` | [Sets the documentation](#sets-the-documentation) of the top-level test suite. |
| `-M, --metadata <name:value>` | [Sets free metadata](#sets-free-metadata) for the top level test suite. |
| `-G, --settag <tag>` | [Sets the tag(s)](#sets-the-tags) to all executed test cases. |
| `-t, --test <name>` | [Selects the test cases by name](#selects-the-test-cases-by-name). |
| `--task <name>` | Alias for `--test` that can be used when [executing tasks](#executing-tasks). |
| `-s, --suite <name>` | [Selects the test suites](#selects-the-test-suites) by name. |
| `-R, --rerunfailed <file>` | [Selects failed tests](#selects-failed-tests) from an earlier [output file](../executing-tests/output-files.md#output-file) to be re-executed. |
| `-S, --rerunfailedsuites <file>` | [Selects failed test suites](#selects-failed-test-suites) from an earlier [output file](../executing-tests/output-files.md#output-file) to be re-executed. |
| `-i, --include <tag>` | [Selects the test cases](#selects-the-test-cases) by tag. |
| `-e, --exclude <tag>` | [Selects the test cases](#selects-the-test-cases) by tag. |
| `--skip <tag>` | Tests having given tag will be [skipped](#skipped). Tag can be a pattern. |
| `--skiponfailure <tag>` | Tests having given tag will be [skipped](#skipped) if they fail. |
| `-v, --variable <name:value>` | Sets [individual variables](#individual-variables). |
| `-V, --variablefile <path:args>` | Sets variables using [variable files](../creating-test-data/resource-and-variable-files.md#variable-files). |
| `-d, --outputdir <dir>` | Defines where to [create output files](#create-output-files). |
| `-o, --output <file>` | Sets the path to the generated [output file](../executing-tests/output-files.md#output-file). |
| `--legacyoutput` | Creates output file in [Robot Framework 6.x compatible format](#robot-framework-6x-compatible-format). |
| `-l, --log <file>` | Sets the path to the generated [log file](../executing-tests/output-files.md#log-file). |
| `-r, --report <file>` | Sets the path to the generated [report file](../executing-tests/output-files.md#report-file). |
| `-x, --xunit <file>` | Sets the path to the generated [xUnit compatible result file](../executing-tests/output-files.md#xunit-compatible-result-file). |
| `-b, --debugfile <file>` | A [debug file](../executing-tests/output-files.md#debug-file) that is written during execution. |
| `-T, --timestampoutputs` | [Adds a timestamp](#adds-a-timestamp) to [output files](../executing-tests/output-files.md#output-files) listed above. |
| `--splitlog` | [Split log file](#split-log-file) into smaller pieces that open in browser transparently. |
| `--logtitle <title>` | [Sets a title](#sets-a-title) for the generated test log. |
| `--reporttitle <title>` | [Sets a title](#sets-a-title) for the generated test report. |
| `--reportbackground <colors>` | [Sets background colors](#sets-background-colors) of the generated report. |
| `--maxerrorlines <lines>` | Sets the number of [error lines](#error-lines) shown in report when tests fail. |
| `--maxassignlength <characters>` | Sets the number of characters shown in log when [variables are assigned](../creating-test-data/variables.md#automatically-logging-assigned-variable-value). |
| `-L, --loglevel <level>` | [Sets the threshold level](#sets-the-threshold-level) for logging. Optionally the default [visible log level](../executing-tests/output-files.md#visible-log-level) can be given separated with a colon (:). |
| `--suitestatlevel <level>` | Defines how many [levels to show](#levels-to-show) in the *Statistics by Suite* table in outputs. |
| `--tagstatinclude <tag>` | [Includes only these tags](#includes-only-these-tags) in the *Statistics by Tag* table. |
| `--tagstatexclude <tag>` | [Excludes these tags](#excludes-these-tags) from the *Statistics by Tag* table. |
| `--tagstatcombine <tags:title>` | Creates [combined statistics based on tags](#combined-statistics-based-on-tags). |
| `--tagdoc <pattern:doc>` | Adds [documentation to the specified tags](#documentation-to-the-specified-tags). |
| `--tagstatlink <pattern:link:title>` | Adds [external links](#external-links) to the *Statistics by Tag* table. |
| `--expandkeywords <name:pattern\|tag:pattern>` | Automatically [expand keywords](#expand-keywords) in the generated log file. |
| `--removekeywords <all\|passed\|name:pattern\|tag:pattern\|for\|while\|wuks>` | [Removes keyword data](#removes-keyword-data) from the generated log file. |
| `--flattenkeywords <for\|while\|iteration\|name:pattern\|tag:pattern>` | [Flattens keywords](#flattens-keywords) in the generated log file. |
| `--listener <name:args>` | [Sets a listener](#sets-a-listener) for monitoring test execution. |
| `--nostatusrc` | Sets the [return code](#return-code) to zero regardless of failures in test cases. Error codes are returned normally. |
| `--runemptysuite` | Executes tests also if the selected [test suites are empty](#test-suites-are-empty). |
| `--dryrun` | In the [dry run](../executing-tests/configuring-execution.md#dry-run) mode tests are run without executing keywords originating from test libraries. Useful for validating test data syntax. |
| `-X, --exitonfailure` | [Stops test execution](../executing-tests/test-execution.md#stopping-when-first-test-case-fails) if any test fails. |
| `--exitonerror` | [Stops test execution](../executing-tests/test-execution.md#stopping-on-parsing-or-execution-error) if any error occurs when parsing test data, importing libraries, and so on. |
| `--skipteardownonexit` | [Skips teardowns](#skips-teardowns) if test execution is prematurely stopped. |
| `--prerunmodifier <name:args>` | Activate [programmatic modification of test data](../executing-tests/configuring-execution.md#programmatic-modification-of-test-data). |
| `--prerebotmodifier <name:args>` | Activate [programmatic modification of results](../executing-tests/output-files.md#programmatic-modification-of-results). |
| `--randomize <all\|suites\|tests\|none>` | [Randomizes](#Randomizes) test execution order. |
| `--console <verbose\|dotted\|quiet\|none>` | [Console output type](../executing-tests/configuring-execution.md#console-output-type). |
| `--dotted` | Shortcut for `--console dotted`. |
| `--quiet` | Shortcut for `--console quiet`. |
| `-W, --consolewidth <width>` | [Sets the width](#sets-the-width) of the console output. |
| `-C, --consolecolors <auto\|on\|ansi\|off>` | [Specifies are colors](#specifies-are-colors) used on the console. |
| `--consolelinks <auto\|off>` | Controls [making paths to results files hyperlinks](../executing-tests/output-files.md#console-links). |
| `-K, --consolemarkers <auto\|on\|off>` | Show [markers on the console](#markers-on-the-console) when top level keywords in a test case end. |
| `-P, --pythonpath <path>` | Additional locations to add to the [module search path](#module-search-path). |
| `-A, --argumentfile <path>` | A text file to [read more arguments](#read-more-arguments) from. |
| `-h, --help` | Prints [usage instructions](#usage-instructions). |
| `--version` | Prints the [version information](../index.md#version-information). |


## Command line options for post-processing outputs

| Option | Description |
|--------|-------------|
| `--rpa` | Turn on [generic automation](#generic-automation) mode. |
| `-R, --merge` | Changes result combining behavior to [merging](../executing-tests/post-processing.md#merging-outputs). |
| `-N, --name <name>` | [Sets the name](#sets-the-name) of the top level test suite. |
| `-D, --doc <document>` | [Sets the documentation](#sets-the-documentation) of the top-level test suite. |
| `-M, --metadata <name:value>` | [Sets free metadata](#sets-free-metadata) for the top-level test suite. |
| `-G, --settag <tag>` | [Sets the tag(s)](#sets-the-tags) to all processed test cases. |
| `-t, --test <name>` | [Selects the test cases by name](#selects-the-test-cases-by-name). |
| `--task <name>` | Alias for `--test`. |
| `-s, --suite <name>` | [Selects the test suites](#selects-the-test-suites) by name. |
| `-i, --include <tag>` | [Selects the test cases](#selects-the-test-cases) by tag. |
| `-e, --exclude <tag>` | [Selects the test cases](#selects-the-test-cases) by tag. |
| `-d, --outputdir <dir>` | Defines where to [create output files](#create-output-files). |
| `-o, --output <file>` | Sets the path to the generated [output file](../executing-tests/output-files.md#output-file). |
| `--legacyoutput` | Creates output file in [Robot Framework 6.x compatible format](#robot-framework-6x-compatible-format). |
| `-l, --log <file>` | Sets the path to the generated [log file](../executing-tests/output-files.md#log-file). |
| `-r, --report <file>` | Sets the path to the generated [report file](../executing-tests/output-files.md#report-file). |
| `-x, --xunit <file>` | Sets the path to the generated [xUnit compatible result file](../executing-tests/output-files.md#xunit-compatible-result-file). |
| `-T, --timestampoutputs` | [Adds a timestamp](#adds-a-timestamp) to [output files](../executing-tests/output-files.md#output-files) listed above. |
| `--splitlog` | [Split log file](#split-log-file) into smaller pieces that open in browser transparently. |
| `--logtitle <title>` | [Sets a title](#sets-a-title) for the generated test log. |
| `--reporttitle <title>` | [Sets a title](#sets-a-title) for the generated test report. |
| `--reportbackground <colors>` | [Sets background colors](#sets-background-colors) of the generated report. |
| `-L, --loglevel <level>` | [Sets the threshold level](#sets-the-threshold-level) to select log messages. Optionally the default [visible log level](../executing-tests/output-files.md#visible-log-level) can be given separated with a colon (:). |
| `--suitestatlevel <level>` | Defines how many [levels to show](#levels-to-show) in the *Statistics by Suite* table in outputs. |
| `--tagstatinclude <tag>` | [Includes only these tags](#includes-only-these-tags) in the *Statistics by Tag* table. |
| `--tagstatexclude <tag>` | [Excludes these tags](#excludes-these-tags) from the *Statistics by Tag* table. |
| `--tagstatcombine <tags:title>` | Creates [combined statistics based on tags](#combined-statistics-based-on-tags). |
| `--tagdoc <pattern:doc>` | Adds [documentation to the specified tags](#documentation-to-the-specified-tags). |
| `--tagstatlink <pattern:link:title>` | Adds [external links](#external-links) to the *Statistics by Tag* table. |
| `--expandkeywords <name:pattern\|tag:pattern>` | Automatically [expand keywords](#expand-keywords) in the generated log file. |
| `--removekeywords <all\|passed\|name:pattern\|tag:pattern\|for\|wuks>` | [Removes keyword data](#removes-keyword-data) from the generated outputs. |
| `--flattenkeywords <for\|foritem\|name:pattern\|tag:pattern>` | [Flattens keywords](#flattens-keywords) in the generated outputs. |
| `--starttime <timestamp>` | Sets the [starting time](#starting-time) of test execution when creating reports. |
| `--endtime <timestamp>` | Sets the [ending time](#ending-time) of test execution when creating reports. |
| `--nostatusrc` | Sets the [return code](#return-code) to zero regardless of failures in test cases. Error codes are returned normally. |
| `--processemptysuite` | Processes output files even if files contain [empty test suites](#empty-test-suites). |
| `--prerebotmodifier <name:args>` | Activate [programmatic modification of results](../executing-tests/output-files.md#programmatic-modification-of-results). |
| `-C, --consolecolors <auto\|on\|ansi\|off>` | [Specifies are colors](#specifies-are-colors) used on the console. |
| `--consolelinks <auto\|off>` | Controls [making paths to results files hyperlinks](../executing-tests/output-files.md#console-links). |
| `-P, --pythonpath <path>` | Additional locations to add to the [module search path](#module-search-path). |
| `-A, --argumentfile <path>` | A text file to [read more arguments](#read-more-arguments) from. |
| `-h, --help` | Prints [usage instructions](#usage-instructions). |
| `--version` | Prints the [version information](../index.md#version-information). |


## Environment variables for execution and post-processing

| Variable | Description |
|----------|-------------|
| `ROBOT_OPTIONS` and `REBOT_OPTIONS` | Space separated list of default options to be placed [in front of any explicit options](#in-front-of-any-explicit-options) on the command line. |
| `ROBOT_SYSLOG_FILE` | Path to a syslog file where Robot Framework writes internal information about parsing test case files and running tests. |
| `ROBOT_SYSLOG_LEVEL` | Log level to use when writing to the syslog file. |
| `ROBOT_INTERNAL_TRACES` | When set to any non-empty value, Robot Framework's internal methods are included in [error tracebacks](#error-tracebacks). |
