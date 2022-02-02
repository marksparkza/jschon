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

jschon provides the following pytest command line options::

    --testsuite-version={2019-09,2020-12}  Only run tests for the specified version
    --testsuite-optionals                  Include optional tests
    --testsuite-formats                    Include format tests
