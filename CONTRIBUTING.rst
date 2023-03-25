.. highlight:: none

Contributing
============
Feature requests, questions, suggestions and bug reports are all welcome as
`issues <https://github.com/marksparkza/jschon/issues/new/choose>`_.

If you would like to contribute to the development of jschon, please create an
issue to discuss any change before creating a pull request.

Development setup
-----------------
The project uses git submodules to incorporate the
`JSON Schema Test Suite <https://github.com/json-schema-org/JSON-Schema-Test-Suite>`_,
as well as supported branches of the
`JSON Schema Specification <https://github.com/json-schema-org/json-schema-spec>`_
repository which provides the meta-schema and vocabulary definition files.

Run the following command in your local copy of jschon to check out all
the submodule files::

    git submodule update --init --recursive

Create and activate a Python virtual environment, and install the project in
editable mode along with development dependencies::

    pip install -e .[dev]

Running the tests
-----------------
To run all the unit tests and test suites (excluding optional and format tests),
simply type::

    pytest

jschon provides the following pytest command line options, all of which only affect
how the standard JSON Schema Test Suite is run::

    --testsuite-version={2019-09,2020-12,next}  Only run tests for the specified version
    --testsuite-optionals                       Include optional tests (excluding formats)
    --testsuite-formats                         Include format tests
    --testsuite-file={suite-file.json}          Only run the specified file
    --testsuite-description={case description}  Only run cases matching the description
    --testsuite-generate-status                 See "Updating xfail and skip outcomes"

The ``--testsuite-version``, ``--testsuite-file``, and ``--testsuite-description`` can
each be passed more than once.  By default, the ``2019-09`` and ``2020-12`` suites
are run, and ``next`` is not.

The test file is a path relative to the version directory in the JSON Schema Test Suite,
e.g. ``properties.json`` or ``optional/bignum.json``.  Optional and format cases will
still only be run if the ``--testsuite-optionals`` or ``--testsuite-formats`` are passed.

The test case description (which is the description of the outer blocks within each
test file, rather than the individual test description) is a case-insensitive
substring match (not a regular expression).

Running the tests through ``tox``
+++++++++++++++++++++++++++++++++
To run the tests against all supported versions of python (which must be available
on your system), type::

    tox

To pass arguments through to ``pytest``, use ``--`` to indicate the end of the ``tox``
arguments::

    tox -e py310 -- --capture=tee-sys --testsuite-version=next

Expected failures and skipped tests
+++++++++++++++++++++++++++++++++++

Many optional, format, and draft-next test cases are expected to fail, as recorded in
`tests/suite_status.json <https://github.com/marksparkza/jschon/blob/main/tests/suite_status.json>`_.
Tests are given a status of ``skip`` if there is a bug in the test that makes them
impossible to pass.  Tests are given a status of ``xfail`` if they could theoretically
pass in the future, although there are no plans to support all optional features and formats.

Tests set to ``xfail`` will produce an ``xpass`` result if they begin to pass.

Updating ``xfail`` and ``skip`` test outcomes
+++++++++++++++++++++++++++++++++++++++++++++

The ``--testsuite-generate-status`` can be used to rewrite ``tests/suite_status.json``
based on the current pass/fail status.  If a failing test is already present in the
status JSON file, it is left as-is to preserve any custom reasons or statuses.
Otherwise, it is added to the file as an ``xfail`` status.  Tests in the file that
now pass will be removed.

This option causes all other options to be ignored, and always runs all versions of
all tests, including the optional and format tests.
