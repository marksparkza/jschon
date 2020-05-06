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
    metaschema = Metaschema.load(metaschema_uri)
    kwclasses = {
        kw: metaschema.kwclasses[kw] for kw in value
    }
    keywords = [
        kwclass.__keyword__ for kwclass in Schema._resolve_keyword_dependencies(kwclasses)
    ]
    try:
        assert keywords.index("properties") < keywords.index("additionalProperties")
    except ValueError:
        pass
    try:
        assert keywords.index("properties") < keywords.index("unevaluatedProperties")
    except ValueError:
        pass
    try:
        assert keywords.index("patternProperties") < keywords.index("additionalProperties")
    except ValueError:
        pass
    try:
        assert keywords.index("patternProperties") < keywords.index("unevaluatedProperties")
    except ValueError:
        pass
    try:
        assert keywords.index("additionalProperties") < keywords.index("unevaluatedProperties")
    except ValueError:
        pass
    try:
        assert keywords.index("items") < keywords.index("additionalItems")
    except ValueError:
        pass
    try:
        assert keywords.index("items") < keywords.index("unevaluatedItems")
    except ValueError:
        pass
    try:
        assert keywords.index("additionalItems") < keywords.index("unevaluatedItems")
    except ValueError:
        pass
    try:
        assert keywords.index("contains") < keywords.index("maxContains")
    except ValueError:
        pass
    try:
        assert keywords.index("contains") < keywords.index("minContains")
    except ValueError:
        pass
    try:
        assert keywords.index("maxContains") < keywords.index("minContains")
    except ValueError:
        pass
