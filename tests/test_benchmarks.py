import sys
from decimal import Decimal

import pytest
from pytest import param as p

from jschon.json import JSON
from jschon.jsonschema import JSONSchema
from tests import metaschema_uri_2020_12, example_schema, example_valid, example_invalid


@pytest.mark.parametrize('value', (
        p(None, id='null'),
        p(True, id='bool'),
        p(sys.maxsize, id='int'),
        p(1.1111111111, id='float'),
        p(sys.float_info.max, id='max float'),
        p(Decimal('100.00'), id='decimal int'),
        p(Decimal('99.9999'), id='decimal float'),
        p('Hello, World!', id='string'),
        p([], id='empty array'),
        p([1] * 10, id='10x int array'),
        p([1] * 100, id='100x int array'),
        p({}, id='empty object'),
        p(dict(zip(map(str, range(10)), [1] * 10)), id='10x int object'),
        p(dict(zip(map(str, range(100)), [1] * 100)), id='100x int object'),
        p(example_valid, id='simple example'),
        p(example_schema, id='complex example'),
))
def test_create_json(benchmark, value):
    benchmark(JSON, value)


@pytest.mark.parametrize('value', (
        p(example_valid, id='valid'),
        p(example_invalid, id='invalid'),
))
def test_evaluate_json(benchmark, request, value):
    json = JSON(value)
    schema = JSONSchema(example_schema, metaschema_uri=metaschema_uri_2020_12)
    scope = benchmark(schema.evaluate, json)
    assert scope.valid is (True if '[valid]' in request.node.name else False)


schema_tests = (
    p(True, id='bool'),
    p({}, id='empty'),
    p({"const": "foo"}, id='simple'),
    p(example_schema, id='complex'),
)


@pytest.mark.parametrize('value', schema_tests)
def test_create_schema(benchmark, value):
    benchmark(JSONSchema, value, metaschema_uri=metaschema_uri_2020_12)


@pytest.mark.parametrize('value', schema_tests)
def test_validate_schema(benchmark, value):
    schema = JSONSchema(value, metaschema_uri=metaschema_uri_2020_12)
    benchmark(schema.validate)
