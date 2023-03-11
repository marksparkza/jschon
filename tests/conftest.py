import hypothesis
import pytest
import sys

from jschon import create_catalog

if _debug := bool(sys.gettrace()):
    hypothesis.settings.register_profile('debug', deadline=None)
    hypothesis.settings.load_profile('debug')
else:
    hypothesis.settings.register_profile('test', deadline=1000)
    hypothesis.settings.load_profile('test')


def pytest_addoption(parser):
    testsuite = parser.getgroup("testsuite", "JSON Schema Test Suite")
    testsuite.addoption(
        "--testsuite-version",
        action="append",
        choices=["2019-09", "2020-12", "next"],
        help="JSON Schema version to test. The option may be repeated to test multiple versions. By default, all supported versions are tested.",
    )
    testsuite.addoption(
        "--testsuite-optionals",
        action="store_true",
        help="Include optional tests",
    )
    testsuite.addoption(
        "--testsuite-formats",
        action="store_true",
        help="Include format tests",
    )
    testsuite.addoption(
        "--testsuite-file",
        action="append",
        help="Run only this file from the JSON Schema test suite. The option may be repeated to run multiple files. Using this option causes --testsuite-optionals and --testsuite-formats to be ignored"
    )
    testsuite.addoption(
        "--testsuite-description",
        action="append",
        help="Run only test groups and tests whose descriptions contain the given substring. "
             "Matching is case insensitive. The option may be repeated.",
    )


@pytest.fixture(scope='module', autouse=True)
def catalog():
    return create_catalog('2019-09', '2020-12', 'next')


@pytest.fixture(scope='session')
def debug():
    return _debug
