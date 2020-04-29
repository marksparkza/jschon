import json
import pathlib

import pytest

from jschon.json import JSON
from jschon.schema import Schema


def pytest_generate_tests(metafunc):
    argnames = ('schema', 'data', 'valid')
    argvalues = []
    testids = []
    testsuite_dir = pathlib.Path('jsonschema_testsuite/tests/draft2019-09')
    testfile_paths = sorted(testsuite_dir.glob('*.json'))
    for testfile_path in testfile_paths:
        with testfile_path.open() as testfile:
            testcases = json.load(testfile)
            for testcase in testcases:
                for test in testcase['tests']:
                    argvalues.append(pytest.param(testcase['schema'], test['data'], test['valid']))
                    testids.append(f"{testsuite_dir.name} --> {testfile_path.name} --> {testcase['description']} --> {test['description']}")
    metafunc.parametrize(argnames, argvalues, ids=testids)


def test_validate(schema, data, valid):
    result = Schema(schema, metaschema_uri='https://json-schema.org/draft/2019-09/schema').evaluate(JSON(data))
    assert result.valid == valid
