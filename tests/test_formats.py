import ipaddress

from hypothesis import given, strategies as hs

from jschon.exceptions import JSONPointerError
from jschon.json import JSON
from jschon.jsonpointer import JSONPointer
from jschon.jsonschema import JSONSchema, Scope
from jschon.vocabulary.format import FormatKeyword
from tests.strategies import jsonpointer


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


FormatKeyword.register_validators({
    "ipv4": ipv4_validator,
    "ipv6": ipv6_validator,
    "json-pointer": jsonpointer_validator,
})


def evaluate(format_attr, instval):
    schema = JSONSchema(True)
    FormatKeyword(schema, format_attr).evaluate(JSON(instval), scope := Scope(schema))
    assert scope.annotations["format"].value == format_attr
    return scope.valid


@given(hs.ip_addresses(v=4))
def test_ipv4_valid(instval):
    result = evaluate("ipv4", str(instval))
    assert result is True


@given(hs.text())
def test_ipv4_invalid(instval):
    result = evaluate("ipv4", instval)
    try:
        ipaddress.IPv4Address(instval)
        assert result is True
    except ipaddress.AddressValueError:
        assert result is False


@given(hs.ip_addresses(v=6))
def test_ipv6_valid(instval):
    result = evaluate("ipv6", str(instval))
    assert result is True


@given(hs.text())
def test_ipv6_invalid(instval):
    result = evaluate("ipv6", instval)
    try:
        ipaddress.IPv6Address(instval)
        assert result is True
    except ipaddress.AddressValueError:
        assert result is False


@given(jsonpointer)
def test_jsonpointer_valid(instval):
    result = evaluate("json-pointer", instval)
    assert result is True


@given(hs.text())
def test_jsonpointer_invalid(instval):
    result = evaluate("json-pointer", instval)
    try:
        JSONPointer(instval)
        assert result is True
    except JSONPointerError:
        assert result is False


@given(hs.uuids() | hs.text())
def test_uuid(instval):
    # we've not registered a "uuid" validator, so the test should always pass
    result = evaluate("uuid", str(instval))
    assert result is True
