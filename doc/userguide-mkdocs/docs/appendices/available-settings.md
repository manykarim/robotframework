
# Available settings


This appendix lists all settings that can be used in different sections.

!!! note
    Settings names are case-insensitive and can contain a varying number
    of spaces between words. For example, `Library`, `LIBRARY`, and
    `L I B R A R Y` are all equivalent. Setting section also lists
    supported translations.


## Setting section


The Setting section is used to import libraries, resource files and
variable files and to define metadata for test suites and test
cases. It can be included in test case files and resource files. Note
that in a resource file, a Setting section can only include settings for
importing libraries, resources, and variables.

| Name | Description |
|---|---|
| Library | Used for [importing libraries](../creating-test-data/creating-test-library.md#importing-libraries). |
| Resource | Used for [taking resource files into use](../creating-test-data/resource-and-variable-files.md#taking-resource-files-into-use). |
| Variables | Used for [taking variable files into use](../creating-test-data/resource-and-variable-files.md#taking-variable-files-into-use). |
| Name | Used for setting a custom [suite name](../creating-test-data/test-suite.md#suite-name). |
| Documentation | Used for specifying a [suite](../creating-test-data/test-suite.md#suite-documentation) or [resource file](../creating-test-data/resource-and-variable-files.md#resource-file-documentation) documentation. |
| Metadata | Used for setting [free suite metadata](../creating-test-data/test-suite.md#free-suite-metadata). |
| Suite Setup | Used for specifying the [suite setup](../creating-test-data/test-suite.md#suite-setup-and-teardown). |
| Suite Teardown | Used for specifying the [suite teardown](../creating-test-data/test-suite.md#suite-setup-and-teardown). |
| Test Tags | Used for specifying [test case tags](../creating-test-data/test-case.md#test-case-tags) for all tests in a suite. |
| Force Tags, Default Tags | [Deprecated settings](../creating-test-data/test-case.md#deprecated-settings) for specifying test case tags. |
| Keyword Tags | Used for specifying [user keyword tags](../creating-test-data/creating-user-keywords.md#user-keyword-tags) for all keywords in a certain file. |
| Test Setup | Used for specifying a default [test setup](../creating-test-data/test-case.md#test-setup-and-teardown). |
| Test Teardown | Used for specifying a default [test teardown](../creating-test-data/test-case.md#test-setup-and-teardown). |
| Test Template | Used for specifying a default [template keyword](../creating-test-data/test-case.md#test-templates) for test cases. |
| Test Timeout | Used for specifying a default [test case timeout](../creating-test-data/test-case.md#test-case-timeout). |
| Task Setup, Task Teardown, Task Template, Task Timeout | Aliases for Test Setup, Test Teardown, Test Template and Test Timeout, respectively, that can be used when [creating tasks](../creating-test-data/creating-tasks.md#creating-tasks). |


## Test Case section


The settings in the Test Case section are always specific to the test
case for which they are defined. Some of these settings override the
default values defined in the Settings section.

Exactly same settings are available when [creating tasks](../creating-test-data/creating-tasks.md#creating-tasks) in the Task section.

| Name | Description |
|---|---|
| [Documentation] | Used for specifying a [test case documentation](../creating-test-data/test-case.md#test-case-documentation). |
| [Tags] | Used for [tagging test cases](../creating-test-data/test-case.md#test-case-tags). |
| [Setup] | Used for specifying a [test setup](../creating-test-data/test-case.md#test-setup-and-teardown). |
| [Teardown] | Used for specifying a [test teardown](../creating-test-data/test-case.md#test-setup-and-teardown). |
| [Template] | Used for specifying a [template keyword](../creating-test-data/test-case.md#test-templates). |
| [Timeout] | Used for specifying a [test case timeout](../creating-test-data/test-case.md#test-case-timeout). |


## Keyword section


Settings in the Keyword section are specific to the user keyword for
which they are defined.

| Name | Description |
|---|---|
| [Documentation] | Used for specifying a [user keyword documentation](../creating-test-data/creating-user-keywords.md#user-keyword-documentation). |
| [Tags] | Used for specifying [user keyword tags](../creating-test-data/creating-user-keywords.md#user-keyword-tags). |
| [Arguments] | Used for specifying [user keyword arguments](../creating-test-data/creating-user-keywords.md#user-keyword-arguments). |
| [Setup] | Used for specifying a [user keyword setup](../executing-tests/test-execution.md#user-keyword-setup). New in Robot Framework 7.0. |
| [Teardown] | Used for specifying [user keyword teardown](../creating-test-data/creating-user-keywords.md#user-keyword-teardown). |
| [Timeout] | Used for specifying a [user keyword timeout](../creating-test-data/creating-user-keywords.md#user-keyword-timeout). |
| [Return] | Used for specifying [user keyword return values](../creating-test-data/creating-user-keywords.md#user-keyword-return-values). Deprecated in Robot Framework 7.0. Use the [RETURN](../creating-test-data/creating-user-keywords.md#return-statement) statement instead. |

