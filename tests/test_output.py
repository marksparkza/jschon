import pytest
from pytest import param as p

from jschon import JSON, JSONSchema
from tests import metaschema_uri_2020_12, metaschema_uri_2019_09

schema_valid = {
    "$id": "http://example.com",
    "if": {
        "prefixItems": [{"const": 1}]
    },
    "then": {
        "contains": {"multipleOf": 2}
    },
    "else": {
        "contains": {"multipleOf": 3}
    }
}

schema_invalid = {
    "$id": "http://example.com",
    "if": {
        "prefixItems": []
    },
    "then": {
        "contains": {"multipleOf": "2"}
    },
    "else": {
        "contains": {"multipleOf": -3}
    }
}

schema_invalid_errors = [
    {"instanceLocation": "/if/prefixItems",
     "keywordLocation": "/allOf/1/$ref/properties/if/$dynamicRef/allOf/1/$ref/properties/prefixItems/$ref/minItems",
     "absoluteKeywordLocation": "https://json-schema.org/draft/2020-12/meta/applicator#/$defs/schemaArray/minItems",
     "error": "The array has too few elements (minimum 1)"},
    {"instanceLocation": "/then/contains/multipleOf",
     "keywordLocation": "/allOf/1/$ref/properties/then/$dynamicRef/allOf/1/$ref/properties/contains/$dynamicRef/allOf/3/$ref/properties/multipleOf/type",
     "absoluteKeywordLocation": "https://json-schema.org/draft/2020-12/meta/validation#/properties/multipleOf/type",
     "error": "The instance must be of type \"number\""},
    {"instanceLocation": "/else/contains/multipleOf",
     "keywordLocation": "/allOf/1/$ref/properties/else/$dynamicRef/allOf/1/$ref/properties/contains/$dynamicRef/allOf/3/$ref/properties/multipleOf/exclusiveMinimum",
     "absoluteKeywordLocation": "https://json-schema.org/draft/2020-12/meta/validation#/properties/multipleOf/exclusiveMinimum",
     "error": "The value must be greater than 0"},
]


@pytest.mark.parametrize('example, valid', [
    (schema_valid, True),
    (schema_invalid, False),
])
def test_validate_schema_flag(example, valid):
    schema = JSONSchema(example, metaschema_uri=metaschema_uri_2020_12)
    result = schema.metaschema.evaluate(schema).output('flag')
    assert result == {
        'valid': valid
    }


@pytest.mark.parametrize('example, valid, errors', [
    (schema_valid, True, None),
    (schema_invalid, False, schema_invalid_errors),
])
def test_validate_schema_basic(example, valid, errors):
    schema = JSONSchema(example, metaschema_uri=metaschema_uri_2020_12)
    result = schema.metaschema.evaluate(schema).output('basic')
    assert result['valid'] is valid
    if valid:
        assert 'errors' not in result
        assert result['annotations']
        assert isinstance(result['annotations'], list)
    else:
        assert 'annotations' not in result
        assert result['errors']
        for error in errors:
            assert error in result['errors']


output_1_2 = {"valid": True,
              "annotations": [{"instanceLocation": "",
                               "keywordLocation": "/if/prefixItems",
                               "absoluteKeywordLocation": "http://example.com#/if/prefixItems",
                               "annotation": 0},
                              {"instanceLocation": "",
                               "keywordLocation": "/then/contains",
                               "absoluteKeywordLocation": "http://example.com#/then/contains",
                               "annotation": [1]}]}

output_1_3 = {"valid": False,
              "errors": [{"instanceLocation": "",
                          "keywordLocation": "/then/contains",
                          "absoluteKeywordLocation": "http://example.com#/then/contains",
                          "error": "The array does not contain any element that is valid against the \"contains\" subschema"},
                         {"instanceLocation": "/0",
                          "keywordLocation": "/then/contains/multipleOf",
                          "absoluteKeywordLocation": "http://example.com#/then/contains/multipleOf",
                          "error": "The value must be a multiple of 2"},
                         {"instanceLocation": "/1",
                          "keywordLocation": "/then/contains/multipleOf",
                          "absoluteKeywordLocation": "http://example.com#/then/contains/multipleOf",
                          "error": "The value must be a multiple of 2"}]}

output_2_2 = {"valid": False,
              "errors": [{'instanceLocation': '',
                          'keywordLocation': '/if/prefixItems',
                          'absoluteKeywordLocation': 'http://example.com#/if/prefixItems',
                          'error': [0]},
                         {'instanceLocation': '/0',
                          'keywordLocation': '/if/prefixItems/0/const',
                          'absoluteKeywordLocation': 'http://example.com#/if/prefixItems/0/const',
                          'error': 'The instance value must be equal to the defined constant'},
                         {"instanceLocation": "",
                          "keywordLocation": "/else/contains",
                          "absoluteKeywordLocation": "http://example.com#/else/contains",
                          "error": "The array does not contain any element that is valid against the \"contains\" subschema"},
                         {"instanceLocation": "/0",
                          "keywordLocation": "/else/contains/multipleOf",
                          "absoluteKeywordLocation": "http://example.com#/else/contains/multipleOf",
                          "error": "The value must be a multiple of 3"},
                         {"instanceLocation": "/1",
                          "keywordLocation": "/else/contains/multipleOf",
                          "absoluteKeywordLocation": "http://example.com#/else/contains/multipleOf",
                          "error": "The value must be a multiple of 3"}]}

output_2_3 = {"valid": True,
              "annotations": [{"instanceLocation": "",
                               "keywordLocation": "/else/contains",
                               "absoluteKeywordLocation": "http://example.com#/else/contains",
                               "annotation": [1]}]}

instance_tests = (
    p([1, 2], True, output_1_2),
    p([1, 3], False, output_1_3),
    p([2, 2], False, output_2_2),
    p([2, 3], True, output_2_3),
)


@pytest.mark.parametrize('example, valid, output', instance_tests)
def test_evaluate_instance_flag(example, valid, output):
    schema = JSONSchema(schema_valid, metaschema_uri=metaschema_uri_2020_12)
    result = schema.evaluate(JSON(example)).output('flag')
    assert result == {
        'valid': valid
    }


@pytest.mark.parametrize('example, valid, output', instance_tests)
def test_evaluate_instance_basic(example, valid, output):
    schema = JSONSchema(schema_valid, metaschema_uri=metaschema_uri_2020_12)
    result = schema.evaluate(JSON(example)).output('basic')
    assert result['valid'] is valid
    assert result == output


# https://github.com/marksparkza/jschon/issues/8
array_schema = {
    "$id": "http://example.com",
    "items": {"type": "integer", "description": "an item"}
}
array_input_0 = [1, 2]
array_input_1 = [1, 'foo']
array_input_2 = ['bar', 2]

array_output_0 = {'valid': True,
                  'annotations': [{'instanceLocation': '',
                                   'keywordLocation': '/items',
                                   'absoluteKeywordLocation': 'http://example.com#/items',
                                   'annotation': True},
                                  {'instanceLocation': '/0',
                                   'keywordLocation': '/items/description',
                                   'absoluteKeywordLocation': 'http://example.com#/items/description',
                                   'annotation': 'an item'},
                                  {'instanceLocation': '/1',
                                   'keywordLocation': '/items/description',
                                   'absoluteKeywordLocation': 'http://example.com#/items/description',
                                   'annotation': 'an item'}]}
array_output_1 = {'valid': False,
                  'errors': [{'instanceLocation': '/1',
                              'keywordLocation': '/items/type',
                              'absoluteKeywordLocation': 'http://example.com#/items/type',
                              'error': 'The instance must be of type "integer"'}]}
array_output_2 = {'valid': False,
                  'errors': [{'instanceLocation': '/0',
                              'keywordLocation': '/items/type',
                              'absoluteKeywordLocation': 'http://example.com#/items/type',
                              'error': 'The instance must be of type "integer"'}]}


@pytest.mark.parametrize('input, output', [
    (array_input_0, array_output_0),
    (array_input_1, array_output_1),
    (array_input_2, array_output_2),
])
def test_array_item_output(input, output):
    schema = JSONSchema(array_schema, metaschema_uri=metaschema_uri_2020_12)
    result = schema.evaluate(JSON(input)).output('basic')
    assert result == output


contains_if_schema = {
    "$id": "http://example.com",
    "contains": {
        "if": {"type": "integer"},
        "else": {"type": "string"}
    }
}
array_input_3 = ['baz', 3.1]

contains_if_output_1 = {'valid': True,
                        'annotations': [{'instanceLocation': '',
                                         'keywordLocation': '/contains',
                                         'absoluteKeywordLocation': 'http://example.com#/contains',
                                         'annotation': [0, 1]}]}
contains_if_output_2 = contains_if_output_1
contains_if_output_3 = {'valid': True,
                        'annotations': [{'instanceLocation': '',
                                         'keywordLocation': '/contains',
                                         'absoluteKeywordLocation': 'http://example.com#/contains',
                                         'annotation': [0]}]}


@pytest.mark.parametrize('input, output', [
    (array_input_1, contains_if_output_1),
    (array_input_2, contains_if_output_2),
    (array_input_3, contains_if_output_3),
])
def test_contains_if_output(input, output):
    schema = JSONSchema(contains_if_schema, metaschema_uri=metaschema_uri_2020_12)
    result = schema.evaluate(JSON(input)).output('basic')
    assert result == output


# https://github.com/marksparkza/jschon/issues/15
@pytest.mark.parametrize('foo_schema, valid', [
    (False, False),
    (True, True),
    ({}, True),
    ({"not": {}}, False),
])
def test_ref_absolute_uri(foo_schema, valid):
    schema = JSONSchema({
        "$id": "http://example.com",
        "$ref": "#/$defs/foo",
        "$defs": {
            "foo": foo_schema
        }
    }, metaschema_uri=metaschema_uri_2020_12)
    result = schema.evaluate(JSON({})).output('verbose')
    key = 'annotations' if valid else 'errors'
    assert result[key][0]['absoluteKeywordLocation'] == 'http://example.com#/$defs/foo'


def test_dynamic_ref_absolute_uri():
    schema = JSONSchema({
        "$id": "http://example.com",
        "$dynamicRef": "#item",
        "$defs": {
            "foo": {
                "$dynamicAnchor": "item"
            }
        }
    }, metaschema_uri=metaschema_uri_2020_12)
    result = schema.evaluate(JSON({})).output('verbose')
    assert result['annotations'][0]['absoluteKeywordLocation'] == 'http://example.com#/$defs/foo'


def test_recursive_ref_absolute_uri():
    schema = JSONSchema({
        "$id": "http://example.com",
        "$recursiveAnchor": True,
        "items": {
            "$recursiveRef": "#"
        },
        "type": ["array", "string"]
    }, metaschema_uri=metaschema_uri_2019_09)
    result = schema.evaluate(JSON([["foo"]])).output('verbose')
    assert result['annotations'][0]['annotations'][0]['absoluteKeywordLocation'] == 'http://example.com'


def test_chained_ref_absolute_uri():
    schema = JSONSchema({
        "$id": "http://example.com",
        "$ref": "#/$defs/foo",
        "$defs": {
            "foo": {"$ref": "#/$defs/bar"},
            "bar": True
        }
    }, metaschema_uri=metaschema_uri_2020_12)
    result = schema.evaluate(JSON({})).output('verbose')
    assert result['annotations'][0]['absoluteKeywordLocation'] == 'http://example.com#/$defs/foo'
    assert result['annotations'][0]['annotations'][0]['absoluteKeywordLocation'] == 'http://example.com#/$defs/bar'
