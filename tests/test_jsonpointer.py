from hypothesis import given, strategies as hs

from jschon.jsonpointer import JSONPointer
from tests.strategies import jsonpointer, jsonarray, jsonobject


@given(jsonpointer)
def test_create_jsonpointer(value):
    tokens = value.split('/')[1:]
    pointer = JSONPointer(value)
    assert pointer == JSONPointer(value)
    assert pointer.is_root == (value == '')
    assert str(pointer) == value
    assert tokens == [token for token in pointer._tokens]


@given(jsonpointer, hs.text() | hs.sampled_from(['~']))
def test_extend_jsonpointer(value, newkey):
    pointer = JSONPointer(value) / newkey
    newtoken = jsonpointer_escape(newkey)
    assert str(pointer) == f'{value}/{newtoken}'


@given(jsonarray | jsonobject)
def test_evaluate_jsonpointer(value):

    resolved_pointers = {}

    def generate_pointers(ptr, val):
        resolved_pointers[ptr] = val
        if isinstance(val, list):
            for i, item in enumerate(val):
                generate_pointers(f'{ptr}/{i}', item)
        elif isinstance(val, dict):
            for k, item in val.items():
                generate_pointers(f"{ptr}/{jsonpointer_escape(k)}", item)

    generate_pointers('', value)
    for pointer, target in resolved_pointers.items():
        assert target == JSONPointer(pointer).evaluate(value)


def jsonpointer_escape(key: str):
    return key.replace('~', '~0').replace('/', '~1')
