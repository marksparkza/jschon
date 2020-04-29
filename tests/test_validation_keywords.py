import re

import hypothesis.strategies as hs
from hypothesis import given

from jschon.json import JSON
from jschon.keywords.validation import *
from jschon.schema import Schema
from tests.strategies import *


@given(kwvalue=jsontype | jsontypes, instance=json)
def test_type(kwvalue, instance):
    kw = TypeKeyword(Schema(True), kwvalue)
    result = kw.evaluate(instance := JSON(instance))
    if type(kwvalue) is str:
        assert result.valid == (instance.jsontype == kwvalue)
    else:
        assert result.valid == (instance.jsontype in kwvalue)


@given(kwvalue=jsonarray, instance=json)
def test_enum(kwvalue, instance):
    kw = EnumKeyword(Schema(True), kwvalue)
    result = kw.evaluate(JSON(instance))
    assert result.valid == (instance in kwvalue)


@given(kwvalue=json, instance=json)
def test_const(kwvalue, instance):
    kw = ConstKeyword(Schema(True), kwvalue)
    result = kw.evaluate(JSON(instance))
    assert result.valid == (instance == kwvalue)


@given(kwvalue=jsonnumber.filter(lambda x: x > 0), instance=jsonnumber)
def test_multiple_of(kwvalue, instance):
    kw = MultipleOfKeyword(Schema(True), kwvalue)
    result = kw.evaluate(JSON(instance))
    assert result.valid == (instance % kwvalue == 0)


@given(kwvalue=jsonnumber, instance=jsonnumber)
def test_maximum(kwvalue, instance):
    kw = MaximumKeyword(Schema(True), kwvalue)
    result = kw.evaluate(JSON(instance))
    assert result.valid == (instance <= kwvalue)


@given(kwvalue=jsonnumber, instance=jsonnumber)
def test_exclusive_maximum(kwvalue, instance):
    kw = ExclusiveMaximumKeyword(Schema(True), kwvalue)
    result = kw.evaluate(JSON(instance))
    assert result.valid == (instance < kwvalue)


@given(kwvalue=jsonnumber, instance=jsonnumber)
def test_minimum(kwvalue, instance):
    kw = MinimumKeyword(Schema(True), kwvalue)
    result = kw.evaluate(JSON(instance))
    assert result.valid == (instance >= kwvalue)


@given(kwvalue=jsonnumber, instance=jsonnumber)
def test_exclusive_minimum(kwvalue, instance):
    kw = ExclusiveMinimumKeyword(Schema(True), kwvalue)
    result = kw.evaluate(JSON(instance))
    assert result.valid == (instance > kwvalue)


@given(kwvalue=jsoninteger.filter(lambda x: x >= 0), instance=jsonstring)
def test_max_length(kwvalue, instance):
    kw = MaxLengthKeyword(Schema(True), kwvalue)
    result = kw.evaluate(JSON(instance))
    assert result.valid == (len(instance) <= kwvalue)


@given(kwvalue=jsoninteger.filter(lambda x: x >= 0), instance=jsonstring)
def test_min_length(kwvalue, instance):
    kw = MinLengthKeyword(Schema(True), kwvalue)
    result = kw.evaluate(JSON(instance))
    assert result.valid == (len(instance) >= kwvalue)


@given(kwvalue=hs.just(jsonpointer_regex), instance=hs.from_regex(jsonpointer_regex))
def test_pattern(kwvalue, instance):
    kw = PatternKeyword(Schema(True), kwvalue)
    result = kw.evaluate(JSON(instance))
    assert result.valid == (re.search(kwvalue, instance) is not None)


@given(kwvalue=jsoninteger.filter(lambda x: x >= 0), instance=jsonarray)
def test_max_items(kwvalue, instance):
    kw = MaxItemsKeyword(Schema(True), kwvalue)
    result = kw.evaluate(JSON(instance))
    assert result.valid == (len(instance) <= kwvalue)


@given(kwvalue=jsoninteger.filter(lambda x: x >= 0), instance=jsonarray)
def test_min_items(kwvalue, instance):
    kw = MinItemsKeyword(Schema(True), kwvalue)
    result = kw.evaluate(JSON(instance))
    assert result.valid == (len(instance) >= kwvalue)


@given(kwvalue=jsonboolean, instance=jsonarray)
def test_unique_items(kwvalue, instance):
    kw = UniqueItemsKeyword(Schema(True), kwvalue)
    result = kw.evaluate(JSON(instance))
    uniquified = []
    for item in instance:
        if item not in uniquified:
            uniquified += [item]
    assert result.valid == (not kwvalue or len(instance) == len(uniquified))
