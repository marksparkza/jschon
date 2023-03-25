import urllib.parse

import pytest
from hypothesis import given
from pytest import param as p

from jschon import JSON, JSONPointer, JSONSchema, URI, create_catalog
from jschon.json import false, true
from tests import example_invalid, example_schema, example_valid, metaschema_uri_2019_09, metaschema_uri_2020_12
from tests.strategies import *

schema_tests = (
    p(False, False, False, id='false'),
    p(True, True, True, id='true'),
    p({}, True, True, id='empty'),
    p({"not": {}}, False, False, id='not'),
    p({"const": example_valid}, True, False, id='simple'),
    p(example_schema, True, False, id='complex'),
)
json1 = JSON(example_valid)
json2 = JSON(example_invalid)


@pytest.mark.parametrize('example, json1_valid, json2_valid', schema_tests)
def test_schema_examples(example, json1_valid, json2_valid):
    schema = JSONSchema(example, metaschema_uri=metaschema_uri_2020_12)
    assert schema.validate().valid is True
    assert schema.data == example
    assert schema.type == "boolean" if isinstance(example, bool) else "object"
    assert schema.parent is None
    assert schema.key is None
    assert not schema.path
    assert schema.metaschema_uri == metaschema_uri_2020_12
    assert schema.evaluate(json1).valid is json1_valid
    assert schema.evaluate(json2).valid is json2_valid


@pytest.mark.parametrize('example', [
    {"type": "foo"},
    {"properties": {"bar": {"multipleOf": -3}}},
    {"allOf": [{"anyOf": []}]},
])
def test_invalid_schema(example):
    schema = JSONSchema(example, metaschema_uri=metaschema_uri_2020_12)
    assert schema.validate().valid is False


def assert_keyword_order(keyword_list, keyword_pairs):
    for (dependency, dependent) in keyword_pairs:
        try:
            assert keyword_list.index(dependency) < keyword_list.index(dependent)
        except ValueError:
            pass


@given(value=interdependent_keywords)
def test_keyword_dependency_resolution_2019_09(value: list):
    metaschema = create_catalog('2019-09').get_metaschema(metaschema_uri_2019_09)
    kwclasses = {
        key: kwclass for key in value if (kwclass := metaschema.kwclasses.get(key))
    }
    keywords = [
        kwclass.key for kwclass in JSONSchema._resolve_dependencies(kwclasses)
    ]
    assert_keyword_order(keywords, [
        ("properties", "additionalProperties"),
        ("properties", "unevaluatedProperties"),
        ("patternProperties", "additionalProperties"),
        ("patternProperties", "unevaluatedProperties"),
        ("additionalProperties", "unevaluatedProperties"),
        ("items", "additionalItems"),
        ("items", "unevaluatedItems"),
        ("additionalItems", "unevaluatedItems"),
        ("contains", "maxContains"),
        ("contains", "minContains"),
        ("maxContains", "minContains"),
        ("if", "then"),
        ("if", "else"),
        ("if", "unevaluatedItems"),
        ("then", "unevaluatedItems"),
        ("else", "unevaluatedItems"),
        ("allOf", "unevaluatedItems"),
        ("anyOf", "unevaluatedItems"),
        ("oneOf", "unevaluatedItems"),
        ("not", "unevaluatedItems"),
        ("if", "unevaluatedProperties"),
        ("then", "unevaluatedProperties"),
        ("else", "unevaluatedProperties"),
        ("dependentSchemas", "unevaluatedProperties"),
        ("allOf", "unevaluatedProperties"),
        ("anyOf", "unevaluatedProperties"),
        ("oneOf", "unevaluatedProperties"),
        ("not", "unevaluatedProperties"),
        ("contentMediaType", "contentSchema"),
    ])


@given(value=interdependent_keywords)
def test_keyword_dependency_resolution_2020_12(value: list):
    metaschema = create_catalog('2020-12').get_metaschema(metaschema_uri_2020_12)
    kwclasses = {
        key: kwclass for key in value if (kwclass := metaschema.kwclasses.get(key))
    }
    keywords = [
        kwclass.key for kwclass in JSONSchema._resolve_dependencies(kwclasses)
    ]
    assert_keyword_order(keywords, [
        ("properties", "additionalProperties"),
        ("properties", "unevaluatedProperties"),
        ("patternProperties", "additionalProperties"),
        ("patternProperties", "unevaluatedProperties"),
        ("additionalProperties", "unevaluatedProperties"),
        ("prefixItems", "items"),
        ("prefixItems", "unevaluatedItems"),
        ("items", "unevaluatedItems"),
        ("contains", "unevaluatedItems"),
        ("contains", "maxContains"),
        ("contains", "minContains"),
        ("maxContains", "minContains"),
        ("if", "then"),
        ("if", "else"),
        ("if", "unevaluatedItems"),
        ("then", "unevaluatedItems"),
        ("else", "unevaluatedItems"),
        ("allOf", "unevaluatedItems"),
        ("anyOf", "unevaluatedItems"),
        ("oneOf", "unevaluatedItems"),
        ("not", "unevaluatedItems"),
        ("if", "unevaluatedProperties"),
        ("then", "unevaluatedProperties"),
        ("else", "unevaluatedProperties"),
        ("dependentSchemas", "unevaluatedProperties"),
        ("allOf", "unevaluatedProperties"),
        ("anyOf", "unevaluatedProperties"),
        ("oneOf", "unevaluatedProperties"),
        ("not", "unevaluatedProperties"),
        ("contentMediaType", "contentSchema"),
    ])


# https://json-schema.org/draft/2020-12/json-schema-core.html#idExamples
id_example = {
    "$id": "https://example.com/root.json",
    "$defs": {
        "A": {"$anchor": "foo"},
        "B": {
            "$id": "other.json",
            "$defs": {
                "X": {"$anchor": "bar"},
                "Y": {
                    "$id": "t/inner.json",
                    "$anchor": "bar"
                }
            }
        },
        "C": {
            "$id": "urn:uuid:ee564b8a-7a87-4125-8c96-e9f123d6766f"
        }
    }
}


@pytest.mark.parametrize('ptr, base_uri', [
    ('#', 'https://example.com/root.json'),
    ('#/$defs/A', 'https://example.com/root.json'),
    ('#/$defs/B', 'https://example.com/other.json'),
    ('#/$defs/B/$defs/X', 'https://example.com/other.json'),
    ('#/$defs/B/$defs/Y', 'https://example.com/t/inner.json'),
    ('#/$defs/C', 'urn:uuid:ee564b8a-7a87-4125-8c96-e9f123d6766f'),
])
def test_base_uri(ptr: str, base_uri: str):
    rootschema = JSONSchema(id_example, metaschema_uri=metaschema_uri_2020_12)
    schema: JSONSchema = JSONPointer.parse_uri_fragment(ptr[1:]).evaluate(rootschema)
    assert schema.base_uri == URI(base_uri)


@pytest.mark.parametrize('ptr, uri, canonical', [
    ('#', 'https://example.com/root.json', True),
    ('#', 'https://example.com/root.json#', True),
    ('#/$defs/A', 'https://example.com/root.json#foo', True),
    ('#/$defs/A', 'https://example.com/root.json#/$defs/A', True),
    ('#/$defs/B', 'https://example.com/other.json#', True),
    ('#/$defs/B', 'https://example.com/root.json#/$defs/B', False),
    ('#/$defs/B/$defs/X', 'https://example.com/other.json#bar', True),
    ('#/$defs/B/$defs/X', 'https://example.com/other.json#/$defs/X', True),
    ('#/$defs/B/$defs/X', 'https://example.com/root.json#/$defs/B/$defs/X', False),
    ('#/$defs/B/$defs/Y', 'https://example.com/t/inner.json#bar', True),
    ('#/$defs/B/$defs/Y', 'https://example.com/t/inner.json#', True),
    ('#/$defs/B/$defs/Y', 'https://example.com/other.json#/$defs/Y', False),
    ('#/$defs/B/$defs/Y', 'https://example.com/root.json#/$defs/B/$defs/Y', False),
    ('#/$defs/C', 'urn:uuid:ee564b8a-7a87-4125-8c96-e9f123d6766f#', True),
    ('#/$defs/C', 'https://example.com/root.json#/$defs/C', False),
])
def test_uri(ptr: str, uri: str, canonical: bool, catalog):
    rootschema = JSONSchema(id_example, metaschema_uri=metaschema_uri_2020_12)
    schema: JSONSchema = JSONPointer.parse_uri_fragment(ptr[1:]).evaluate(rootschema)
    assert schema == catalog.get_schema(uri := URI(uri))
    if canonical:
        # 'canonical' is as per the JSON Schema spec; however, we skip testing of
        # anchored URIs since we have only one way to calculate a schema's canonical URI
        if (fragment := uri.fragment) and not fragment.startswith('/'):
            return

        if fragment:
            # allow chars in the RFC3986 'sub-delims' set in the 'safe' arg,
            # since these are allowed by the 'fragment' definition; in particular,
            # this means we don't percent encode '$'
            uri = uri.copy(fragment=urllib.parse.quote(fragment, safe="/!$&'()*+,;="))
        else:
            # remove empty fragment
            uri = uri.copy(fragment=False)

        assert schema.canonical_uri == uri


# https://json-schema.org/draft/2019-09/json-schema-core.html#recursive-example
# tree schema, extensible
tree_2019_09 = {
    "$schema": "https://json-schema.org/draft/2019-09/schema",
    "$id": "https://example.com/tree",
    "$recursiveAnchor": true,
    "type": "object",
    "properties": {
        "data": true,
        "children": {
            "type": "array",
            "items": {
                "$recursiveRef": "#"
            }
        }
    }
}

# strict-tree schema, guards against misspelled properties
strict_tree_2019_09 = {
    "$schema": "https://json-schema.org/draft/2019-09/schema",
    "$id": "https://example.com/strict-tree",
    "$recursiveAnchor": true,
    "$ref": "tree",
    "unevaluatedProperties": false
}

# instance with misspelled field
tree_instance_2019_09 = {
    "children": [{"daat": 1}]
}


def test_recursive_schema_extension_2019_09():
    tree_schema = JSONSchema(tree_2019_09)
    strict_tree_schema = JSONSchema(strict_tree_2019_09)
    tree_json = JSON(tree_instance_2019_09)
    assert tree_schema.evaluate(tree_json).valid is True
    assert strict_tree_schema.evaluate(tree_json).valid is False


# https://json-schema.org/draft/2020-12/json-schema-core.html#recursive-example
# tree schema, extensible
tree_2020_12 = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://example.com/tree",
    "$dynamicAnchor": "node",
    "type": "object",
    "properties": {
        "data": true,
        "children": {
            "type": "array",
            "items": {
                "$dynamicRef": "#node"
            }
        }
    }
}

# strict-tree schema, guards against misspelled properties
strict_tree_2020_12 = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://example.com/strict-tree",
    "$dynamicAnchor": "node",
    "$ref": "tree",
    "unevaluatedProperties": false
}

# instance with misspelled field
tree_instance_2020_12 = {
    "children": [{"daat": 1}]
}


def test_recursive_schema_extension_2020_12():
    tree_schema = JSONSchema(tree_2020_12)
    strict_tree_schema = JSONSchema(strict_tree_2020_12)
    tree_json = JSON(tree_instance_2020_12)
    assert tree_schema.evaluate(tree_json).valid is True
    assert strict_tree_schema.evaluate(tree_json).valid is False
