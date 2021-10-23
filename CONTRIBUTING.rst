.. highlight:: none

Contributing
============
Contributions in the form of `issues <https://github.com/marksparkza/jschon/issues>`_
are welcome.

Kindly note that the development status of the project is **alpha**.
API and internals may change from one release to the next.

If you have an idea for a code contribution, feel free to reach out on the
`JSON Schema Slack <https://json-schema.org/slack>`_ (@marksparkza) to discuss.

For details on setting up a local environment for development and testing,
read on!

Submodules
----------
The project uses git submodules to incorporate the
`JSON Schema Test Suite <https://github.com/json-schema-org/JSON-Schema-Test-Suite>`_,
as well as supported branches of the
`JSON Schema Specification <https://github.com/json-schema-org/json-schema-spec>`_
repository which provides the meta-schema and vocabulary definition files.

Run the following command in your local copy of jschon to check out all
the submodule files::

    git submodule update --init --recursive

Development setup
-----------------
With your Python virtual environment activated, install the project in editable
mode along with development dependencies::

    pip install -e .[dev]

Benchmarking
------------
Before starting any new work, you might want to run an initial benchmarking
test. This will give you a baseline for performance testing of your changes::

    pytest tests/test_benchmarks.py --benchmark-autosave

You can later run a comparison against this baseline with::

    pytest tests/test_benchmarks.py --benchmark-compare

See the `pytest-benchmark documentation <https://pytest-benchmark.readthedocs.io/en/latest/usage.html#commandline-options>`_
for other ``--benchmark-*`` command line options. The jschon project's ``.gitignore``
excludes benchmarking output from source control, so feel free to experiment!

Running the tests
-----------------
To run all of the tests -- unit tests, benchmarking tests, and the test suites
(excluding optional and format tests) for all supported versions of the JSON Schema
spec -- simply type::

    pytest

jschon provides the following pytest command line options::

    --testsuite-version={2019-09,2020-12}  Only run tests for the specified version
    --testsuite-optionals                  Include optional tests
    --testsuite-formats                    Include format tests

So, for example, you can run the full 2020-12 test suite, including optional and format
tests (which jschon does not currently support), by typing::

    pytest tests/test_suite.py --testsuite-version=2020-12 --testsuite-optionals --testsuite-formats

