import re
from unittest.mock import Mock

import hypothesis.strategies as hs
from hypothesis import given

from jschon.json import JSON
from jschon.jsoninstance import JSONInstance
from jschon.jsonschema import JSONSchema
from jschon.keywords import *
from tests.strategies import *


def evaluate_instance(kwclass, kwvalue, instval):
    return JSONInstance(
        evaluator=kwclass(JSONSchema(True), kwvalue),
        json=JSON(instval),
    )


@given(kwvalue=jsontype | jsontypes, instval=json)
def test_type(kwvalue, instval):
    instance = evaluate_instance(TypeKeyword, kwvalue, instval)
    if type(kwvalue) is str:
        kwvalue = [kwvalue]
    if instval is None:
        assert instance.valid == ("null" in kwvalue)
    elif type(instval) is bool:
        assert instance.valid == ("boolean" in kwvalue)
    elif type(instval) is float:
        assert instance.valid == ("number" in kwvalue)
    elif type(instval) is int:
        assert instance.valid == ("number" in kwvalue or "integer" in kwvalue)
    elif type(instval) is str:
        assert instance.valid == ("string" in kwvalue)
    elif type(instval) is list:
        assert instance.valid == ("array" in kwvalue)
    elif type(instval) is dict:
        assert instance.valid == ("object" in kwvalue)


@given(kwvalue=jsonarray, instval=json)
def test_enum(kwvalue, instval):
    instance = evaluate_instance(EnumKeyword, kwvalue, instval)
    assert instance.valid == any(
        instval == kwval for kwval in kwvalue
        if type(instval) == type(kwval) or {type(instval), type(kwval)} <= {int, float}
    )


@given(kwvalue=json, instval=json)
def test_const(kwvalue, instval):
    instance = evaluate_instance(ConstKeyword, kwvalue, instval)
    assert instance.valid == (
            instval == kwvalue and
            (type(instval) == type(kwvalue) or {type(instval), type(kwvalue)} <= {int, float})
    )


@given(kwvalue=jsonnumber.filter(lambda x: x > 0), instval=jsonnumber)
def test_multiple_of(kwvalue, instval):
    instance = evaluate_instance(MultipleOfKeyword, kwvalue, instval)
    assert instance.valid == (instval % kwvalue == 0)


@given(kwvalue=jsonnumber, instval=jsonnumber)
def test_maximum(kwvalue, instval):
    instance = evaluate_instance(MaximumKeyword, kwvalue, instval)
    assert instance.valid == (instval <= kwvalue)


@given(kwvalue=jsonnumber, instval=jsonnumber)
def test_exclusive_maximum(kwvalue, instval):
    instance = evaluate_instance(ExclusiveMaximumKeyword, kwvalue, instval)
    assert instance.valid == (instval < kwvalue)


@given(kwvalue=jsonnumber, instval=jsonnumber)
def test_minimum(kwvalue, instval):
    instance = evaluate_instance(MinimumKeyword, kwvalue, instval)
    assert instance.valid == (instval >= kwvalue)


@given(kwvalue=jsonnumber, instval=jsonnumber)
def test_exclusive_minimum(kwvalue, instval):
    instance = evaluate_instance(ExclusiveMinimumKeyword, kwvalue, instval)
    assert instance.valid == (instval > kwvalue)


@given(kwvalue=jsoninteger.filter(lambda x: x >= 0), instval=jsonstring)
def test_max_length(kwvalue, instval):
    instance = evaluate_instance(MaxLengthKeyword, kwvalue, instval)
    assert instance.valid == (len(instval) <= kwvalue)


@given(kwvalue=jsoninteger.filter(lambda x: x >= 0), instval=jsonstring)
def test_min_length(kwvalue, instval):
    instance = evaluate_instance(MinLengthKeyword, kwvalue, instval)
    assert instance.valid == (len(instval) >= kwvalue)


@given(kwvalue=hs.just(jsonpointer_regex), instval=hs.from_regex(jsonpointer_regex))
def test_pattern(kwvalue, instval):
    instance = evaluate_instance(PatternKeyword, kwvalue, instval)
    assert instance.valid == (re.search(kwvalue, instval) is not None)


@given(kwvalue=jsoninteger.filter(lambda x: x >= 0), instval=jsonarray)
def test_max_items(kwvalue, instval):
    instance = evaluate_instance(MaxItemsKeyword, kwvalue, instval)
    assert instance.valid == (len(instval) <= kwvalue)


@given(kwvalue=jsoninteger.filter(lambda x: x >= 0), instval=jsonarray)
def test_min_items(kwvalue, instval):
    instance = evaluate_instance(MinItemsKeyword, kwvalue, instval)
    assert instance.valid == (len(instval) >= kwvalue)


@given(kwvalue=jsonboolean, instval=jsonarray)
def test_unique_items(kwvalue, instval):
    def isequal(x, y):
        if type(x) is not type(y) and not {type(x), type(y)} <= {int, float}:
            return False
        if isinstance(x, list):
            return len(x) == len(y) and all(isequal(x[i], y[i]) for i in range(len(x)))
        if isinstance(x, dict):
            return x.keys() == y.keys() and all(isequal(x[k], y[k]) for k in x)
        return x == y

    instance = evaluate_instance(UniqueItemsKeyword, kwvalue, instval)
    if kwvalue:
        uniquified = []
        for item in instval:
            if not any(isequal(item, value) for value in uniquified):
                uniquified += [item]
        assert instance.valid == (len(instval) == len(uniquified))
    else:
        assert instance.valid is True


@given(kwvalue=jsoninteger.filter(lambda x: x >= 0), instval=jsonarray, containstype=jsontype)
def test_max_contains(kwvalue, instval, containstype):
    count = len(list(filter(lambda item: JSON(item).istype(containstype), instval)))
    kw = MaxContainsKeyword(JSONSchema(True), kwvalue)
    instance = JSONInstance(JSON(instval), kw)
    instance.sibling = (mock_sibling_fn := Mock())
    instance.sibling.return_value = (mock_contains_instance := Mock())
    mock_contains_instance.annotation = count
    kw(instance)
    mock_sibling_fn.assert_called_once_with("contains")
    assert instance.valid == (count <= kwvalue)


@given(kwvalue=jsoninteger.filter(lambda x: x >= 0), instval=jsonarray, containstype=jsontype)
def test_min_contains(kwvalue, instval, containstype):
    count = len(list(filter(lambda item: JSON(item).istype(containstype), instval)))
    kw = MinContainsKeyword(JSONSchema(True), kwvalue)
    instance = JSONInstance(JSON(instval), kw)
    instance.sibling = (mock_sibling_fn := Mock())
    instance.sibling.return_value = (mock_contains_instance := Mock())
    mock_contains_instance.annotation = count
    kw(instance)
    mock_sibling_fn.assert_called_once_with("contains")
    assert instance.valid == (count >= kwvalue)


@given(kwvalue=jsoninteger.filter(lambda x: x >= 0), instval=jsonobject)
def test_max_properties(kwvalue, instval):
    instance = evaluate_instance(MaxPropertiesKeyword, kwvalue, instval)
    assert instance.valid == (len(instval) <= kwvalue)


@given(kwvalue=jsoninteger.filter(lambda x: x >= 0), instval=jsonobject)
def test_min_properties(kwvalue, instval):
    instance = evaluate_instance(MinPropertiesKeyword, kwvalue, instval)
    assert instance.valid == (len(instval) >= kwvalue)


@given(kwvalue=propnames, instval=jsonproperties)
def test_required(kwvalue, instval):
    instance = evaluate_instance(RequiredKeyword, kwvalue, instval)
    missing = any(name for name in kwvalue if name not in instval)
    assert instance.valid == (not missing)


@given(kwvalue=hs.dictionaries(propname, propnames), instval=jsonproperties)
def test_dependent_required(kwvalue, instval):
    instance = evaluate_instance(DependentRequiredKeyword, kwvalue, instval)
    missing = False
    for name, deps in kwvalue.items():
        if name in instval:
            if any(dep for dep in deps if dep not in instval):
                missing = True
                break
    assert instance.valid == (not missing)
