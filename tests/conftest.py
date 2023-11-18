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
        help="JSON Schema version to test. The option may be repeated to test multiple versions. "
             "(default: {2019-09,2020-12})",
    )
    testsuite.addoption(
        "--testsuite-version-all",
        action="store_true",
        help="Test all available JSON Schema versions. Overrides --testsuite-version",
    )
    testsuite.addoption(
        "--testsuite-optionals",
        action="store_true",
        help="Include optional tests.",
    )
    testsuite.addoption(
        "--testsuite-formats",
        action="store_true",
        help="Include format tests.",
    )
    testsuite.addoption(
        "--testsuite-file",
        action="append",
        help="Run only this file from the JSON Schema Test Suite. Given as a path relative to the "
             "version directory in the test suite, e.g. 'properties.json' or 'optional/bignum.json'. "
             "The option may be repeated to run multiple files. "
             "Using this option causes --testsuite-optionals and --testsuite-formats to be ignored."
    )
    testsuite.addoption(
        "--testsuite-description",
        action="store",
        help="Run only tests where the test or test case description matches the given regular "
             "expression. Matching is case insensitive and not anchored to the start or end of string.",
    )
    testsuite.addoption(
        "--testsuite-generate-status",
        action="store_true",
        help="Run all possible tests from all supported versions and update the tests/suite_status.json "
             "file.  If a failed test is already in tests/suite_status.json, its status and reason are "
             "left as is.  Otherwise, all optional and format tests that fail are given an 'xfail' with "
             "the reason being 'optional' or 'format', respectively, while other failures from the 'next' "
             "version are given an 'xfail' status with a None (JSON null) reason, which should be set "
             "manually to an appropriate string.  All other options are ignored when this option is passed.  "
             "NOTE: the tests/suite_status.json is updated IN PLACE, overwriting the current contents.",
    )


@pytest.fixture(autouse=True)
def catalog():
    return create_catalog('2019-09', '2020-12', 'next')


@pytest.fixture(scope='session')
def debug():
    return _debug
