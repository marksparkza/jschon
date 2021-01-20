import re
from unittest.mock import Mock

import hypothesis.strategies as hs
from hypothesis import given

from jschon.evaluation import EvaluationNode
from jschon.json import JSON
from jschon.keywords import *
from tests.strategies import *


def evaluate(kwclass, kwvalue, instval):
    return EvaluationNode(
        evaluator=kwclass(kwvalue),
        json=JSON(instval),
    )


@given(kwvalue=jsontype | jsontypes, instval=json)
def test_type(kwvalue, instval):
    result = evaluate(TypeKeyword, kwvalue, instval)
    if type(kwvalue) is str:
        kwvalue = [kwvalue]
    if instval is None:
        assert result.valid == ("null" in kwvalue)
    elif type(instval) is bool:
        assert result.valid == ("boolean" in kwvalue)
    elif type(instval) is float:
        assert result.valid == ("number" in kwvalue)
    elif type(instval) is int:
        assert result.valid == ("number" in kwvalue or "integer" in kwvalue)
    elif type(instval) is str:
        assert result.valid == ("string" in kwvalue)
    elif type(instval) is list:
        assert result.valid == ("array" in kwvalue)
    elif type(instval) is dict:
        assert result.valid == ("object" in kwvalue)


@given(kwvalue=jsonarray, instval=json)
def test_enum(kwvalue, instval):
    result = evaluate(EnumKeyword, kwvalue, instval)
    assert result.valid == any(
        instval == kwval for kwval in kwvalue
        if type(instval) == type(kwval) or {type(instval), type(kwval)} <= {int, float}
    )


@given(kwvalue=json, instval=json)
def test_const(kwvalue, instval):
    result = evaluate(ConstKeyword, kwvalue, instval)
    assert result.valid == (
            instval == kwvalue and
            (type(instval) == type(kwvalue) or {type(instval), type(kwvalue)} <= {int, float})
    )


@given(kwvalue=jsonnumber.filter(lambda x: x > 0), instval=jsonnumber)
def test_multiple_of(kwvalue, instval):
    result = evaluate(MultipleOfKeyword, kwvalue, instval)
    assert result.valid == (instval % kwvalue == 0)


@given(kwvalue=jsonnumber, instval=jsonnumber)
def test_maximum(kwvalue, instval):
    result = evaluate(MaximumKeyword, kwvalue, instval)
    assert result.valid == (instval <= kwvalue)


@given(kwvalue=jsonnumber, instval=jsonnumber)
def test_exclusive_maximum(kwvalue, instval):
    result = evaluate(ExclusiveMaximumKeyword, kwvalue, instval)
    assert result.valid == (instval < kwvalue)


@given(kwvalue=jsonnumber, instval=jsonnumber)
def test_minimum(kwvalue, instval):
    result = evaluate(MinimumKeyword, kwvalue, instval)
    assert result.valid == (instval >= kwvalue)


@given(kwvalue=jsonnumber, instval=jsonnumber)
def test_exclusive_minimum(kwvalue, instval):
    result = evaluate(ExclusiveMinimumKeyword, kwvalue, instval)
    assert result.valid == (instval > kwvalue)


@given(kwvalue=jsoninteger.filter(lambda x: x >= 0), instval=jsonstring)
def test_max_length(kwvalue, instval):
    result = evaluate(MaxLengthKeyword, kwvalue, instval)
    assert result.valid == (len(instval) <= kwvalue)


@given(kwvalue=jsoninteger.filter(lambda x: x >= 0), instval=jsonstring)
def test_min_length(kwvalue, instval):
    result = evaluate(MinLengthKeyword, kwvalue, instval)
    assert result.valid == (len(instval) >= kwvalue)


@given(kwvalue=hs.just(jsonpointer_regex), instval=hs.from_regex(jsonpointer_regex))
def test_pattern(kwvalue, instval):
    result = evaluate(PatternKeyword, kwvalue, instval)
    assert result.valid == (re.search(kwvalue, instval) is not None)


@given(kwvalue=jsoninteger.filter(lambda x: x >= 0), instval=jsonarray)
def test_max_items(kwvalue, instval):
    result = evaluate(MaxItemsKeyword, kwvalue, instval)
    assert result.valid == (len(instval) <= kwvalue)


@given(kwvalue=jsoninteger.filter(lambda x: x >= 0), instval=jsonarray)
def test_min_items(kwvalue, instval):
    result = evaluate(MinItemsKeyword, kwvalue, instval)
    assert result.valid == (len(instval) >= kwvalue)


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

    result = evaluate(UniqueItemsKeyword, kwvalue, instval)
    if kwvalue:
        uniquified = []
        for item in instval:
            if not any(isequal(item, value) for value in uniquified):
                uniquified += [item]
        assert result.valid == (len(instval) == len(uniquified))
    else:
        assert result.valid is True


@given(kwvalue=jsoninteger.filter(lambda x: x >= 0), instval=jsonarray, containstype=jsontype)
def test_max_contains(kwvalue, instval, containstype):
    count = len(list(filter(lambda item: JSON(item).istype(containstype), instval)))
    kw = MaxContainsKeyword(kwvalue)
    result = EvaluationNode(JSON(instval), kw)
    result.sibling = (mock_sibling_fn := Mock())
    result.sibling.return_value = (mock_contains_instance := Mock())
    mock_contains_instance.annotation = count
    kw(result)
    mock_sibling_fn.assert_called_once_with("contains")
    assert result.valid == (count <= kwvalue)


@given(kwvalue=jsoninteger.filter(lambda x: x >= 0), instval=jsonarray, containstype=jsontype)
def test_min_contains(kwvalue, instval, containstype):
    count = len(list(filter(lambda item: JSON(item).istype(containstype), instval)))
    kw = MinContainsKeyword(kwvalue)
    result = EvaluationNode(JSON(instval), kw)
    result.sibling = (mock_sibling_fn := Mock())
    result.sibling.return_value = (mock_contains_instance := Mock())
    mock_contains_instance.annotation = count
    kw(result)
    mock_sibling_fn.assert_called_once_with("contains")
    assert result.valid == (count >= kwvalue)


@given(kwvalue=jsoninteger.filter(lambda x: x >= 0), instval=jsonobject)
def test_max_properties(kwvalue, instval):
    result = evaluate(MaxPropertiesKeyword, kwvalue, instval)
    assert result.valid == (len(instval) <= kwvalue)


@given(kwvalue=jsoninteger.filter(lambda x: x >= 0), instval=jsonobject)
def test_min_properties(kwvalue, instval):
    result = evaluate(MinPropertiesKeyword, kwvalue, instval)
    assert result.valid == (len(instval) >= kwvalue)


@given(kwvalue=propnames, instval=jsonproperties)
def test_required(kwvalue, instval):
    result = evaluate(RequiredKeyword, kwvalue, instval)
    missing = any(name for name in kwvalue if name not in instval)
    assert result.valid == (not missing)


@given(kwvalue=hs.dictionaries(propname, propnames), instval=jsonproperties)
def test_dependent_required(kwvalue, instval):
    result = evaluate(DependentRequiredKeyword, kwvalue, instval)
    missing = False
    for name, deps in kwvalue.items():
        if name in instval:
            if any(dep for dep in deps if dep not in instval):
                missing = True
                break
    assert result.valid == (not missing)
