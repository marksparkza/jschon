import pytest

from jschon.jsonschema import JSONSchema
from tests import metaschema_uri


@pytest.mark.parametrize('example', [
    {"not": {"type": ["array", "object"]}},
    {"if": {"type": "integer"},
     "then": {"minimum": 1},
     "else": {"enum": ["foo", "bar"]}},
    {"items": {"enum": ["a", "b", "c"]},
     "contains": {"const": "b"}},
    {"additionalItems": True},
    {"unevaluatedItems": False},
    {"additionalProperties": True},
    {"unevaluatedProperties": False},
    {"propertyNames": {"pattern": "^x"}},
])
def test_applicator(example):
    schema = JSONSchema(example, metaschema_uri=metaschema_uri)
    for applicator_key, applicator_val in example.items():
        assert isinstance(schema[applicator_key], JSONSchema)
        assert schema[applicator_key].value == applicator_val


@pytest.mark.parametrize('example', [
    {"allOf": [{"type": "string"}, {"maxLength": 10}]},
    {"anyOf": [{"type": "number"}, {"const": True}]},
    {"oneOf": [{"type": "array"}, {"const": True}],
     "items": [{"const": 1}, {"const": 2}, {"const": 3}]},
])
def test_array_applicator(example):
    schema = JSONSchema(example, metaschema_uri=metaschema_uri)
    for applicator_key, applicator_val in example.items():
        for i, item in enumerate(applicator_val):
            assert isinstance(schema[applicator_key][i], JSONSchema)
            assert schema[applicator_key][i].value == item


@pytest.mark.parametrize('example', [
    {"$defs": {"foo": {"type": "integer"}}},
    {"dependentSchemas": {"foo": True, "bar": False}},
    {"properties": {"foo": {"type": "integer"}, "bar": {"type": "number"}},
     "patternProperties": {r"^x": {"type": "string"}}},
])
def test_property_applicator(example):
    schema = JSONSchema(example, metaschema_uri=metaschema_uri)
    for applicator_key, applicator_val in example.items():
        for prop_key, prop_val in applicator_val.items():
            assert isinstance(schema[applicator_key][prop_key], JSONSchema)
            assert schema[applicator_key][prop_key].value == prop_val
