from typing import Union, List

import pytest
from hypothesis import given, strategies as hs

from jschon.exceptions import JSONPointerError
from jschon.json import JSON
from jschon.jsonpointer import JSONPointer
from tests.strategies import jsonpointer, jsonpointer_key, json


@given(hs.lists(jsonpointer | hs.lists(jsonpointer_key)))
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


@given(json, jsonpointer_key)
def test_evaluate_jsonpointer(value, testkey):
    resolved_pointers = {}

    def generate_pointers(ptr, val):
        resolved_pointers[ptr] = val
        if isinstance(val, list):
            for i, item in enumerate(val):
                generate_pointers(f'{ptr}/{i}', item)
        elif isinstance(val, dict):
            for k, item in val.items():
                generate_pointers(f"{ptr}/{jsonpointer_escape(k)}", item)

    assert JSONPointer().evaluate(value) == value
    assert JSONPointer().evaluate(JSON(value)) == value

    generate_pointers('', value)
    for pointer, target in resolved_pointers.items():
        assert JSONPointer(pointer).evaluate(value) == target
        assert JSONPointer(pointer).evaluate(JSON(value)) == target

    if isinstance(value, list):
        with pytest.raises(JSONPointerError):
            JSONPointer(f'/{len(value)}').evaluate(value)
        with pytest.raises(JSONPointerError):
            JSONPointer('/-').evaluate(value)
        with pytest.raises(JSONPointerError):
            JSONPointer('/').evaluate(value)
    elif isinstance(value, dict):
        if testkey not in value:
            with pytest.raises(JSONPointerError):
                JSONPointer(f'/{jsonpointer_escape(testkey)}').evaluate(value)
    else:
        with pytest.raises(JSONPointerError):
            JSONPointer(f'/{value}').evaluate(value)


def jsonpointer_escape(key: str):
    return key.replace('~', '~0').replace('/', '~1')


def jsonpointer_unescape(token: str):
    return token.replace('~1', '/').replace('~0', '~')
