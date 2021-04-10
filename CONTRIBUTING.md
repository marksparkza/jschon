# Contributing to Jschon

_These guidelines will be expanded as the project matures; for now, the intention
is simply to assist contributors with setting up a local environment for development
and testing._

## Submodules

The project uses git _submodules_ to incorporate the
[JSON-Schema-Test-Suite](https://github.com/marksparkza/JSON-Schema-Test-Suite),
as well as supported branches of
[json-schema-spec](https://github.com/json-schema-org/json-schema-spec)
(which provides the metaschema and vocabulary definition files).

Run the following command in your local copy of the Jschon repository
to check out all of the submodules' files:

    git submodule update --init --recursive

See [Git Tools - Submodules](https://git-scm.com/book/en/v2/Git-Tools-Submodules)
for further information about working with submodules.

## Development setup

With your Python virtual environment activated, install the project in editable
mode along with development dependencies:

    pip install -e .[dev]

## Benchmarking

Before starting any new work, run an initial benchmarking test in _autosave_ mode.
This will give you a baseline for performance testing of your changes:

    pytest tests/test_benchmarks.py --benchmark-autosave

You can later run a comparison against this baseline with:

    pytest tests/test_benchmarks.py --benchmark-compare

See the [pytest-benchmark documenation](https://pytest-benchmark.readthedocs.io/en/latest/usage.html#commandline-options)
for other `--benchmark-*` command line options. The Jschon project's `.gitignore`
excludes benchmarking output from source control, so feel free to experiment!

## Running the tests

To run all of the tests - unit tests, benchmarking tests, and the test suites
(excluding optional tests) for all supported versions of the JSON Schema spec -
simply type:

    pytest

Jschon defines a few additional pytest command line options relating to the JSON
Schema Test Suite:

    --testsuite-version=VERSION     Only run tests for the specified version
    --testsuite-optionals           Include optional tests
    --testsuite-formats             Include format tests

So, for example, you can run the full 2020-12 test suite, including optional and format
tests (which Jschon does not currently support), by typing:

    pytest tests/test_suite.py --testsuite-version=2020-12 --testsuite-optionals --testsuite-formats

Typing `pytest --help` will show the above options, including the available `VERSION`
specifiers.
