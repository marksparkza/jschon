import pathlib

import pytest

from jschon import Catalogue, JSON, JSONSchema, URI, JSONEvaluator
from jschon.utils import json_loadf
from tests import metaschema_uri_2019_09, metaschema_uri_2020_12

testsuite_dir = pathlib.Path(__file__).parent / 'JSON-Schema-Test-Suite'

Catalogue.add_directory(
    base_uri=URI('http://localhost:1234/'),
    base_dir=testsuite_dir / 'remotes',
)


def pytest_generate_tests(metafunc):
    argnames = ('metaschema_uri', 'schema', 'data', 'valid')
    argvalues = []
    testids = []

    only_version = metafunc.config.getoption("testsuite_version")
    include_optionals = metafunc.config.getoption("testsuite_optionals")
    include_formats = metafunc.config.getoption("testsuite_formats")

    base_dir = testsuite_dir / 'tests'
    version_dirs = {
        '2019-09': (metaschema_uri_2019_09, base_dir / 'draft2019-09'),
        '2020-12': (metaschema_uri_2020_12, base_dir / 'draft2020-12'),
    }

    for version, (metaschema_uri, dir_) in version_dirs.items():
        testfile_paths = []

        if not only_version or version == only_version:
            testfile_paths += sorted(dir_.glob('*.json'))
            if include_optionals:
                testfile_paths += sorted((dir_ / 'optional').glob('*.json'))
            if include_formats:
                testfile_paths += sorted((dir_ / 'optional' / 'format').glob('*.json'))

        for testfile_path in testfile_paths:
            testcases = json_loadf(testfile_path)
            for testcase in testcases:
                for test in testcase['tests']:
                    argvalues.append(pytest.param(metaschema_uri, testcase['schema'], test['data'], test['valid']))
                    testids.append(f"{version} -> {testfile_path.name} -> {testcase['description']} -> {test['description']}")

    metafunc.parametrize(argnames, argvalues, ids=testids)


def test_validate(metaschema_uri, schema, data, valid):
    json_schema = JSONSchema(schema, metaschema_uri=metaschema_uri)
    json_data = JSON(data)
    json_evaluator = JSONEvaluator(json_schema, json_data)
    result = json_evaluator.evaluate_instance()
    assert result['valid'] is valid
