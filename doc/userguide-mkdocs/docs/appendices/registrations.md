
# Registrations


This appendix lists file extensions, media types, and so on, that are
associated with Robot Framework.


## Suite file extensions


[Suite files](../creating-test-data/creating-test-suites.md#suite-files) with the following extensions are parsed automatically:

`.robot`
    Suite file using the [plain text format](#plain-text-format).

`.robot.rst`
    Suite file using the [reStructuredText format](../creating-test-data/test-data-syntax.md#restructuredtext-format).

`.rbt`
    Suite file using the [JSON format](../creating-test-data/test-data-syntax.md#json-format).

Using other extensions is possible, but it requires [separate configuration](#separate-configuration).


## Resource file extensions


[Resource files](../creating-test-data/resource-and-variable-files.md#resource-files) can use the following extensions:

`.resource`
    Recommended when using the plain text format.

`.robot`, `.txt` and `.tsv`
    Supported with the plain text format for backwards compatibility reasons.
    `.resource` is recommended and may be mandated in the future.

`.rst` and `.rest`
    Resource file using the [reStructuredText format](#restructuredtext-format).

`.rsrc` and `.json`
    Resource file using the [JSON format](#json-format).


## Media type


The media type to use with Robot Framework data is `text/robotframework`.


## Remote server port


The default [remote server](#remote-server) port is 8270. The port has been [registered by IANA](#registered-by-iana).

