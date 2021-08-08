import ipaddress

import pytest
from hypothesis import given, strategies as hs

from jschon import JSON, JSONPointer, JSONPointerError, JSONSchema
from jschon.jsonschema import Scope
from jschon.vocabulary.format import FormatKeyword
from tests.strategies import jsonpointer


@pytest.fixture(scope='module', autouse=True)
def setup_validators(catalog):
    catalog.add_format_validators({
        "ipv4": ipv4_validator,
        "ipv6": ipv6_validator,
        "json-pointer": jsonpointer_validator,
    })
    yield
    catalog._format_validators.clear()


def ipv4_validator(value):
    if isinstance(value, str):
        ipaddress.IPv4Address(value)


def ipv6_validator(value):
    if isinstance(value, str):
        ipaddress.IPv6Address(value)


def jsonpointer_validator(value):
    if isinstance(value, str):
        try:
            JSONPointer(value)
        except JSONPointerError as e:
            raise ValueError(str(e))


def evaluate(format_attr, instval, assert_=True):
    schema = JSONSchema(True)
    FormatKeyword(schema, format_attr).evaluate(JSON(instval), scope := Scope(schema))
    assert scope.annotation == format_attr
    assert scope._assert is assert_
    return scope.valid


@given(instval=hs.ip_addresses(v=4))
def test_ipv4_valid(instval):
    result = evaluate("ipv4", str(instval))
    assert result is True


@given(instval=hs.text())
def test_ipv4_invalid(instval):
    result = evaluate("ipv4", instval)
    try:
        ipaddress.IPv4Address(instval)
        assert result is True
    except ipaddress.AddressValueError:
        assert result is False


@given(instval=hs.ip_addresses(v=6))
def test_ipv6_valid(instval):
    result = evaluate("ipv6", str(instval))
    assert result is True


@given(instval=hs.text())
def test_ipv6_invalid(instval):
    result = evaluate("ipv6", instval)
    try:
        ipaddress.IPv6Address(instval)
        assert result is True
    except ipaddress.AddressValueError:
        assert result is False


@given(instval=jsonpointer)
def test_jsonpointer_valid(instval):
    result = evaluate("json-pointer", instval)
    assert result is True


@given(instval=hs.text())
def test_jsonpointer_invalid(instval):
    result = evaluate("json-pointer", instval)
    try:
        JSONPointer(instval)
        assert result is True
    except JSONPointerError:
        assert result is False


@given(instval=hs.uuids() | hs.text())
def test_uuid(instval):
    # we've not registered a "uuid" validator, so the test should always pass
    result = evaluate("uuid", str(instval), assert_=False)
    assert result is True
