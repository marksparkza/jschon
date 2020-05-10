from hypothesis import given

from jschon.json import *
from jschon.pointer import Pointer
from jschon.schema import Schema, Metaschema
from tests.strategies import *

metaschema_uri = "https://json-schema.org/draft/2019-09/schema"


@given(json)
def test_create_json(value):

    def assert_node(inst, val, loc):
        assert inst.value == val
        assert inst.location == Pointer(loc)
        if val is None:
            assert type(inst) is JSONNull
        elif isinstance(val, bool):
            assert type(inst) is JSONBoolean
        elif isinstance(val, int):
            assert type(inst) is JSONInteger
        elif isinstance(val, float):
            assert type(inst) is JSONNumber
        elif isinstance(val, str):
            assert type(inst) is JSONString
        elif isinstance(val, list):
            assert type(inst) is JSONArray
            for i, el in enumerate(val):
                assert_node(inst[i], el, f'{inst.location}/{i}')
        elif isinstance(val, dict):
            assert type(inst) is JSONObject
            for k, v in val.items():
                assert_node(inst[k], v, f'{inst.location}/{k}')
        else:
            assert False

    instance = JSON(value)
    assert_node(instance, value, '')


@given(jsonpointer)
def test_create_pointer(value):
    tokens = value.split('/')[1:]
    pointer = Pointer(value)
    assert pointer == Pointer(value)
    assert pointer.is_root() == (value == '')
    assert str(pointer) == value
    assert tokens == [token.value for token in pointer._tokens]


@given(jsonboolean | jsonobject)
def test_create_schema(value):
    schema = Schema(value, metaschema_uri=metaschema_uri)
    assert schema.value == value
    assert schema.location.is_root()
    if isinstance(value, dict):
        assert schema.metaschema.uri == metaschema_uri


@given(interdependent_keywords)
def test_keyword_dependency_resolution(value: list):

    def assert_keyword_order(dependency, dependent):
        try:
            assert keywords.index(dependency) < keywords.index(dependent)
        except ValueError:
            pass

    metaschema = Metaschema.load(metaschema_uri)
    kwclasses = {
        kw: metaschema.kwclasses[kw] for kw in value
    }
    keywords = [
        kwclass.__keyword__ for kwclass in Schema._resolve_keyword_dependencies(kwclasses)
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
