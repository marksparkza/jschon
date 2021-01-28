import re
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation
from unittest.mock import Mock

import hypothesis.strategies as hs
from hypothesis import given

from jschon.json import JSON
from jschon.jsonschema import Scope, JSONSchema
from jschon.keywords import *
from tests.strategies import *


def evaluate(kwclass, kwvalue, instval):
    kwclass(kwvalue).evaluate(JSON(instval), scope := Scope(JSONSchema(True)))
    return scope.valid


@given(kwvalue=jsontype | jsontypes, instval=json)
def test_type(kwvalue, instval):
    result = evaluate(TypeKeyword, kwvalue, instval)
    if isinstance(kwvalue, str):
        kwvalue = [kwvalue]
    if instval is None:
        assert result == ("null" in kwvalue)
    elif isinstance(instval, bool):
        assert result == ("boolean" in kwvalue)
    elif isinstance(instval, int) or isinstance(instval, (float, Decimal)) and instval == int(instval):
        assert result == ("number" in kwvalue or "integer" in kwvalue)
    elif isinstance(instval, float):
        assert result == ("number" in kwvalue)
    elif isinstance(instval, str):
        assert result == ("string" in kwvalue)
    elif isinstance(instval, list):
        assert result == ("array" in kwvalue)
    elif isinstance(instval, dict):
        assert result == ("object" in kwvalue)


@given(kwvalue=jsonarray, instval=json)
def test_enum(kwvalue, instval):
    result = evaluate(EnumKeyword, kwvalue, instval)
    assert result == any(
        instval == kwval for kwval in kwvalue
        if type(instval) == type(kwval) or {type(instval), type(kwval)} <= {int, float, Decimal}
    )


@given(kwvalue=json, instval=json)
def test_const(kwvalue, instval):
    result = evaluate(ConstKeyword, kwvalue, instval)
    assert result == (
            instval == kwvalue and
            (type(instval) == type(kwvalue) or {type(instval), type(kwvalue)} <= {int, float, Decimal})
    )


@given(kwvalue=jsonnumber.filter(lambda x: x > 0), instval=jsonnumber)
def test_multiple_of(kwvalue, instval):
    result = evaluate(MultipleOfKeyword, kwvalue, instval)
    try:
        try:
            assert result == (instval % kwvalue == 0)
        except TypeError:
            assert result == (Decimal(instval) % Decimal(kwvalue) == 0)
    except InvalidOperation:
        assert result is False


@given(kwvalue=jsonnumber, instval=jsonnumber)
def test_maximum(kwvalue, instval):
    result = evaluate(MaximumKeyword, kwvalue, instval)
    assert result == (instval <= kwvalue)


@given(kwvalue=jsonnumber, instval=jsonnumber)
def test_exclusive_maximum(kwvalue, instval):
    result = evaluate(ExclusiveMaximumKeyword, kwvalue, instval)
    assert result == (instval < kwvalue)


@given(kwvalue=jsonnumber, instval=jsonnumber)
def test_minimum(kwvalue, instval):
    result = evaluate(MinimumKeyword, kwvalue, instval)
    assert result == (instval >= kwvalue)


@given(kwvalue=jsonnumber, instval=jsonnumber)
def test_exclusive_minimum(kwvalue, instval):
    result = evaluate(ExclusiveMinimumKeyword, kwvalue, instval)
    assert result == (instval > kwvalue)


@given(kwvalue=jsoninteger.filter(lambda x: x >= 0), instval=jsonstring)
def test_max_length(kwvalue, instval):
    result = evaluate(MaxLengthKeyword, kwvalue, instval)
    assert result == (len(instval) <= kwvalue)


@given(kwvalue=jsoninteger.filter(lambda x: x >= 0), instval=jsonstring)
def test_min_length(kwvalue, instval):
    result = evaluate(MinLengthKeyword, kwvalue, instval)
    assert result == (len(instval) >= kwvalue)


@given(kwvalue=hs.just(jsonpointer_regex), instval=hs.from_regex(jsonpointer_regex))
def test_pattern(kwvalue, instval):
    result = evaluate(PatternKeyword, kwvalue, instval)
    assert result == (re.search(kwvalue, instval) is not None)


@given(kwvalue=hs.integers(min_value=0, max_value=20), instval=jsonflatarray)
def test_max_items(kwvalue, instval):
    result = evaluate(MaxItemsKeyword, kwvalue, instval)
    assert result == (len(instval) <= kwvalue)


@given(kwvalue=hs.integers(min_value=0, max_value=20), instval=jsonflatarray)
def test_min_items(kwvalue, instval):
    result = evaluate(MinItemsKeyword, kwvalue, instval)
    assert result == (len(instval) >= kwvalue)


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
        assert result == (len(instval) == len(uniquified))
    else:
        assert result is True


@contextmanager
def mock_contains_scope(test_kw, contains_count):
    def get_sibling(key):
        if key == "contains":
            return contains
        elif key == "maxContains":
            return max_contains

    scope = Scope(JSONSchema(True))
    scope.sibling = Mock(side_effect=get_sibling)
    contains = Mock()
    contains.annotations.get = Mock(return_value=(contains_annotation := Mock()))
    contains_annotation.value = contains_count
    contains.valid = contains_count > 0
    if test_kw == "minContains":
        max_contains = Mock()
        max_contains.valid = True

    yield scope

    if test_kw == "minContains":
        # minContains == 0 makes contains valid
        if scope.valid and not contains.valid:
            contains.errors.clear.assert_called_once()


@given(
    kwvalue=hs.integers(min_value=0, max_value=20),
    instval=jsonflatarray,
    containstype=jsontype,
)
def test_max_contains(kwvalue, instval, containstype):
    contains_count = len(list(filter(lambda item: JSON(item).istype(containstype), instval)))
    kw = MaxContainsKeyword(kwvalue)
    with mock_contains_scope("maxContains", contains_count) as scope:
        kw.evaluate(JSON(instval), scope)
        assert scope.valid == (contains_count <= kwvalue)


@given(
    kwvalue=hs.integers(min_value=0, max_value=20),
    instval=jsonflatarray,
    containstype=jsontype,
)
def test_min_contains(kwvalue, instval, containstype):
    contains_count = len(list(filter(lambda item: JSON(item).istype(containstype), instval)))
    kw = MinContainsKeyword(kwvalue)
    with mock_contains_scope("minContains", contains_count) as scope:
        kw.evaluate(JSON(instval), scope)
        assert scope.valid == (contains_count >= kwvalue)


@given(kwvalue=hs.integers(min_value=0, max_value=20), instval=jsonflatobject)
def test_max_properties(kwvalue, instval):
    result = evaluate(MaxPropertiesKeyword, kwvalue, instval)
    assert result == (len(instval) <= kwvalue)


@given(kwvalue=hs.integers(min_value=0, max_value=20), instval=jsonflatobject)
def test_min_properties(kwvalue, instval):
    result = evaluate(MinPropertiesKeyword, kwvalue, instval)
    assert result == (len(instval) >= kwvalue)


@given(kwvalue=propnames, instval=jsonproperties)
def test_required(kwvalue, instval):
    result = evaluate(RequiredKeyword, kwvalue, instval)
    missing = any(name for name in kwvalue if name not in instval)
    assert result == (not missing)


@given(kwvalue=hs.dictionaries(propname, propnames), instval=jsonproperties)
def test_dependent_required(kwvalue, instval):
    result = evaluate(DependentRequiredKeyword, kwvalue, instval)
    missing = False
    for name, deps in kwvalue.items():
        if name in instval:
            if any(dep for dep in deps if dep not in instval):
                missing = True
                break
    assert result == (not missing)
