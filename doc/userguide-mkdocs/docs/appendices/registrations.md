# Registrations

This appendix lists file extensions, media types, and so on, that are
associated with Robot Framework.

## Suite file extensions

[Suite files](../creating-test-data/creating-test-suites.md#suite-files) with the following extensions are parsed automatically:

`.robot`{.file}
: Suite file using the [plain text data format](../creating-test-data/test-data-syntax.md#plain-text-data-format).

`.robot.rst`{.file}
: Suite file using the [reStructuredText data format](../creating-test-data/test-data-syntax.md#restructuredtext-data-format).

`.robot.md`{.file}
: Suite file using the [Markdown data format](../creating-test-data/test-data-syntax.md#markdown-data-format).

`.rbt`{.file}
: Suite file using the [JSON data format](../creating-test-data/test-data-syntax.md#json-data-format).

Using other extensions is possible, but it requires [separate configuration](../executing-tests/configuring-execution.md#selecting-files-to-parse).

## Resource file extensions

[Resource files](../creating-test-data/resource-files.md#resource-files) can use the following extensions:

`.resource`{.file}
: Recommended when using the plain text format.

`.robot`{.file}, `.txt`{.file} and `.tsv`{.file}
: Supported with the plain text format for backwards compatibility reasons.
    `.resource`{.file} is recommended and may be mandated in the future.

`.rst`{.file} and `.rest`{.file}
: Resource file using the [reStructuredText format](../creating-test-data/resource-files.md#resource-files-using-restructuredtext-format).

`.md`{.file} and `.markdown`{.file}
: Resource file using the [Markdown format](../creating-test-data/resource-files.md#resource-files-using-markdown-format).

`.rsrc`{.file} and `.json`{.file}
: Resource file using the [JSON format](../creating-test-data/resource-files.md#resource-files-using-json-format).

## Media type

The media type to use with Robot Framework data is `text/robotframework`.

## Remote server port

The default [remote server](../extending/remote-library.md#remote-library-interface) port is 8270. The port has been [registered by IANA](https://www.iana.org/assignments/service-names-port-numbers/service-names-port-numbers.xhtml?search=8270).

