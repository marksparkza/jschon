import re
from decimal import Decimal, InvalidOperation

from hypothesis import given

from jschon import JSON
from jschon.jsonschema import Scope
from jschon.vocabulary.validation import *
from tests import metaschema_uri_2019_09
from tests.strategies import *


def evaluate(kwclass, kwvalue, instval, catalogue):
    schema = catalogue.create_schema(True)
    kwclass(schema, kwvalue).evaluate(JSON(instval), scope := Scope(schema))
    return scope.valid


def isequal(x, y):
    if type(x) is not type(y) and not {type(x), type(y)} <= {int, float, Decimal}:
        return False
    if isinstance(x, list):
        return len(x) == len(y) and all(isequal(x[i], y[i]) for i in range(len(x)))
    if isinstance(x, dict):
        return x.keys() == y.keys() and all(isequal(x[k], y[k]) for k in x)
    return x == y


@given(kwvalue=jsontype | jsontypes, instval=json)
def test_type(kwvalue, instval, catalogue):
    result = evaluate(TypeKeyword, kwvalue, instval, catalogue)
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
def test_enum(kwvalue, instval, catalogue):
    result = evaluate(EnumKeyword, kwvalue, instval, catalogue)
    assert result == any(isequal(instval, kwval) for kwval in kwvalue)


@given(kwvalue=json, instval=json)
def test_const(kwvalue, instval, catalogue):
    result = evaluate(ConstKeyword, kwvalue, instval, catalogue)
    assert result == isequal(instval, kwvalue)


@given(kwvalue=jsonnumber.filter(lambda x: x > 0), instval=jsonnumber)
def test_multiple_of(kwvalue, instval, catalogue):
    def decimalize(val):
        if isinstance(val, float):
            return Decimal(f'{val}')
        return val

    result = evaluate(MultipleOfKeyword, kwvalue, instval, catalogue)
    try:
        assert result == (decimalize(instval) % decimalize(kwvalue) == 0)
    except InvalidOperation:
        pass


@given(kwvalue=jsonnumber, instval=jsonnumber)
def test_maximum(kwvalue, instval, catalogue):
    result = evaluate(MaximumKeyword, kwvalue, instval, catalogue)
    assert result == (instval <= kwvalue)


@given(kwvalue=jsonnumber, instval=jsonnumber)
def test_exclusive_maximum(kwvalue, instval, catalogue):
    result = evaluate(ExclusiveMaximumKeyword, kwvalue, instval, catalogue)
    assert result == (instval < kwvalue)


@given(kwvalue=jsonnumber, instval=jsonnumber)
def test_minimum(kwvalue, instval, catalogue):
    result = evaluate(MinimumKeyword, kwvalue, instval, catalogue)
    assert result == (instval >= kwvalue)


@given(kwvalue=jsonnumber, instval=jsonnumber)
def test_exclusive_minimum(kwvalue, instval, catalogue):
    result = evaluate(ExclusiveMinimumKeyword, kwvalue, instval, catalogue)
    assert result == (instval > kwvalue)


@given(kwvalue=jsoninteger.filter(lambda x: x >= 0), instval=jsonstring)
def test_max_length(kwvalue, instval, catalogue):
    result = evaluate(MaxLengthKeyword, kwvalue, instval, catalogue)
    assert result == (len(instval) <= kwvalue)


@given(kwvalue=jsoninteger.filter(lambda x: x >= 0), instval=jsonstring)
def test_min_length(kwvalue, instval, catalogue):
    result = evaluate(MinLengthKeyword, kwvalue, instval, catalogue)
    assert result == (len(instval) >= kwvalue)


@given(kwvalue=hs.just(jsonpointer_regex), instval=hs.from_regex(jsonpointer_regex))
def test_pattern(kwvalue, instval, catalogue):
    result = evaluate(PatternKeyword, kwvalue, instval, catalogue)
    assert result == (re.search(kwvalue, instval) is not None)


@given(kwvalue=hs.integers(min_value=0, max_value=20), instval=jsonflatarray)
def test_max_items(kwvalue, instval, catalogue):
    result = evaluate(MaxItemsKeyword, kwvalue, instval, catalogue)
    assert result == (len(instval) <= kwvalue)


@given(kwvalue=hs.integers(min_value=0, max_value=20), instval=jsonflatarray)
def test_min_items(kwvalue, instval, catalogue):
    result = evaluate(MinItemsKeyword, kwvalue, instval, catalogue)
    assert result == (len(instval) >= kwvalue)


@given(kwvalue=jsonboolean, instval=jsonarray)
def test_unique_items(kwvalue, instval, catalogue):
    result = evaluate(UniqueItemsKeyword, kwvalue, instval, catalogue)
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
def test_contains(minmax, instval, catalogue):
    min_contains = min(minmax)
    max_contains = max(minmax)
    contains_count = len(list(filter(lambda item: JSON(item).type == "boolean", instval)))
    schema = catalogue.create_schema({
        "contains": {"type": "boolean"},
        "minContains": min_contains,
        "maxContains": max_contains,
    }, metaschema_uri=metaschema_uri_2019_09)
    scope = schema.evaluate(JSON(instval))
    assert scope.valid == (min_contains <= contains_count <= max_contains)


@given(kwvalue=hs.integers(min_value=0, max_value=20), instval=jsonflatobject)
def test_max_properties(kwvalue, instval, catalogue):
    result = evaluate(MaxPropertiesKeyword, kwvalue, instval, catalogue)
    assert result == (len(instval) <= kwvalue)


@given(kwvalue=hs.integers(min_value=0, max_value=20), instval=jsonflatobject)
def test_min_properties(kwvalue, instval, catalogue):
    result = evaluate(MinPropertiesKeyword, kwvalue, instval, catalogue)
    assert result == (len(instval) >= kwvalue)


@given(kwvalue=propnames, instval=jsonproperties)
def test_required(kwvalue, instval, catalogue):
    result = evaluate(RequiredKeyword, kwvalue, instval, catalogue)
    missing = any(name for name in kwvalue if name not in instval)
    assert result == (not missing)


@given(kwvalue=hs.dictionaries(propname, propnames), instval=jsonproperties)
def test_dependent_required(kwvalue, instval, catalogue):
    result = evaluate(DependentRequiredKeyword, kwvalue, instval, catalogue)
    missing = False
    for name, deps in kwvalue.items():
        if name in instval:
            if any(dep for dep in deps if dep not in instval):
                missing = True
                break
    assert result == (not missing)
