from hypothesis import given

from jschon.json import *
from jschon.pointer import Pointer
from jschon.schema import Schema
from tests.strategies import *


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
    metaschema_uri = "https://json-schema.org/draft/2019-09/schema"
    schema = Schema(value, metaschema_uri=metaschema_uri)
    assert schema.value == value
    assert schema.location.is_root()
    if isinstance(value, dict):
        assert schema.metaschema.uri == metaschema_uri
