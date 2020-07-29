from hypothesis import given

from jschon.jsonschema import JSONSchema, JSONObjectSchema
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
