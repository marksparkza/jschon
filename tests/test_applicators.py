import pytest

from jschon.json import JSON
from jschon.jsonschema import JSONSchema
from tests import metaschema_uri_2020_12


@pytest.mark.parametrize('example, valid_json, invalid_json', [
    ({"not": {"type": ["array", "object"]}}, "valid", ["invalid"]),
    ({"if": {"type": "integer"},
      "then": {"minimum": 1},
      "else": {"enum": ["foo", "bar"]}}, 5, "invalid"),
    ({"contains": {"const": "a"}}, ["b", "a"], ["b", "c"]),
    ({"items": {"const": "a"}}, ["a", "a"], ["a", "b"]),
    ({"unevaluatedItems": False}, [], ["invalid"]),
    ({"additionalProperties": {"const": "a"}}, {"valid": "a"}, {"invalid": "b"}),
    ({"unevaluatedProperties": False}, {}, {"invalid": True}),
    ({"propertyNames": {"pattern": "^v"}}, {"valid": True}, {"invalid": True}),
])
def test_applicator(example, valid_json, invalid_json):
    schema = JSONSchema(example, metaschema_uri=metaschema_uri_2020_12)
    for applicator_key, applicator_val in example.items():
        assert isinstance(schema[applicator_key], JSONSchema)
        assert schema[applicator_key].data == applicator_val

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
        for i, item in enumerate(applicator_val):
            assert isinstance(schema[applicator_key][i], JSONSchema)
            assert schema[applicator_key][i].data == item

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
        for prop_key, prop_val in applicator_val.items():
            assert isinstance(schema[applicator_key][prop_key], JSONSchema)
            assert schema[applicator_key][prop_key].data == prop_val

    assert schema.evaluate(JSON(valid_json)).valid is True
    assert schema.evaluate(JSON(invalid_json)).valid is False


@pytest.mark.parametrize('example, expected_error_paths', [
    ({"additionalProperties": False}, {"/additionalProperties"}),
    ({"properties": {"foo": False},
      "additionalProperties": False}, {"/properties", "/properties/foo"}),
    ({"properties": {"oof": False},
      "additionalProperties": False}, {"/additionalProperties"}),
    ({"patternProperties": {"o+": False},
      "additionalProperties": False}, {"/patternProperties", "/patternProperties/o+"}),
    ({"patternProperties": {"n+": False},
      "additionalProperties": False}, {"/additionalProperties"}),
])
def test_additional_properties(example, expected_error_paths):
    schema = JSONSchema(example, metaschema_uri=metaschema_uri_2020_12)
    data = JSON({"foo": "bar"})
    result = schema.evaluate(data)
    actual_error_paths = {
        error['keywordLocation'] for error in result.output('basic')['errors']
    }
    assert actual_error_paths == expected_error_paths


@pytest.mark.parametrize('example, expected_error_paths', [
    ({"items": False}, {"/items"}),
    ({"items": False,
      "prefixItems": [False]}, {"/prefixItems", "/prefixItems/0"}),
])
def test_items(example, expected_error_paths):
    schema = JSONSchema(example, metaschema_uri=metaschema_uri_2020_12)
    data = JSON(["foo"])
    result = schema.evaluate(data)
    actual_error_paths = {
        error['keywordLocation'] for error in result.output('basic')['errors']
    }
    assert actual_error_paths == expected_error_paths
