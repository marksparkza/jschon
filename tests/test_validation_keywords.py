import re

import hypothesis.strategies as hs
from hypothesis import given

from jschon.json import *
from jschon.jsonschema import JSONSchema
from jschon.keywords import *
from tests import metaschema_uri
from tests.strategies import *


@given(kwvalue=jsontype | jsontypes, instance=json)
def test_type(kwvalue, instance):
    kw = TypeKeyword(JSONSchema(True), kwvalue)
    result = kw.evaluate(JSON(instance))
    if type(kwvalue) is str:
        kwvalue = [kwvalue]
    if instance is None:
        assert result.valid == ("null" in kwvalue)
    elif type(instance) is bool:
        assert result.valid == ("boolean" in kwvalue)
    elif type(instance) is float:
        assert result.valid == ("number" in kwvalue)
    elif type(instance) is int:
        assert result.valid == ("number" in kwvalue or "integer" in kwvalue)
    elif type(instance) is str:
        assert result.valid == ("string" in kwvalue)
    elif type(instance) is list:
        assert result.valid == ("array" in kwvalue)
    elif type(instance) is dict:
        assert result.valid == ("object" in kwvalue)


@given(kwvalue=jsonarray, instance=json)
def test_enum(kwvalue, instance):
    kw = EnumKeyword(JSONSchema(True), kwvalue)
    result = kw.evaluate(JSON(instance))
    assert result.valid == any(
        instance == value for value in kwvalue
        if type(instance) == type(value) or {type(instance), type(value)} <= {int, float}
    )


@given(kwvalue=json, instance=json)
def test_const(kwvalue, instance):
    kw = ConstKeyword(JSONSchema(True), kwvalue)
    result = kw.evaluate(JSON(instance))
    assert result.valid == (
            instance == kwvalue and
            (type(instance) == type(kwvalue) or {type(instance), type(kwvalue)} <= {int, float})
    )


@given(kwvalue=jsonnumber.filter(lambda x: x > 0), instance=jsonnumber)
def test_multiple_of(kwvalue, instance):
    kw = MultipleOfKeyword(JSONSchema(True), kwvalue)
    result = kw.evaluate(JSONNumber(instance))
    assert result.valid == (instance % kwvalue == 0)


@given(kwvalue=jsonnumber, instance=jsonnumber)
def test_maximum(kwvalue, instance):
    kw = MaximumKeyword(JSONSchema(True), kwvalue)
    result = kw.evaluate(JSONNumber(instance))
    assert result.valid == (instance <= kwvalue)


@given(kwvalue=jsonnumber, instance=jsonnumber)
def test_exclusive_maximum(kwvalue, instance):
    kw = ExclusiveMaximumKeyword(JSONSchema(True), kwvalue)
    result = kw.evaluate(JSONNumber(instance))
    assert result.valid == (instance < kwvalue)


@given(kwvalue=jsonnumber, instance=jsonnumber)
def test_minimum(kwvalue, instance):
    kw = MinimumKeyword(JSONSchema(True), kwvalue)
    result = kw.evaluate(JSONNumber(instance))
    assert result.valid == (instance >= kwvalue)


@given(kwvalue=jsonnumber, instance=jsonnumber)
def test_exclusive_minimum(kwvalue, instance):
    kw = ExclusiveMinimumKeyword(JSONSchema(True), kwvalue)
    result = kw.evaluate(JSONNumber(instance))
    assert result.valid == (instance > kwvalue)


@given(kwvalue=jsoninteger.filter(lambda x: x >= 0), instance=jsonstring)
def test_max_length(kwvalue, instance):
    kw = MaxLengthKeyword(JSONSchema(True), kwvalue)
    result = kw.evaluate(JSONString(instance))
    assert result.valid == (len(instance) <= kwvalue)


@given(kwvalue=jsoninteger.filter(lambda x: x >= 0), instance=jsonstring)
def test_min_length(kwvalue, instance):
    kw = MinLengthKeyword(JSONSchema(True), kwvalue)
    result = kw.evaluate(JSONString(instance))
    assert result.valid == (len(instance) >= kwvalue)


@given(kwvalue=hs.just(jsonpointer_regex), instance=hs.from_regex(jsonpointer_regex))
def test_pattern(kwvalue, instance):
    kw = PatternKeyword(JSONSchema(True), kwvalue)
    result = kw.evaluate(JSONString(instance))
    assert result.valid == (re.search(kwvalue, instance) is not None)


@given(kwvalue=jsoninteger.filter(lambda x: x >= 0), instance=jsonarray)
def test_max_items(kwvalue, instance):
    kw = MaxItemsKeyword(JSONSchema(True), kwvalue)
    result = kw.evaluate(JSONArray(instance))
    assert result.valid == (len(instance) <= kwvalue)


@given(kwvalue=jsoninteger.filter(lambda x: x >= 0), instance=jsonarray)
def test_min_items(kwvalue, instance):
    kw = MinItemsKeyword(JSONSchema(True), kwvalue)
    result = kw.evaluate(JSONArray(instance))
    assert result.valid == (len(instance) >= kwvalue)


@given(kwvalue=jsonboolean, instance=jsonarray)
def test_unique_items(kwvalue, instance):
    def isequal(x, y):
        if type(x) is not type(y) and not {type(x), type(y)} <= {int, float}:
            return False
        if isinstance(x, list):
            return len(x) == len(y) and all(isequal(x[i], y[i]) for i in range(len(x)))
        if isinstance(x, dict):
            return x.keys() == y.keys() and all(isequal(x[k], y[k]) for k in x)
        return x == y

    kw = UniqueItemsKeyword(JSONSchema(True), kwvalue)
    result = kw.evaluate(JSONArray(instance))
    if kwvalue:
        uniquified = []
        for item in instance:
            if not any(isequal(item, value) for value in uniquified):
                uniquified += [item]
        assert result.valid == (len(instance) == len(uniquified))
    else:
        assert result.valid is True


@given(kwvalue=jsoninteger.filter(lambda x: x >= 0), instance=jsonarray, containstype=jsontype)
def test_max_contains(kwvalue, instance, containstype):
    count = len(list(filter(lambda item: JSON(item).istype(containstype), instance)))
    schema = JSONSchema({"contains": {"type": containstype}}, metaschema_uri=metaschema_uri)
    schema.evaluate(JSON(instance))
    kw = MaxContainsKeyword(schema, kwvalue)
    result = kw.evaluate(JSONArray(instance))
    assert result.valid == (count <= kwvalue)


@given(kwvalue=jsoninteger.filter(lambda x: x >= 0), instance=jsonarray, containstype=jsontype)
def test_min_contains(kwvalue, instance, containstype):
    count = len(list(filter(lambda item: JSON(item).istype(containstype), instance)))
    schema = JSONSchema({"contains": {"type": containstype}}, metaschema_uri=metaschema_uri)
    schema.evaluate(JSON(instance))
    kw = MinContainsKeyword(schema, kwvalue)
    result = kw.evaluate(JSONArray(instance))
    assert result.valid == (count >= kwvalue)


@given(kwvalue=jsoninteger.filter(lambda x: x >= 0), instance=jsonobject)
def test_max_properties(kwvalue, instance):
    kw = MaxPropertiesKeyword(JSONSchema(True), kwvalue)
    result = kw.evaluate(JSONObject(instance))
    assert result.valid == (len(instance) <= kwvalue)


@given(kwvalue=jsoninteger.filter(lambda x: x >= 0), instance=jsonobject)
def test_min_properties(kwvalue, instance):
    kw = MinPropertiesKeyword(JSONSchema(True), kwvalue)
    result = kw.evaluate(JSONObject(instance))
    assert result.valid == (len(instance) >= kwvalue)


@given(kwvalue=propnames, instance=jsonproperties)
def test_required(kwvalue, instance):
    kw = RequiredKeyword(JSONSchema(True), kwvalue)
    result = kw.evaluate(JSONObject(instance))
    missing = any(name for name in kwvalue if name not in instance)
    assert result.valid == (not missing)


@given(kwvalue=hs.dictionaries(propname, propnames), instance=jsonproperties)
def test_dependent_required(kwvalue, instance):
    kw = DependentRequiredKeyword(JSONSchema(True), kwvalue)
    result = kw.evaluate(JSONObject(instance))
    missing = False
    for name, deps in kwvalue.items():
        if name in instance:
            if any(dep for dep in deps if dep not in instance):
                missing = True
                break
    assert result.valid == (not missing)
