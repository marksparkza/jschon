import sys
from decimal import Decimal

import pytest
from pytest import param

from jschon import JSON, JSONSchema
from tests import metaschema_uri_2020_12, example_schema, example_valid, example_invalid


def test_create_json(benchmark):
    benchmark(
        JSON, {
            'null': None,
            'bool': True,
            'int': sys.maxsize,
            'float': 1.234,
            'decimal': Decimal('99.99'),
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
    schema = JSONSchema(example_schema, metaschema_uri=metaschema_uri_2020_12)
    scope = benchmark(schema.evaluate, json)
    assert scope.valid is (True if '[valid]' in request.node.name else False)


def test_create_schema(benchmark):
    benchmark(JSONSchema, example_schema, metaschema_uri=metaschema_uri_2020_12)


def test_validate_schema(benchmark):
    schema = JSONSchema(example_schema, metaschema_uri=metaschema_uri_2020_12)
    benchmark(schema.validate)
