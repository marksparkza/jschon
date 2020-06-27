from typing import Union, List

from hypothesis import given, strategies as hs

from jschon.jsonpointer import JSONPointer
from tests.strategies import jsonpointer, jsonpointer_key, jsonarray, jsonobject


@given(hs.lists(jsonpointer | hs.lists(hs.text())))
def test_create_jsonpointer(values: List[Union[str, List[str]]]):
    keys = []
    for value in values:
        keys += [jsonpointer_unescape(token) for token in value.split('/')[1:]] if isinstance(value, str) else value
    pointer = JSONPointer(*values)
    assert pointer == JSONPointer(*values)
    assert pointer == JSONPointer(keys)
    assert pointer == JSONPointer(pointer)
    assert str(pointer) == ''.join(f'/{jsonpointer_escape(key)}' for key in keys)
    assert list(pointer) == keys
    assert bool(pointer) == bool(keys)
    assert pointer != JSONPointer() if keys else JSONPointer('/')
    assert pointer != JSONPointer('/', keys)


@given(jsonpointer, jsonpointer_key)
def test_extend_jsonpointer(value, newkey):
    pointer = JSONPointer(value) / newkey
    newtoken = jsonpointer_escape(newkey)
    assert pointer[-1] == newkey
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
        assert JSONPointer(pointer).evaluate(value) == target


def jsonpointer_escape(key: str):
    return key.replace('~', '~0').replace('/', '~1')


def jsonpointer_unescape(token: str):
    return token.replace('~1', '/').replace('~0', '~')
