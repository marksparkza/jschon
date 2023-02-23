import pathlib
import re
from copy import copy
from typing import Dict, List, Union

import pytest
from hypothesis import given, strategies as hs

from jschon import JSON, JSONCompatible, JSONPointer, JSONPointerError, RelativeJSONPointer, RelativeJSONPointerError
from jschon.utils import json_loadf
from tests.strategies import json, jsonpointer, jsonpointer_key, relative_jsonpointer, relative_jsonpointer_regex


def generate_jsonpointers(
        targets: Dict[str, JSONCompatible],
        target: JSONCompatible,
        ptr: str = '',
):
    targets[ptr] = target
    if isinstance(target, list):
        for i, item in enumerate(target):
            generate_jsonpointers(targets, item, f'{ptr}/{i}')
    elif isinstance(target, dict):
        for k, item in target.items():
            generate_jsonpointers(targets, item, f'{ptr}/{jsonpointer_escape(k)}')


def jsonpointer_escape(key: str):
    return key.replace('~', '~0').replace('/', '~1')


def jsonpointer_unescape(token: str):
    return token.replace('~1', '/').replace('~0', '~')


@given(hs.lists(jsonpointer | hs.lists(jsonpointer_key)))
def test_create_jsonpointer(values: List[Union[str, List[str]]]):
    keys = []
    for value in values:
        keys += [jsonpointer_unescape(token) for token in value.split('/')[1:]] if isinstance(value, str) else value

    ptr0 = JSONPointer(*values)
    assert ptr0 == (ptr1 := JSONPointer(*values))
    assert ptr0 == (ptr2 := JSONPointer(keys))
    assert ptr0 == (ptr3 := JSONPointer(ptr0))
    assert ptr0 != (ptr4 := JSONPointer() if keys else JSONPointer('/'))
    assert ptr0 != (ptr5 := JSONPointer('/', keys))
    assert JSONPointer(ptr0, keys, *values) == JSONPointer(*values, keys, ptr0)

    ptrs = {ptr0, ptr1, ptr2, ptr3}
    assert ptrs == {ptr0}
    ptrs |= {ptr4, ptr5}
    assert ptrs > {ptr0}

    assert str(ptr0) == ''.join(f'/{jsonpointer_escape(key)}' for key in keys)
    assert list(ptr0) == keys
    assert bool(ptr0) == bool(keys)
    assert eval(repr(ptr0)) == ptr0


@given(jsonpointer, jsonpointer_key)
def test_extend_jsonpointer_one_key(value, newkey):
    pointer = JSONPointer(value) / newkey
    newtoken = jsonpointer_escape(newkey)
    assert pointer[-1] == newkey
    assert str(pointer) == f'{value}/{newtoken}'


@given(jsonpointer, hs.lists(jsonpointer_key))
def test_extend_jsonpointer_multi_keys(value, newkeys):
    pointer = (base_ptr := JSONPointer(value)) / newkeys
    for i in range(len(newkeys)):
        assert pointer[len(base_ptr) + i] == newkeys[i]
    assert str(pointer) == value + ''.join(f'/{jsonpointer_escape(key)}' for key in newkeys)


@given(json, jsonpointer_key)
def test_evaluate_jsonpointer(value, testkey):
    assert JSONPointer().evaluate(value) == value
    assert JSONPointer().evaluate(JSON(value)) == value

    generate_jsonpointers(resolved_pointers := {}, value)
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


@given(jsonpointer, jsonpointer)
def test_compare_jsonpointer(value1, value2):
    ptr1 = JSONPointer(value1)
    ptr2 = JSONPointer(value2)
    assert ptr1 == JSONPointer(ptr1)
    assert ptr1 <= JSONPointer(ptr1)
    assert ptr1 >= JSONPointer(ptr1)
    assert not (ptr1 < JSONPointer(ptr1))
    assert not (ptr1 > JSONPointer(ptr1))
    assert ptr1 <= ptr1 / ptr2
    assert ptr1 / ptr2 >= ptr1
    assert bool(ptr2) == (ptr1 < ptr1 / ptr2)
    assert bool(ptr2) == (ptr1 / ptr2 > ptr1)
    assert bool(ptr2) == (not (ptr1 / ptr2 <= ptr1))
    assert bool(ptr2) == (not (ptr1 >= ptr1 / ptr2))
    assert (ptr1 <= ptr2) == ([k for k in ptr1] == [k for k in ptr2[:len(ptr1)]])
    assert (ptr1 >= ptr2) == ([k for k in ptr1[:len(ptr2)]] == [k for k in ptr2])
    assert (ptr1 < ptr2) == (ptr1 <= ptr2 and ptr1 != ptr2)
    assert (ptr1 > ptr2) == (ptr1 >= ptr2 and ptr1 != ptr2)


@given(relative_jsonpointer)
def test_create_relative_jsonpointer(value):
    match = re.fullmatch(relative_jsonpointer_regex, value)
    up, over, ref = match.group('up', 'over', 'ref')
    kwargs = dict(
        up=int(up),
        over=int(over) if over else 0,
        ref=JSONPointer(ref) if ref != '#' else ref,
    )

    r1 = RelativeJSONPointer(value)
    r2 = RelativeJSONPointer(**kwargs)
    assert r1 == r2
    assert str(r1) == value
    assert eval(repr(r1)) == r1

    oldkwargs = copy(kwargs)
    if up == '0':
        del kwargs['up']
    if over == '':
        del kwargs['over']
    if ref == '':
        del kwargs['ref']
    if kwargs != oldkwargs:
        assert r1 == RelativeJSONPointer(**kwargs)


# Examples from:
# https://datatracker.ietf.org/doc/html/draft-handrews-relative-json-pointer-01#section-5.1
# https://gist.github.com/geraintluff/5911303
# https://gist.github.com/handrews/62d9ae0abe8938c910f7f4906cfa53f9
example_file = pathlib.Path(__file__).parent / 'data' / 'relative_jsonpointer.json'


def pytest_generate_tests(metafunc):
    if metafunc.definition.name == 'test_evaluate_relative_jsonpointer':
        argnames = ('data', 'start', 'ref', 'result')
        argvalues = []
        examples = json_loadf(example_file)
        for example in examples:
            for test in example['tests']:
                argvalues += [pytest.param(
                    example['data'],
                    test['start'],
                    test['ref'],
                    test['result'],
                )]
        metafunc.parametrize(argnames, argvalues)


def test_evaluate_relative_jsonpointer(data, start, ref, result):
    data = JSON(data)
    start = JSONPointer(start)
    ref = RelativeJSONPointer(ref)
    node = start.evaluate(data)

    if result == '<data>':
        result = data
    elif result == '<fail>':
        with pytest.raises(RelativeJSONPointerError):
            ref.evaluate(node)
        return

    value = ref.evaluate(node)
    assert value == result
