import pytest
from hypothesis import given

from jschon.jsonpointer import JSONPointer
from jschon.jsonschema import JSONSchema, JSONObjectSchema
from jschon.uri import URI
from tests import metaschema_uri
from tests.strategies import *


@given(jsonboolean | jsonobject)
def test_create_schema(value):
    schema = JSONSchema(value, metaschema_uri=metaschema_uri)
    assert schema.value == value
    assert not schema.location
    assert schema.superkeyword is None
    assert schema.metaschema_uri == metaschema_uri


@given(interdependent_keywords)
def test_keyword_dependency_resolution(value: list):

    def assert_keyword_order(dependency, dependent):
        try:
            assert keywords.index(dependency) < keywords.index(dependent)
        except ValueError:
            pass

    metaschema = JSONSchema.get(metaschema_uri)
    kwclasses = {
        kw: metaschema.kwclasses[kw] for kw in value
    }
    keywords = [
        kwclass.__keyword__ for kwclass in JSONObjectSchema._resolve_keyword_dependencies(kwclasses)
    ]

    assert_keyword_order("properties", "additionalProperties")
    assert_keyword_order("properties", "unevaluatedProperties")
    assert_keyword_order("patternProperties", "additionalProperties")
    assert_keyword_order("patternProperties", "unevaluatedProperties")
    assert_keyword_order("additionalProperties", "unevaluatedProperties")
    assert_keyword_order("items", "additionalItems")
    assert_keyword_order("items", "unevaluatedItems")
    assert_keyword_order("additionalItems", "unevaluatedItems")
    assert_keyword_order("contains", "maxContains")
    assert_keyword_order("contains", "minContains")
    assert_keyword_order("maxContains", "minContains")
    assert_keyword_order("if", "then")
    assert_keyword_order("if", "else")
    assert_keyword_order("if", "unevaluatedItems")
    assert_keyword_order("then", "unevaluatedItems")
    assert_keyword_order("else", "unevaluatedItems")
    assert_keyword_order("allOf", "unevaluatedItems")
    assert_keyword_order("anyOf", "unevaluatedItems")
    assert_keyword_order("oneOf", "unevaluatedItems")
    assert_keyword_order("not", "unevaluatedItems")
    assert_keyword_order("if", "unevaluatedProperties")
    assert_keyword_order("then", "unevaluatedProperties")
    assert_keyword_order("else", "unevaluatedProperties")
    assert_keyword_order("dependentSchemas", "unevaluatedProperties")
    assert_keyword_order("allOf", "unevaluatedProperties")
    assert_keyword_order("anyOf", "unevaluatedProperties")
    assert_keyword_order("oneOf", "unevaluatedProperties")
    assert_keyword_order("not", "unevaluatedProperties")


# https://json-schema.org/draft/2019-09/json-schema-core.html#idExamples
example = {
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
    rootschema = JSONSchema(example, metaschema_uri=metaschema_uri)
    schema: JSONSchema = JSONPointer.parse_uri_fragment(ptr).evaluate(rootschema)
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
def test_uri(ptr: str, uri: str, canonical: bool):
    rootschema = JSONSchema(example, metaschema_uri=metaschema_uri)
    schema: JSONSchema = JSONPointer.parse_uri_fragment(ptr).evaluate(rootschema)
    assert schema == JSONSchema.get(URI(uri))
