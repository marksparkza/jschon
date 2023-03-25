import ipaddress

import pytest
from hypothesis import given, strategies as hs

from jschon import JSON, JSONPointer, JSONPointerError, JSONSchema
from jschon.jsonschema import Result
from jschon.vocabulary.format import FormatKeyword, format_validator
from tests.strategies import jsonpointer


@pytest.fixture(autouse=True)
def setup_validators(catalog):
    catalog.enable_formats(
        "ipv4",
        "ipv6",
        "json-pointer",
    )
    yield
    catalog._enabled_formats.clear()


@format_validator('ipv4')
def ipv4_validator(value):
    if isinstance(value, str):
        ipaddress.IPv4Address(value)


@format_validator('ipv6')
def ipv6_validator(value):
    if isinstance(value, str):
        ipaddress.IPv6Address(value)


def evaluate(format_attr, instval, assert_=True):
    schema = JSONSchema(True)
    FormatKeyword(schema, format_attr).evaluate(inst := JSON(instval), result := Result(schema, inst))
    assert result.annotation == format_attr
    assert result._assert is assert_
    return result.valid


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
