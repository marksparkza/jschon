import pytest

from jschon.json import JSON
from jschon.jsonschema import *
from tests import metaschema_uri_2020_12


@pytest.mark.parametrize('example, valid_json, invalid_json', [
    ({"not": {"type": ["array", "object"]}}, "valid", ["invalid"]),
    ({"if": {"type": "integer"},
      "then": {"minimum": 1},
      "else": {"enum": ["foo", "bar"]}}, 5, "invalid"),
    ({"contains": {"const": "a"}}, ["a", "b"], ["b", "c"]),
    ({"items": {"const": "a"}}, ["a", "a"], ["a", "b"]),
    ({"unevaluatedItems": False}, [], ["invalid"]),
    ({"additionalProperties": {"const": "a"}}, {"valid": "a"}, {"invalid": "b"}),
    ({"unevaluatedProperties": False}, {}, {"invalid": True}),
    ({"propertyNames": {"pattern": "^v"}}, {"valid": True}, {"invalid": True}),
])
def test_applicator(example, valid_json, invalid_json):
    schema = JSONSchema(example, metaschema_uri=metaschema_uri_2020_12)
    for applicator_key, applicator_val in example.items():
        assert schema.keywords[applicator_key].applicator_cls is Applicator
        assert isinstance(schema[applicator_key], JSONSchema)
        assert schema[applicator_key].value == applicator_val

    assert schema.evaluate(JSON(valid_json)).valid is True
    assert schema.evaluate(JSON(invalid_json)).valid is False


@pytest.mark.parametrize('example, valid_json, invalid_json', [
    ({"allOf": [{"type": "string"}, {"maxLength": 10}]}, "valid", "invalid string"),
    ({"anyOf": [{"type": "number"}, {"const": True}]}, 5, "invalid"),
    ({"oneOf": [{"type": "array"}, {"const": True}],
      "prefixItems": [{"const": 1}, {"const": 2}, {"const": 3}]}, [1], False),
])
def test_array_applicator(example, valid_json, invalid_json):
    schema = JSONSchema(example, metaschema_uri=metaschema_uri_2020_12)
    for applicator_key, applicator_val in example.items():
        assert schema.keywords[applicator_key].applicator_cls is ArrayApplicator
        for i, item in enumerate(applicator_val):
            assert isinstance(schema[applicator_key][i], JSONSchema)
            assert schema[applicator_key][i].value == item

    assert schema.evaluate(JSON(valid_json)).valid is True
    assert schema.evaluate(JSON(invalid_json)).valid is False


@pytest.mark.parametrize('example, valid_json, invalid_json', [
    ({"$ref": "#/$defs/foo",
      "$defs": {"foo": {"type": "integer"}}}, 1, "invalid"),
    ({"dependentSchemas": {"foo": True, "bar": False}}, {"foo": "valid"}, {"bar": "invalid"}),
    ({"properties": {"foo": {"type": "integer"}, "bar": {"type": "number"}},
      "patternProperties": {r"^x": {"type": "string"}}},
     {"foo": 1, "bar": 1.1, "xyz": "baz"}, {"foo": 1.1, "bar": "1.1", "xyz": False}),
])
def test_property_applicator(example, valid_json, invalid_json):
    schema = JSONSchema(example, metaschema_uri=metaschema_uri_2020_12)
    for applicator_key, applicator_val in example.items():
        if applicator_key == '$ref':
            continue
        assert schema.keywords[applicator_key].applicator_cls is PropertyApplicator
        for prop_key, prop_val in applicator_val.items():
            assert isinstance(schema[applicator_key][prop_key], JSONSchema)
            assert schema[applicator_key][prop_key].value == prop_val

    assert schema.evaluate(JSON(valid_json)).valid is True
    assert schema.evaluate(JSON(invalid_json)).valid is False
