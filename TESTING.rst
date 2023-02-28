.. highlight:: none

Running the tests
=================
jschon is tested using the
`JSON Schema Test Suite <https://github.com/json-schema-org/JSON-Schema-Test-Suite>`_
(excluding optional and format tests), along with custom unit tests that make
use of the `Hypothesis <https://hypothesis.readthedocs.io/>`_ testing library.

To run the tests, install jschon in editable mode, including testing dependencies::

    pip install -e git+https://github.com/marksparkza/jschon.git#egg=jschon[test]

Then, ``cd`` to the jschon source directory (``pip show jschon`` will give you
the location), and type ``tox``.

Note that a complete test run requires all of the supported Python versions
(3.8, 3.9, 3.10, 3.11) to be installed on your system.
