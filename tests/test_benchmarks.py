import pathlib
import sys
from decimal import Decimal

import pytest
from pytest import param as p

from jschon.json import JSON
from jschon.jsonschema import JSONSchema
from jschon.utils import load_json
from tests import metaschema_uri

example_1_json = load_json(
    pathlib.Path(__file__).parent /
    'test_suite/JSON-Schema-Test-Suite/tests/draft2019-09/recursiveRef.json'
)
example_2_json = load_json(
    pathlib.Path(__file__).parent /
    'test_suite/JSON-Schema-Test-Suite/tests/draft2019-09/unevaluatedProperties.json'
)


@pytest.mark.parametrize('value, jsontype', (
        p(None, 'null', id='null'),
        p(True, 'boolean', id='bool'),
        p(sys.maxsize, 'integer', id='int'),
        p(1.1111111111, 'number', id='float'),
        p(sys.float_info.max, 'number', id='max float'),
        p(Decimal('100.00'), 'integer', id='decimal int'),
        p(Decimal('99.9999'), 'number', id='decimal float'),
        p('Hello, World!', 'string', id='string'),
        p([], 'array', id='empty array'),
        p([1] * 10, 'array', id='10x int array'),
        p([1] * 100, 'array', id='100x int array'),
        p({}, 'object', id='empty object'),
        p(dict(zip(map(str, range(10)), [1] * 10)), 'object', id='10x int object'),
        p(dict(zip(map(str, range(100)), [1] * 100)), 'object', id='100x int object'),
        p(example_1_json, 'array', id='complex example 1'),
        p(example_2_json, 'array', id='complex example 2'),
))
def test_create_json(benchmark, value, jsontype):
    result = benchmark(lambda v: JSON(v), value)
    assert result.istype(jsontype)


@pytest.mark.parametrize('value', (
        p(True, id='boolean'),
        p({}, id='empty'),
        p({"const": "foo"}, id='const'),
))
def test_create_schema(benchmark, value):
    benchmark(lambda v: JSONSchema(v, metaschema_uri=metaschema_uri), value)
