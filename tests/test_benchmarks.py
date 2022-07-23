import sys

import pytest
from pytest import param

from jschon import JSON, JSONSchema
from tests import example_schema, example_valid, example_invalid


def test_create_json(benchmark):
    benchmark(
        JSON, {
            'null': None,
            'bool': True,
            'int': sys.maxsize,
            'float': 1.234,
            'string': 'Hello, World!',
            'array': list(map(chr, range(10))),
            'object': dict(zip(map(str, range(10)), map(chr, range(10)))),
            'schema': example_schema,
        }
    )


@pytest.mark.parametrize('value', (
        param(example_valid, id='valid'),
        param(example_invalid, id='invalid'),
))
def test_evaluate_json(benchmark, request, value):
    json = JSON(value)
    schema = JSONSchema(example_schema)
    result = benchmark(schema.evaluate, json)
    assert result.valid is (True if '[valid]' in request.node.name else False)


def test_create_schema(benchmark):
    benchmark(JSONSchema, example_schema)


def test_validate_schema(benchmark):
    schema = JSONSchema(example_schema)
    benchmark(schema.validate)
