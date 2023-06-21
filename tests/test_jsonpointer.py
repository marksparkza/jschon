import pathlib
import re
from copy import copy
from typing import Dict, List, Union, Type

import pytest
from hypothesis import example, given, strategies as hs

from jschon import JSON, JSONCompatible, JSONPointer, RelativeJSONPointer
from jschon.exc import (
    JSONPointerMalformedError, JSONPointerReferenceError,
    RelativeJSONPointerMalformedError, RelativeJSONPointerReferenceError,
)
from jschon.utils import json_loadf
from tests.strategies import json, jsonpointer, jsonpointer_key, relative_jsonpointer, relative_jsonpointer_regex


##############################################################
# These subclasses exist to test the ability to override the #
# exception classes used in [Relative]JSONPointer subclasses #
##############################################################

class JPMalError(JSONPointerMalformedError):
    pass


class JPRefError(JSONPointerReferenceError):
    pass


class JPtr(JSONPointer):
    malformed_exc = JPMalError
    reference_exc = JPRefError


class RJPMalError(RelativeJSONPointerMalformedError):
    pass


class RJPRefError(RelativeJSONPointerReferenceError):
    pass


class RJPtr(RelativeJSONPointer):
    malformed_exc = RJPMalError
    reference_exc = RJPRefError
    json_pointer_class = JPtr


##################### End subclasses #########################


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


@pytest.mark.parametrize('jp_cls', (JSONPointer, JPtr))
@given(hs.lists(jsonpointer | hs.lists(jsonpointer_key)))
def test_create_jsonpointer(jp_cls: Type[JSONPointer], values: List[Union[str, List[str]]]):
    keys = []
    for value in values:
        keys += [jsonpointer_unescape(token) for token in value.split('/')[1:]] if isinstance(value, str) else value

    ptr0 = jp_cls(*values)
    assert ptr0 == (ptr1 := jp_cls(*values))
    assert ptr0 == (ptr2 := jp_cls(keys))
    assert ptr0 == (ptr3 := jp_cls(ptr0))
    assert ptr0 != (ptr4 := jp_cls() if keys else jp_cls('/'))
    assert ptr0 != (ptr5 := jp_cls('/', keys))
    assert jp_cls(ptr0, keys, *values) == jp_cls(*values, keys, ptr0)

    ptrs = {ptr0, ptr1, ptr2, ptr3}
    assert ptrs == {ptr0}
    ptrs |= {ptr4, ptr5}
    assert ptrs > {ptr0}

    assert str(ptr0) == ''.join(f'/{jsonpointer_escape(key)}' for key in keys)
    assert list(ptr0) == keys
    assert bool(ptr0) == bool(keys)
    assert eval(repr(ptr0)) == ptr0


@pytest.mark.parametrize('jp_cls', (JSONPointer, JPtr))
def test_malformed_jsonpointer(jp_cls):
    with pytest.raises(jp_cls.malformed_exc) as exc_info:
        jp_cls('0/foo')
    assert exc_info.type == jp_cls.malformed_exc


@pytest.mark.parametrize('jp_cls', (JSONPointer, JPtr))
@given(jsonpointer, jsonpointer_key)
def test_extend_jsonpointer_one_key(jp_cls, value, newkey):
    pointer = jp_cls(value) / newkey
    newtoken = jsonpointer_escape(newkey)
    assert type(pointer) == jp_cls
    assert pointer[-1] == newkey
    assert str(pointer) == f'{value}/{newtoken}'


@pytest.mark.parametrize('jp_cls', (JSONPointer, JPtr))
@given(jsonpointer, hs.lists(jsonpointer_key))
def test_extend_jsonpointer_multi_keys(jp_cls, value, newkeys):
    pointer = (base_ptr := jp_cls(value)) / newkeys
    assert type(pointer) == jp_cls
    for i in range(len(newkeys)):
        assert pointer[len(base_ptr) + i] == newkeys[i]
    assert str(pointer) == value + ''.join(f'/{jsonpointer_escape(key)}' for key in newkeys)


def test_uri_fragment_safe_characters():
    pointer_str = "/!$&'()*+,;="
    pointer = JSONPointer(pointer_str)
    assert pointer.uri_fragment() == pointer_str


@pytest.mark.parametrize('jp_cls', (JSONPointer, JPtr))
@given(json, jsonpointer_key)
@example('~', '')
def test_evaluate_jsonpointer(jp_cls, value, testkey):
    assert jp_cls().evaluate(value) == value
    assert jp_cls().evaluate(JSON(value)) == value

    generate_jsonpointers(resolved_pointers := {}, value)
    for pointer, target in resolved_pointers.items():
        assert jp_cls(pointer).evaluate(value) == target
        assert jp_cls(pointer).evaluate(JSON(value)) == target

    if isinstance(value, list):
        with pytest.raises(jp_cls.reference_exc) as exc_info:
            jp_cls(f'/{len(value)}').evaluate(value)
        assert exc_info.type == jp_cls.reference_exc
        with pytest.raises(jp_cls.reference_exc) as exc_info:
            jp_cls('/-').evaluate(value)
        assert exc_info.type == jp_cls.reference_exc
        with pytest.raises(jp_cls.reference_exc) as exc_info:
            jp_cls('/').evaluate(value)
        assert exc_info.type == jp_cls.reference_exc
    elif isinstance(value, dict):
        if testkey not in value:
            with pytest.raises(jp_cls.reference_exc) as exc_info:
                jp_cls(f'/{jsonpointer_escape(testkey)}').evaluate(value)
            assert exc_info.type == jp_cls.reference_exc
    else:
        with pytest.raises(jp_cls.reference_exc) as exc_info:
            jp_cls(f'/{jsonpointer_escape(str(value))}').evaluate(value)
        assert exc_info.type == jp_cls.reference_exc


@given(jsonpointer, jsonpointer)
def test_compare_jsonpointer(value1, value2):
    ptr1 = JPtr(value1)
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


@pytest.mark.parametrize('rjp_cls', (RelativeJSONPointer, RJPtr))
@given(relative_jsonpointer)
def test_create_relative_jsonpointer(rjp_cls, value):
    match = re.fullmatch(relative_jsonpointer_regex, value)
    up, over, ref = match.group('up', 'over', 'ref')
    kwargs = dict(
        up=int(up),
        over=int(over) if over else 0,
        ref=JSONPointer(ref) if ref != '#' else ref,
    )

    r1 = rjp_cls(value)
    r2 = rjp_cls(**kwargs)
    assert r1 == r2
    assert str(r1) == value
    assert eval(repr(r1)) == r1
    if type(kwargs['ref']) == JSONPointer:
        assert type(r1.path) == rjp_cls.json_pointer_class
        assert type(r2.path) == rjp_cls.json_pointer_class

    oldkwargs = copy(kwargs)
    if up == '0':
        del kwargs['up']
    if over == '':
        del kwargs['over']
    if ref == '':
        del kwargs['ref']
    if kwargs != oldkwargs:
        assert r1 == RelativeJSONPointer(**kwargs)


@pytest.mark.parametrize('rjp_cls', (RelativeJSONPointer, RJPtr))
def test_malformed_relative_jsonpointer(rjp_cls):
    with pytest.raises(rjp_cls.malformed_exc) as exc_info:
        rjp_cls('/bar')
    assert exc_info.type == rjp_cls.malformed_exc


# Examples from:
# https://datatracker.ietf.org/doc/html/draft-handrews-relative-json-pointer-01#section-5.1
# https://gist.github.com/geraintluff/5911303
# https://gist.github.com/handrews/62d9ae0abe8938c910f7f4906cfa53f9
example_file = pathlib.Path(__file__).parent / 'data' / 'relative_jsonpointer.json'


def pytest_generate_tests(metafunc):
    if metafunc.definition.name == 'test_evaluate_relative_jsonpointer':
        argnames = ('jp_cls', 'rjp_cls', 'data', 'start', 'ref', 'result')
        argvalues = []
        examples = json_loadf(example_file)
        for jp_cls, rjp_cls in (
            (JSONPointer, RelativeJSONPointer),
            (JPtr, RJPtr),
        ):
            for example in examples:
                for test in example['tests']:
                    argvalues += [pytest.param(
                        jp_cls,
                        rjp_cls,
                        example['data'],
                        test['start'],
                        test['ref'],
                        test['result'],
                    )]
        metafunc.parametrize(argnames, argvalues)


def test_evaluate_relative_jsonpointer(jp_cls, rjp_cls, data, start, ref, result):
    data = JSON(data)
    start = jp_cls(start)
    ref = rjp_cls(ref)
    node = start.evaluate(data)

    if result == '<data>':
        result = data
    elif result == '<fail>':
        with pytest.raises(rjp_cls.reference_exc) as exc_info:
            ref.evaluate(node)
        assert exc_info.type == rjp_cls.reference_exc
        return

    value = ref.evaluate(node)
    assert value == result
