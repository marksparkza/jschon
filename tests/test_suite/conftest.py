import pathlib

import pytest

from jschon.catalogue import Catalogue
from jschon.uri import URI
from jschon.utils import load_json

Catalogue.add_local(
    base_uri=URI('http://localhost:1234/'),
    base_dir=pathlib.Path(__file__).parent / 'JSON-Schema-Test-Suite' / 'remotes',
)


def pytest_generate_tests(metafunc):
    argnames = ('schema', 'data', 'valid')
    argvalues = []
    testids = []
    testsuite_dir = pathlib.Path(__file__).parent / 'JSON-Schema-Test-Suite' / 'tests' / 'draft2019-09'
    testfile_paths = sorted(testsuite_dir.glob('*.json'))
    if metafunc.config.getoption("optionals"):
        testfile_paths += sorted((testsuite_dir / 'optional').rglob('*.json'))
    for testfile_path in testfile_paths:
        testcases = load_json(testfile_path)
        for testcase in testcases:
            for test in testcase['tests']:
                argvalues.append(pytest.param(testcase['schema'], test['data'], test['valid']))
                testids.append(f"{testfile_path.name} -> {testcase['description']} -> {test['description']}")
    metafunc.parametrize(argnames, argvalues, ids=testids)
