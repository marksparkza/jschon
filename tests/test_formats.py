import ipaddress

import pytest
from hypothesis import given, strategies as hs

from jschon import JSON, JSONPointer, JSONPointerError
from jschon.jsonschema import Scope
from jschon.vocabulary.format import FormatKeyword
from tests.strategies import jsonpointer


@pytest.fixture(scope='module', autouse=True)
def setup_validators(catalogue):
    catalogue.add_format_validators({
        "ipv4": ipv4_validator,
        "ipv6": ipv6_validator,
        "json-pointer": jsonpointer_validator,
    })
    yield
    catalogue._format_validators.clear()


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


def evaluate(format_attr, instval, catalogue, assert_=True):
    schema = catalogue.create_schema(True)
    FormatKeyword(schema, format_attr).evaluate(JSON(instval), scope := Scope(schema))
    assert scope.annotations["format"].value == format_attr
    assert scope._assert is assert_
    return scope.valid


@given(instval=hs.ip_addresses(v=4))
def test_ipv4_valid(instval, catalogue):
    result = evaluate("ipv4", str(instval), catalogue)
    assert result is True


@given(instval=hs.text())
def test_ipv4_invalid(instval, catalogue):
    result = evaluate("ipv4", instval, catalogue)
    try:
        ipaddress.IPv4Address(instval)
        assert result is True
    except ipaddress.AddressValueError:
        assert result is False


@given(instval=hs.ip_addresses(v=6))
def test_ipv6_valid(instval, catalogue):
    result = evaluate("ipv6", str(instval), catalogue)
    assert result is True


@given(instval=hs.text())
def test_ipv6_invalid(instval, catalogue):
    result = evaluate("ipv6", instval, catalogue)
    try:
        ipaddress.IPv6Address(instval)
        assert result is True
    except ipaddress.AddressValueError:
        assert result is False


@given(instval=jsonpointer)
def test_jsonpointer_valid(instval, catalogue):
    result = evaluate("json-pointer", instval, catalogue)
    assert result is True


@given(instval=hs.text())
def test_jsonpointer_invalid(instval, catalogue):
    result = evaluate("json-pointer", instval, catalogue)
    try:
        JSONPointer(instval)
        assert result is True
    except JSONPointerError:
        assert result is False


@given(instval=hs.uuids() | hs.text())
def test_uuid(instval, catalogue):
    # we've not registered a "uuid" validator, so the test should always pass
    result = evaluate("uuid", str(instval), catalogue, assert_=False)
    assert result is True
