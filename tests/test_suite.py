import pathlib
import warnings

import pytest

from jschon import JSON, JSONSchema, LocalSource, URI
from jschon.utils import json_loadf
from tests import metaschema_uri_2019_09, metaschema_uri_2020_12, metaschema_uri_next

testsuite_dir = pathlib.Path(__file__).parent / 'JSON-Schema-Test-Suite'


@pytest.fixture(autouse=True)
def setup_remotes(catalog):
    catalog.add_uri_source(
        URI('http://localhost:1234/'),
        LocalSource(testsuite_dir / 'remotes'),
    )


def pytest_generate_tests(metafunc):
    argnames = ('metaschema_uri', 'schema', 'data', 'valid')
    argvalues = []
    testids = []

    test_versions = metafunc.config.getoption("testsuite_version")
    include_optionals = metafunc.config.getoption("testsuite_optionals")
    include_formats = metafunc.config.getoption("testsuite_formats")
    test_files = metafunc.config.getoption("testsuite_file")
    test_descriptions = metafunc.config.getoption("testsuite_description")

    base_dir = testsuite_dir / 'tests'
    version_dirs = {
        '2019-09': (metaschema_uri_2019_09, base_dir / 'draft2019-09'),
        '2020-12': (metaschema_uri_2020_12, base_dir / 'draft2020-12'),
        'next': (metaschema_uri_next, base_dir / 'draft-next'),
    }

    for version, (metaschema_uri, dir_) in version_dirs.items():
        testfile_paths = []

        if not test_versions or version in test_versions:
            if test_files:
                for tf in test_files:
                    tf_path = dir_.joinpath(tf)
                    if tf_path.exists():
                        testfile_paths.append(tf_path)
                    else:
                        # Warn because it might exist under other versions
                        warnings.warn(f'Test suite file "{tf_path}" does not exist for "{version}"')

            else:
                testfile_paths += sorted(dir_.glob('*.json'))
                if include_optionals:
                    testfile_paths += sorted((dir_ / 'optional').glob('*.json'))
                if include_formats:
                    testfile_paths += sorted((dir_ / 'optional' / 'format').glob('*.json'))

        for testfile_path in testfile_paths:
            testcases = json_loadf(testfile_path)
            for testcase in testcases:
                for test in testcase['tests']:
                    if test_descriptions and not any(
                            s.lower() in testcase['description'].lower() or s.lower() in test['description'].lower()
                            for s in test_descriptions
                    ):
                        continue

                    argvalues.append(pytest.param(metaschema_uri, testcase['schema'], test['data'], test['valid']))
                    testids.append(f"{version} -> {testfile_path.name} -> {testcase['description']} -> {test['description']}")

    metafunc.parametrize(argnames, argvalues, ids=testids)


def test_validate(metaschema_uri, schema, data, valid):
    json_schema = JSONSchema(schema, metaschema_uri=metaschema_uri)
    json_data = JSON(data)
    result = json_schema.evaluate(json_data).valid
    assert result is valid
