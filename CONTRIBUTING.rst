.. highlight:: none

Contributing
============
Please create an `issue <https://github.com/marksparkza/jschon/issues/new/choose>`_
for any feature request, question, suggestion or bug report.

PRs are welcome for minor fixes, doc typos and clarifications, added test coverage,
and to address updates or omissions from supported specifications.

PRs involving complex changes to jschon modules are unlikely to be merged
while the development status of the library is alpha (v0.x). There are currently
no plans for a v1.0 release. For advanced use cases, and in the spirit of open
source software development, you are encouraged to fork and republish the
library under any name of your choosing.

jschon was originally created to solve a JSON translation problem using
JSON Schema and Python. It is intended to provide a starting point for
building JSON-related tools, extensions and applications.

Development
-----------
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

Testing
-------
To run the jschon tests, type::

    pytest

A default test run includes all unit tests and JSON Schema Test Suite versions
2019-09 and 2020-12. Optional and format tests are excluded. To customize running
of the test suite, jschon provides the following pytest command line options::

  --testsuite-version={2019-09,2020-12,next}
                        JSON Schema version to test. The option may be repeated
                        to test multiple versions. (default: {2019-09,2020-12})
  --testsuite-version-all
                        Test all available JSON Schema versions. Overrides
                        --testsuite-version
  --testsuite-optionals
                        Include optional tests.
  --testsuite-formats   Include format tests.
  --testsuite-file=TESTSUITE_FILE
                        Run only this file from the JSON Schema Test Suite.
                        Given as a path relative to the version directory in the
                        test suite, e.g. 'properties.json' or
                        'optional/bignum.json'. The option may be repeated to
                        run multiple files. Using this option causes
                        --testsuite-optionals and --testsuite-formats to be
                        ignored.
  --testsuite-description=TESTSUITE_DESCRIPTION
                        Run only tests where the test or test case description
                        matches the given regular expression. Matching is case
                        insensitive and not anchored to the start or end of
                        string.
  --testsuite-generate-status
                        Run all possible tests from all supported versions and
                        update the tests/suite_status.json file.  If a failed
                        test is already in tests/suite_status.json, its status
                        and reason are left as is.  Otherwise, all optional and
                        format tests that fail are given an 'xfail' with the
                        reason being 'optional' or 'format', respectively, while
                        other failures from the 'next' version are given an
                        'xfail' status with a None (JSON null) reason, which
                        should be set manually to an appropriate string.  All
                        other options are ignored when this option is passed.
                        NOTE: the tests/suite_status.json is updated IN PLACE,
                        overwriting the current contents.

The above options are printed under the section *JSON Schema Test Suite*
in the output of::

    pytest --help

Expected failures and skipped tests
+++++++++++++++++++++++++++++++++++

Many optional, format, and draft-next test cases are expected to fail, as recorded in
`tests/suite_status.json <https://github.com/marksparkza/jschon/blob/main/tests/suite_status.json>`_.
A status of ``xfail`` indicates an optional feature or format that is not currently supported.
A status of ``skip`` indicates a bug in the test that makes it impossible to pass.

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

Running the tests through tox
+++++++++++++++++++++++++++++
To run the tests against all supported versions of python (which must be available
on your system), type::

    tox

To pass arguments through to ``pytest``, use ``--`` to indicate the end of the ``tox``
arguments::

    tox -e py310 -- --capture=tee-sys --testsuite-version=next

Documentation
-------------
The jschon documentation is written in
`reStructuredText <https://www.sphinx-doc.org/en/master/usage/restructuredtext/index.html>`_.

To build the docs locally, install sphinx and co::

    pip install -e .[doc]

In the ``docs`` directory, type::

    make html

The HTML pages are written to ``docs/_build/html/``.
