import pathlib

import pytest

from jschon import JSON, JSONSchema
from jschon.jsonpatch import JSONPatch
from jschon.utils import json_loadf

example_dir = pathlib.Path(__file__).parent / 'data' / 'translation'


def pytest_generate_tests(metafunc):
    if metafunc.definition.name == 'test_translate_json':
        argnames = ('schema', 'data', 'patches', 'translations')
        argvalues = []
        testids = []

        testfile_paths = sorted(example_dir.glob('*.json'))
        for testfile_path in testfile_paths:
            testcase = json_loadf(testfile_path)
            for n, test in enumerate(testcase['tests']):
                argvalues += [pytest.param(testcase['schema'], test['data'], test['patches'], test['translations'])]
                testids += [f'{testfile_path.name}/{n}']

        metafunc.parametrize(argnames, argvalues, ids=testids)


def test_translate_json(schema, data, patches, translations):
    schema = JSONSchema(schema)
    data = JSON(data)
    patches = {
        scheme: JSONPatch(*patch)
        for scheme, patch in patches.items()
    }

    # sanity checks
    assert schema.validate().valid is True
    assert patches.keys() == translations.keys()
    for scheme, patch in patches.items():
        assert patch.evaluate(None) == translations[scheme]

    result = schema.evaluate(data)
    assert result.valid
    for scheme, patch in patches.items():
        assert result.output('patch', scheme=scheme) == patch
    for scheme, translation in translations.items():
        assert result.output('translation', scheme=scheme) == translation
