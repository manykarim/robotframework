# Command line options

This appendix lists all the command line options that are available
when [executing test cases](../executing-tests/basic-usage.md#executing-test-cases)  and when [post-processing outputs](../executing-tests/post-processing.md#post-processing-outputs).
Also environment variables affecting execution and post-processing
are listed.

## Command line options for test execution

`--rpa`{.option}
:   Turn on [generic automation](../executing-tests/task-execution.md#task-execution) mode.

`--language <lang>`{.option}
:   Activate [localization](../creating-test-data/test-data-syntax.md#localization). `lang` can be a name or a code of a [built-in language](translations.md#translations), or a path or a module name of a custom language file.

`-F, --extension <value>`{.option}
:   [Parse only these files](../executing-tests/configuring-execution.md#selecting-files-to-parse) when executing a directory.

`-I, --parseinclude <pattern>`{.option}
:   [Parse only matching files](../executing-tests/configuring-execution.md#selecting-files-to-parse) when executing a directory.

`-N, --name <name>`{.option}
:   [Sets the name](../executing-tests/configuring-execution.md#setting-suite-name) of the top-level test suite.

`-D, --doc <document>`{.option}
:   [Sets the documentation](../executing-tests/configuring-execution.md#setting-suite-documentation) of the top-level test suite.

`-M, --metadata <name:value>`{.option}
:   [Sets free metadata](../executing-tests/configuring-execution.md#setting-free-suite-metadata) for the top level test suite.

`-G, --settag <tag>`{.option}
:   [Sets the tag(s)](../executing-tests/configuring-execution.md#setting-test-tags) to all executed test cases.

`-t, --test <name>`{.option}
:   [Selects the test cases by name](../executing-tests/configuring-execution.md#by-test-names).

`--task <name>`{.option}
:   Alias for `--test`{.option} that can be used when [executing tasks](../executing-tests/task-execution.md#executing-tasks).

`-s, --suite <name>`{.option}
:   [Selects the test suites](../executing-tests/configuring-execution.md#by-suite-names) by name.

`-R, --rerunfailed <file>`{.option}
:   [Selects failed tests](../executing-tests/configuring-execution.md#re-executing-failed-test-cases) from an earlier [output file](../executing-tests/result-files.md#output-file) to be re-executed.

`-S, --rerunfailedsuites <file>`{.option}
:   [Selects failed test suites](../executing-tests/configuring-execution.md#re-executing-failed-test-suites) from an earlier [output file](../executing-tests/result-files.md#output-file) to be re-executed.

`-i, --include <tag>`{.option}
:   [Selects the test cases](../executing-tests/configuring-execution.md#by-tag-names) by tag.

`-e, --exclude <tag>`{.option}
:   [Selects the test cases](../executing-tests/configuring-execution.md#by-tag-names) by tag.

`--skip <tag>`{.option}
:   Tests having given tag will be [skipped](../executing-tests/test-execution.md#skipped). Tag can be a pattern.

`--skiponfailure <tag>`{.option}
:   Tests having given tag will be [skipped](../executing-tests/test-execution.md#skipped) if they fail.

`-v, --variable <name:value>`{.option}
:   Sets [individual variables](../creating-test-data/variables.md#command-line-variables).

`-V, --variablefile <path:args>`{.option}
:   Sets variables using [variable files](../creating-test-data/variable-files.md#variable-files).

`-d, --outputdir <dir>`{.option}
:   Defines where to [create result files](../executing-tests/result-files.md#output-directory).

`-o, --output <file>`{.option}
:   Sets the path to the generated [output file](../executing-tests/result-files.md#output-file).

`--legacyoutput`{.option}
:   Creates output file in [Robot Framework 6.x compatible format](../executing-tests/result-files.md#legacy-xml-format).

`-l, --log <file>`{.option}
:   Sets the path to the generated [log file](../executing-tests/result-files.md#log-file).

`-r, --report <file>`{.option}
:   Sets the path to the generated [report file](../executing-tests/result-files.md#report-file).

`-x, --xunit <file>`{.option}
:   Sets the path to the generated [xUnit compatible result file](../executing-tests/result-files.md#xunit-compatible-result-file).

`-b, --debugfile <file>`{.option}
:   A [debug file](../executing-tests/result-files.md#debug-file) that is written during execution.

`-T, --timestampoutputs`{.option}
:   [Adds a timestamp](../executing-tests/result-files.md#timestamping-result-files) to [result files](../executing-tests/result-files.md#result-files) listed above.

`--splitlog`{.option}
:   [Split log file](../executing-tests/result-files.md#splitting-logs) into smaller pieces that open in browser transparently.

`--logtitle <title>`{.option}
:   [Sets a title](../executing-tests/result-files.md#setting-titles) for the generated test log.

`--reporttitle <title>`{.option}
:   [Sets a title](../executing-tests/result-files.md#setting-titles) for the generated test report.

`--reportbackground <colors>`{.option}
:   [Sets background colors](../executing-tests/result-files.md#setting-background-colors) of the generated report.

`--maxerrorlines <lines>`{.option}
:   Sets the number of [error lines](../executing-tests/result-files.md#limiting-error-message-length-in-reports) shown in report when tests fail.

`--maxassignlength <characters>`{.option}
:   Sets the number of characters shown in log when [variables are assigned](../creating-test-data/variables.md#automatically-logging-assigned-variable-value).

`-L, --loglevel <level>`{.option}
:   [Sets the threshold level](../executing-tests/result-files.md#setting-log-level) for logging. Optionally the default [visible log level](../executing-tests/result-files.md#visible-log-level) can be given separated with a colon (:).

`--suitestatlevel <level>`{.option}
:   Defines how many [levels to show](../executing-tests/result-files.md#configuring-displayed-suite-statistics) in the *Statistics by Suite* table in outputs.

`--tagstatinclude <tag>`{.option}
:   [Includes only these tags](../executing-tests/result-files.md#including-and-excluding-tag-statistics) in the *Statistics by Tag* table.

`--tagstatexclude <tag>`{.option}
:   [Excludes these tags](../executing-tests/result-files.md#including-and-excluding-tag-statistics) from the *Statistics by Tag* table.

`--tagstatcombine <tags:title>`{.option}
:   Creates [combined statistics based on tags](../executing-tests/result-files.md#generating-combined-tag-statistics).

`--tagdoc <pattern:doc>`{.option}
:   Adds [documentation to the specified tags](../executing-tests/result-files.md#adding-documentation-to-tags).

`--tagstatlink <pattern:link:title>`{.option}
:   Adds [external links](../executing-tests/result-files.md#creating-links-from-tag-names) to the *Statistics by Tag* table.

`--expandkeywords <name:pattern|tag:pattern>`{.option}
:   Automatically [expand keywords](../executing-tests/result-files.md#automatically-expanding-keywords) in the generated log file.

`--removekeywords <all|passed|name:pattern|tag:pattern|for|while|wuks>`{.option}
:   [Removes keyword data](../executing-tests/result-files.md#removing-and-flattening-keywords) from the generated log file.

`--flattenkeywords <for|while|iteration|name:pattern|tag:pattern>`{.option}
:   [Flattens keywords](../executing-tests/result-files.md#removing-and-flattening-keywords) in the generated log file.

`--listener <name:args>`{.option}
:   [Sets a listener](../executing-tests/configuring-execution.md#setting-listeners) for monitoring test execution.

`--nostatusrc`{.option}
:   Sets the [return code](../executing-tests/basic-usage.md#return-codes) to zero regardless of failures in test cases. Error codes are returned normally.

`--runemptysuite`{.option}
:   Executes tests also if the selected [test suites are empty](../executing-tests/configuring-execution.md#when-no-tests-match-selection).

`--dryrun`{.option}
:   In the [dry run](../executing-tests/configuring-execution.md#dry-run) mode tests are run without executing keywords originating from test libraries. Useful for validating test data syntax.

`-X, --exitonfailure`{.option}
:   [Stops test execution](../executing-tests/test-execution.md#stopping-when-first-test-case-fails) if any test fails.

`--exitonerror`{.option}
:   [Stops test execution](../executing-tests/test-execution.md#stopping-on-parsing-or-execution-error) if any error occurs when parsing test data, importing libraries, and so on.

`--skipteardownonexit`{.option}
:   [Skips teardowns](../executing-tests/test-execution.md#handling-teardowns) if test execution is prematurely stopped.

`--prerunmodifier <name:args>`{.option}
:   Activate [programmatic modification of test data](../executing-tests/configuring-execution.md#programmatic-modification-of-test-data).

`--prerebotmodifier <name:args>`{.option}
:   Activate [programmatic modification of results](../executing-tests/result-files.md#programmatic-modification-of-results).

`--randomize <all|suites|tests|none>`{.option}
:   [Randomizes](../executing-tests/configuring-execution.md#randomizing-execution-order) test execution order.

`--console <verbose|dotted|quiet|none|custom>`{.option}
:   [Console output type](../executing-tests/configuring-execution.md#built-in-console-loggers). Also accepts [custom console loggers](../executing-tests/configuring-execution.md#custom-console-loggers).

`--dotted`{.option}
:   Shortcut for `--console dotted`.

`--quiet`{.option}
:   Shortcut for `--console quiet`.

`-W, --consolewidth <width>`{.option}
:   [Sets the width](../executing-tests/configuring-execution.md#console-width) of the console output.

`-C, --consolecolors <auto|on|ansi|off>`{.option}
:   [Specifies are colors](../executing-tests/configuring-execution.md#console-colors) used on the console.

`--consolelinks <auto|off>`{.option}
:   Controls [making paths to results files hyperlinks](../executing-tests/configuring-execution.md#console-links).

`-K, --consolemarkers <auto|on|off>`{.option}
:   Show [markers on the console](../executing-tests/configuring-execution.md#console-markers) when top level keywords in a test case end.

`-P, --pythonpath <path>`{.option}
:   Additional locations to add to the [module search path](../executing-tests/configuring-execution.md#module-search-path).

`-A, --argumentfile <path>`{.option}
:   A text file to [read more arguments](../executing-tests/basic-usage.md#argument-files) from.

`-h, --help`{.option}
:   Prints [usage instructions](../executing-tests/basic-usage.md#getting-help-and-version-information).

`--version`{.option}
:   Prints the [version information](../executing-tests/basic-usage.md#getting-help-and-version-information).

## Command line options for post-processing outputs

`--rpa`{.option}
:   Turn on [generic automation](../executing-tests/task-execution.md#task-execution) mode.

`-R, --merge`{.option}
:   Changes result combining behavior to [merging](../executing-tests/post-processing.md#merging-results).

`-N, --name <name>`{.option}
:   [Sets the name](../executing-tests/configuring-execution.md#setting-suite-name) of the top level test suite.

`-D, --doc <document>`{.option}
:   [Sets the documentation](../executing-tests/configuring-execution.md#setting-suite-documentation) of the top-level test suite.

`-M, --metadata <name:value>`{.option}
:   [Sets free metadata](../executing-tests/configuring-execution.md#setting-free-suite-metadata) for the top-level test suite.

`-G, --settag <tag>`{.option}
:   [Sets the tag(s)](../executing-tests/configuring-execution.md#setting-test-tags) to all processed test cases.

`-t, --test <name>`{.option}
:   [Selects the test cases by name](../executing-tests/configuring-execution.md#by-test-names).

`--task <name>`{.option}
:   Alias for `--test`{.option}.

`-s, --suite <name>`{.option}
:   [Selects the test suites](../executing-tests/configuring-execution.md#by-suite-names) by name.

`-i, --include <tag>`{.option}
:   [Selects the test cases](../executing-tests/configuring-execution.md#by-tag-names) by tag.

`-e, --exclude <tag>`{.option}
:   [Selects the test cases](../executing-tests/configuring-execution.md#by-tag-names) by tag.

`-d, --outputdir <dir>`{.option}
:   Defines where to [create result files](../executing-tests/result-files.md#output-directory).

`-o, --output <file>`{.option}
:   Sets the path to the generated [output file](../executing-tests/result-files.md#output-file).

`--legacyoutput`{.option}
:   Creates output file in [Robot Framework 6.x compatible format](../executing-tests/result-files.md#legacy-xml-format).

`-l, --log <file>`{.option}
:   Sets the path to the generated [log file](../executing-tests/result-files.md#log-file).

`-r, --report <file>`{.option}
:   Sets the path to the generated [report file](../executing-tests/result-files.md#report-file).

`-x, --xunit <file>`{.option}
:   Sets the path to the generated [xUnit compatible result file](../executing-tests/result-files.md#xunit-compatible-result-file).

`-T, --timestampoutputs`{.option}
:   [Adds a timestamp](../executing-tests/result-files.md#timestamping-result-files) to [result files](../executing-tests/result-files.md#result-files) listed above.

`--splitlog`{.option}
:   [Split log file](../executing-tests/result-files.md#splitting-logs) into smaller pieces that open in browser transparently.

`--logtitle <title>`{.option}
:   [Sets a title](../executing-tests/result-files.md#setting-titles) for the generated test log.

`--reporttitle <title>`{.option}
:   [Sets a title](../executing-tests/result-files.md#setting-titles) for the generated test report.

`--reportbackground <colors>`{.option}
:   [Sets background colors](../executing-tests/result-files.md#setting-background-colors) of the generated report.

`-L, --loglevel <level>`{.option}
:   [Sets the threshold level](../executing-tests/result-files.md#setting-log-level) to select log messages. Optionally the default [visible log level](../executing-tests/result-files.md#visible-log-level) can be given separated with a colon (:).

`--suitestatlevel <level>`{.option}
:   Defines how many [levels to show](../executing-tests/result-files.md#configuring-displayed-suite-statistics) in the *Statistics by Suite* table in outputs.

`--tagstatinclude <tag>`{.option}
:   [Includes only these tags](../executing-tests/result-files.md#including-and-excluding-tag-statistics) in the *Statistics by Tag* table.

`--tagstatexclude <tag>`{.option}
:   [Excludes these tags](../executing-tests/result-files.md#including-and-excluding-tag-statistics) from the *Statistics by Tag* table.

`--tagstatcombine <tags:title>`{.option}
:   Creates [combined statistics based on tags](../executing-tests/result-files.md#generating-combined-tag-statistics).

`--tagdoc <pattern:doc>`{.option}
:   Adds [documentation to the specified tags](../executing-tests/result-files.md#adding-documentation-to-tags).

`--tagstatlink <pattern:link:title>`{.option}
:   Adds [external links](../executing-tests/result-files.md#creating-links-from-tag-names) to the *Statistics by Tag* table.

`--expandkeywords <name:pattern|tag:pattern>`{.option}
:   Automatically [expand keywords](../executing-tests/result-files.md#automatically-expanding-keywords) in the generated log file.

`--removekeywords <all|passed|name:pattern|tag:pattern|for|wuks>`{.option}
:   [Removes keyword data](../executing-tests/result-files.md#removing-and-flattening-keywords) from the generated outputs.

`--flattenkeywords <for|foritem|name:pattern|tag:pattern>`{.option}
:   [Flattens keywords](../executing-tests/result-files.md#removing-and-flattening-keywords) in the generated outputs.

`--starttime <timestamp>`{.option}
:   Sets the [starting time](../executing-tests/result-files.md#setting-start-and-end-time-of-execution) of test execution when creating reports.

`--endtime <timestamp>`{.option}
:   Sets the [ending time](../executing-tests/result-files.md#setting-start-and-end-time-of-execution) of test execution when creating reports.

`--nostatusrc`{.option}
:   Sets the [return code](../executing-tests/basic-usage.md#return-codes) to zero regardless of failures in test cases. Error codes are returned normally.

`--processemptysuite`{.option}
:   Processes output files even if files contain [empty test suites](../executing-tests/configuring-execution.md#when-no-tests-match-selection).

`--prerebotmodifier <name:args>`{.option}
:   Activate [programmatic modification of results](../executing-tests/result-files.md#programmatic-modification-of-results).

`--console <verbose|quiet|none|custom>`{.option}
:   [Controlling Rebot console output](../executing-tests/post-processing.md#controlling-rebot-console-output). Also accepts [custom console loggers](../executing-tests/configuring-execution.md#custom-console-loggers).

`--quiet`{.option}
:   Shortcut for `--console quiet`.

`-C, --consolecolors <auto|on|ansi|off>`{.option}
:   [Specifies are colors](../executing-tests/configuring-execution.md#console-colors) used on the console.

`--consolelinks <auto|off>`{.option}
:   Controls [making paths to results files hyperlinks](../executing-tests/configuring-execution.md#console-links).

`-P, --pythonpath <path>`{.option}
:   Additional locations to add to the [module search path](../executing-tests/configuring-execution.md#module-search-path).

`-A, --argumentfile <path>`{.option}
:   A text file to [read more arguments](../executing-tests/basic-usage.md#argument-files) from.

`-h, --help`{.option}
:   Prints [usage instructions](../executing-tests/basic-usage.md#getting-help-and-version-information).

`--version`{.option}
:   Prints the [version information](../executing-tests/basic-usage.md#getting-help-and-version-information).

## Environment variables for execution and post-processing

`ROBOT_OPTIONS` and `REBOT_OPTIONS`
: Space separated list of default options to be placed
    [in front of any explicit options](../executing-tests/basic-usage.md#robot-options-and-rebot-options-environment-variables) on the command line.

`ROBOT_SYSLOG_FILE`
: Path to a [syslog](../executing-tests/result-files.md#system-log) file where Robot Framework writes internal
    information about parsing test case files and running
    tests.

`ROBOT_SYSLOG_LEVEL`
: Log level to use when writing to the [syslog](../executing-tests/result-files.md#system-log) file.

`ROBOT_INTERNAL_TRACES`
: When set to any non-empty value, Robot Framework's
    internal methods are included in [error tracebacks](../executing-tests/basic-usage.md#debugging-problems).

