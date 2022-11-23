import pytest

from jschon import JSON, JSONSchema, URI

example_schema = {
    "$schema": "https://json-schema.org/draft/next/schema",
    "type": "array",
    "anyOf": [
        {"items": {"type": "integer"}},
        {"items": {"type": "string"}},
    ]
}

example_data = [
    ([1, 2], True),
    (['one', 'two'], True),
    ([1, 'two'], False),
    ([None, True], False),
]


@pytest.fixture(params=['flag', 'basic', 'hierarchical'])
def format(request):
    return request.param


@pytest.mark.parametrize('data, valid', example_data)
def test_output(data, valid, format, catalog):
    output = JSONSchema(example_schema).evaluate(JSON(data)).output(format)
    assert output['valid'] is valid

    output_schema = catalog.get_schema(URI(f'https://jschon.dev/output/{format}'))
    output_validity = output_schema.evaluate(JSON(output))
    print(output_validity.output('basic'))
    assert output_validity.valid is True
