from hypothesis import given, strategies as hs

from jschon.json import *
from tests.strategies import jsonpointer, jsonarray, jsonobject, json


@given(json)
def test_create_json(value):

    def assert_node(inst, val, loc):
        assert inst.value == val
        assert inst.location == JSONPointer(loc)
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
                assert_node(inst[k], v, f'{inst.location}/{pointer_escape(k)}')
        else:
            assert False

    instance = JSON(value)
    assert_node(instance, value, '')


@given(jsonpointer)
def test_create_pointer(value):
    tokens = value.split('/')[1:]
    pointer = JSONPointer(value)
    assert pointer == JSONPointer(value)
    assert pointer.is_root() == (value == '')
    assert str(pointer) == value
    assert tokens == [token for token in pointer._tokens]


@given(jsonpointer, hs.text() | hs.sampled_from(['~']))
def test_extend_pointer(value, newkey):
    pointer = JSONPointer(value) / newkey
    newtoken = pointer_escape(newkey)
    assert str(pointer) == f'{value}/{newtoken}'


@given(jsonarray | jsonobject)
def test_evaluate_pointer(value):

    resolved_pointers = {}

    def generate_pointers(ptr, val):
        resolved_pointers[ptr] = val
        if isinstance(val, list):
            for i, item in enumerate(val):
                generate_pointers(f'{ptr}/{i}', item)
        elif isinstance(val, dict):
            for k, item in val.items():
                generate_pointers(f"{ptr}/{pointer_escape(k)}", item)

    generate_pointers('', value)
    for pointer, target in resolved_pointers.items():
        assert target == JSONPointer(pointer).evaluate(JSON(value))


def pointer_escape(key: str):
    return key.replace('~', '~0').replace('/', '~1')
