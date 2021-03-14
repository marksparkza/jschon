import pytest

import submodules
from jschon.catalogue import Catalogue
from jschon.json import JSON
from jschon.jsonschema import JSONSchema
from jschon.uri import URI
from jschon.utils import load_json
from tests import metaschema_uri

Catalogue.add_directory(
    base_uri=URI('http://localhost:1234/'),
    base_dir=submodules.rootdir / 'JSON-Schema-Test-Suite' / 'remotes',
)


def pytest_generate_tests(metafunc):
    argnames = ('schema', 'data', 'valid')
    argvalues = []
    testids = []

    only_version = metafunc.config.getoption("testsuite_version")
    include_optionals = metafunc.config.getoption("testsuite_optionals")
    include_formats = metafunc.config.getoption("testsuite_formats")

    base_dir = submodules.rootdir / 'JSON-Schema-Test-Suite' / 'tests'
    version_dirs = {
        '2019-09': base_dir / 'draft2019-09',
        '2020-12': base_dir / 'draft2020-12',
    }

    testfile_paths = []
    for version, dir_ in version_dirs.items():
        if not only_version or version == only_version:
            testfile_paths += sorted(dir_.glob('*.json'))
            if include_optionals:
                testfile_paths += sorted((dir_ / 'optional').glob('*.json'))
            if include_formats:
                testfile_paths += sorted((dir_ / 'optional' / 'format').glob('*.json'))

    for testfile_path in testfile_paths:
        testcases = load_json(testfile_path)
        for testcase in testcases:
            for test in testcase['tests']:
                argvalues.append(pytest.param(testcase['schema'], test['data'], test['valid']))
                testids.append(f"{testfile_path.name} -> {testcase['description']} -> {test['description']}")

    metafunc.parametrize(argnames, argvalues, ids=testids)


def test_validate(schema, data, valid):
    s = JSONSchema(schema, metaschema_uri=metaschema_uri)
    assert s.evaluate(JSON(data)).valid is valid
