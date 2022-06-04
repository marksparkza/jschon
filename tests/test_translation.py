import pathlib
from datetime import datetime
from urllib.parse import urlparse

import pytest

from jschon import JSON, JSONSchema
from jschon.jsonpatch import JSONPatch
from jschon.translation import translation_filter
from jschon.utils import json_loadf

translation_tests_dir = pathlib.Path(__file__).parent.parent / 'jschon' / 'catalog' / 'json-translation-vocabulary' / 'tests'
iso19115_to_datacite_dir = translation_tests_dir / 'iso19115-to-datacite'


@translation_filter('date-to-year')
def date_to_year(date: str) -> int:
    return datetime.strptime(date, '%Y-%m-%d').year


@translation_filter('base-url')
def base_url(url: str) -> str:
    u = urlparse(url)
    return f'{u.scheme}://{u.netloc}'


def pytest_generate_tests(metafunc):
    if metafunc.definition.name == 'test_translate_json':
        argnames = ('schema', 'data', 'patches', 'translations')
        argvalues = []
        testids = []

        testfile_paths = sorted(translation_tests_dir.glob('*.json'))
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


def test_translate_iso19115_to_datacite():
    input_schema = JSONSchema.loadf(iso19115_to_datacite_dir / 'iso19115-schema-excerpt.json')
    input_json = JSON.loadf(iso19115_to_datacite_dir / 'iso19115-example.json')
    output_schema = JSONSchema.loadf(iso19115_to_datacite_dir / 'datacite-schema-excerpt.json')
    output_json = JSON.loadf(iso19115_to_datacite_dir / 'datacite-example-translated.json')

    # sanity checks
    assert input_schema.validate().valid
    assert input_schema.evaluate(input_json).valid
    assert output_schema.validate().valid
    assert output_schema.evaluate(output_json).valid

    result = input_schema.evaluate(input_json)
    patch = result.output('patch', scheme='datacite')
    translation = result.output('translation', scheme='datacite')

    assert JSONPatch(*patch).evaluate(None) == translation

    # work in progress
    # assert translation == output_json
    assert translation.keys() == output_json.keys()
    for k in translation:
        if k == 'contributors':
            # todo: resolve leftover empty arrays/objects when there are
            #  no source values to fill them
            continue
        assert translation[k] == output_json[k]
