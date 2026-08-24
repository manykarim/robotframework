
<a id="Introduction"></a>
# Introduction

Robot Framework is a Python-based, extensible keyword-driven automation
framework for acceptance testing, acceptance test driven development (ATDD),
behavior driven development (BDD) and robotic process automation (RPA). It
can be used in distributed, heterogeneous environments, where automation
requires using different technologies and interfaces.

The framework has a rich ecosystem around it consisting of various generic
libraries and tools that are developed as separate projects. For more
information about Robot Framework and the ecosystem, see
http://robotframework.org.

Robot Framework is open source software released under the [Apache License
2.0](#apache-license-20). Its development is sponsored by the [Robot Framework Foundation](http://robotframework.org/foundation).

!!! note
    The official RPA support was added in Robot Framework 3.1.
    This User Guide still talks mainly about creating tests, test data,
    and test libraries, but same concepts apply also when [creating
    tasks](../creating-test-data/creating-tasks.md#creating-tasks).


<a id="WhyRobotFramework"></a>
<a id="Why Robot Framework?"></a>
## Why Robot Framework?

- Enables easy-to-use tabular syntax for [creating test cases](../creating-test-data/creating-test-cases.md#creating-test-cases) in a uniform
  way.

- Provides ability to create reusable [higher-level keywords](../creating-test-data/creating-user-keywords.md#creating-user-keywords) from the
  existing keywords.

- Provides easy-to-read result [reports](../executing-tests/post-processing.md#creating-reports-logs-and-output-files) and [logs](../executing-tests/execution-artifacts.md#splitting-logs) in HTML format.

- Is platform and application independent.

- Provides a simple [library API](../extending/creating-test-libraries.md#creating-test-libraries) for creating customized test libraries
  which can be implemented natively with Python.

- Provides a [command line interface](../executing-tests/basic-usage.md#executing-test-cases) and XML based [output files](../executing-tests/result-files.md#output-file)  for
  integration into existing build infrastructure (continuous integration
  systems).

- Provides support for testing web applications, rest APIs, mobile applications,
  running processes, connecting to remote systems via Telnet or SSH, and so on.

- Supports creating [data-driven test cases](../creating-test-data/creating-test-cases.md#data-driven-style).

- Has built-in support for [variables](../creating-test-data/variables.md#variables), practical particularly for testing in
  different environments.

- Provides [tagging](../creating-test-data/creating-test-cases.md#tagging-test-cases) to categorize and [select test cases](../executing-tests/configuring-execution.md#selecting-test-cases) to be executed.

- Enables easy integration with source control: [test suites](../creating-test-data/creating-test-suites.md#creating-test-suites) are just files
  and directories that can be versioned with the production code.

- Provides [test-case](../creating-test-data/creating-test-cases.md#test-setup-and-teardown) and [test-suite](../creating-test-data/creating-test-suites.md#suite-setup-and-teardown) -level setup and teardown.

- The modular architecture supports creating tests even for applications with
  several diverse interfaces.


<a id="High-levelarchitecture"></a>
<a id="HighLevelArchitecture"></a>
## High-level architecture

Robot Framework is a generic, application and technology independent
framework. It has a highly modular architecture illustrated in the
diagram below.

![Robot Framework architecture](architecture.png)

*Robot Framework architecture*

The [test data](#creating-test-data) is in simple, easy-to-edit tabular format. When
Robot Framework is started, it processes the data, [executes test
cases](../executing-tests/basic-usage.md#executing-test-cases) and generates logs and reports. The core framework does not
know anything about the target under test, and the interaction with it
is handled by [libraries](../extending/creating-test-libraries.md#creating-test-libraries). Libraries can either use application
interfaces directly or use lower level test tools as drivers.

## Screenshots

Following screenshots show examples of the [test data](#creating-test-data) and created
[reports](../executing-tests/post-processing.md#creating-reports-logs-and-output-files) and [logs](../executing-tests/execution-artifacts.md#splitting-logs).

![Test case file](testdata_screenshots.png)

*Test case file*

![Reports and logs](screenshots.png)

*Reports and logs*

## Getting more information

### Project pages

The number one place to find more information about Robot Framework
and the rich ecosystem around it is http://robotframework.org.
Robot Framework itself is hosted on [GitHub](https://github.com/robotframework/robotframework).

<a id="mailing-list"></a>

<a id="Mailinglists"></a>
<a id="mailing list"></a>
### Mailing lists

There are several Robot Framework mailing lists where to ask and
search for more information. The mailing list archives are open for
everyone (including the search engines) and everyone can also join
these lists freely. Only list members can send mails, though, and to
prevent spam new users are moderated which means that it might take a
little time before your first message goes through.  Do not be afraid
to send question to mailing lists but remember [How To Ask Questions
The Smart Way](http://www.catb.org/~esr/faqs/smart-questions.html).

robotframework-[users](http://groups.google.com/group/robotframework-users)
: General discussion about all Robot Framework related
    issues. Questions and problems can be sent to this list. Used also
    for information sharing for all users.

robotframework-[announce](http://groups.google.com/group/robotframework-announce)
: An announcements-only mailing list where only moderators can send
    messages. All announcements are sent also to the
    robotframework-users mailing list so there is no need to join both
    lists.

robotframework-[devel](http://groups.google.com/group/robotframework-devel)
: Discussion about Robot Framework development.

