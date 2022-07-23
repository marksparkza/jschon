import math
import re
from decimal import Decimal, InvalidOperation

from hypothesis import given

from jschon import JSON, JSONSchema
from jschon.jsonschema import Result
from jschon.vocabulary.validation import *
from tests import metaschema_uri_2019_09
from tests.strategies import *


def evaluate(kwclass, kwvalue, instval):
    schema = JSONSchema(True)
    kwclass(schema, kwvalue).evaluate(inst := JSON(instval), result := Result(schema, inst))
    return result.valid


def isequal(x, y):
    if {type(x), type(y)} <= {int, float}:
        return math.isclose(x, y)
    if type(x) is not type(y):
        return False
    if isinstance(x, list):
        return len(x) == len(y) and all(isequal(x[i], y[i]) for i in range(len(x)))
    if isinstance(x, dict):
        return x.keys() == y.keys() and all(isequal(x[k], y[k]) for k in x)
    return x == y


@given(kwvalue=jsontype | jsontypes, instval=json)
def test_type(kwvalue, instval):
    result = evaluate(TypeKeyword, kwvalue, instval)
    if isinstance(kwvalue, str):
        kwvalue = [kwvalue]
    if instval is None:
        assert result == ("null" in kwvalue)
    elif isinstance(instval, bool):
        assert result == ("boolean" in kwvalue)
    elif isinstance(instval, int) or isinstance(instval, float) and instval == int(instval):
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
    assert result == any(isequal(instval, kwval) for kwval in kwvalue)


@given(kwvalue=json, instval=json)
def test_const(kwvalue, instval):
    result = evaluate(ConstKeyword, kwvalue, instval)
    assert result == isequal(instval, kwvalue)


@given(kwvalue=jsonnumber.filter(lambda x: x > 0), instval=jsonnumber)
def test_multiple_of(kwvalue, instval):
    result = evaluate(MultipleOfKeyword, kwvalue, instval)
    try:
        assert result == (Decimal(f'{instval}') % Decimal(f'{kwvalue}') == 0)
    except InvalidOperation:
        pass


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
    result = evaluate(UniqueItemsKeyword, kwvalue, instval)
    if kwvalue:
        uniquified = []
        for item in instval:
            if not any(isequal(item, value) for value in uniquified):
                uniquified += [item]
        assert result == (len(instval) == len(uniquified))
    else:
        assert result is True


@given(
    minmax=hs.tuples(hs.integers(min_value=0, max_value=20), hs.integers(min_value=0, max_value=20)),
    instval=jsonflatarray,
)
def test_contains(minmax, instval):
    min_contains = min(minmax)
    max_contains = max(minmax)
    contains_count = len(list(filter(lambda item: JSON(item).type == "boolean", instval)))
    schema = JSONSchema({
        "contains": {"type": "boolean"},
        "minContains": min_contains,
        "maxContains": max_contains,
    }, metaschema_uri=metaschema_uri_2019_09)
    result = schema.evaluate(JSON(instval))
    assert result.valid == (min_contains <= contains_count <= max_contains)


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
