import re

import email_validator
import rfc3986.exceptions
import rfc3986.validators
from hypothesis import given, strategies as hs, provisional as hp

from jschon.exceptions import JSONPointerError
from jschon.json import JSONString
from jschon.jsonpointer import JSONPointer
from jschon.jsonschema import JSONSchema
from jschon.keywords import FormatKeyword
from tests import metaschema_uri
from tests.strategies import jsonpointer


def evaluate_format(format_attr, instance):
    kw = FormatKeyword(JSONSchema(True, metaschema_uri=metaschema_uri), format_attr)
    return kw.evaluate(JSONString(instance))


@given(hs.emails() | hs.text())
def test_email(instance):
    result = evaluate_format("email", instance)
    try:
        email_validator.validate_email(instance, allow_smtputf8=False, check_deliverability=False)
        assert result.valid is True
    except email_validator.EmailNotValidError:
        assert result.valid is False


@given(hs.emails() | hs.text())
def test_idnemail(instance):
    result = evaluate_format("idn-email", instance)
    try:
        email_validator.validate_email(instance, allow_smtputf8=True, check_deliverability=False)
        assert result.valid is True
    except email_validator.EmailNotValidError:
        assert result.valid is False


@given(hp.urls())
def test_uri_valid(instance):
    result = evaluate_format("uri", instance)
    assert result.valid is True


@given(hs.text())
def test_uri_invalid(instance):
    result = evaluate_format("uri", instance)
    validator = rfc3986.validators.Validator().require_presence_of('scheme')
    try:
        validator.validate(rfc3986.uri_reference(instance))
        assert result.valid is True
    except rfc3986.exceptions.ValidationError:
        assert result.valid is False


@given(hp.urls() | jsonpointer)
def test_urireference_valid(instance):
    result = evaluate_format("uri-reference", instance)
    assert result.valid is True


@given(hs.text())
def test_urireference_invalid(instance):
    result = evaluate_format("uri-reference", instance)
    validator = rfc3986.validators.Validator()
    try:
        validator.validate(rfc3986.uri_reference(instance))
        assert result.valid is True
    except rfc3986.exceptions.ValidationError:
        assert result.valid is False


@given(jsonpointer)
def test_jsonpointer_valid(instance):
    result = evaluate_format("json-pointer", instance)
    assert result.valid is True


@given(hs.text())
def test_jsonpointer_invalid(instance):
    result = evaluate_format("json-pointer", instance)
    try:
        JSONPointer(instance)
        assert result.valid is True
    except JSONPointerError:
        assert result.valid is False


@given(hs.text(hs.from_regex(r'[0-9\[\]\-^+*?{},$()|]')))
def test_regex(instance):
    result = evaluate_format("regex", instance)
    try:
        re.compile(instance)
        assert result.valid is True
    except re.error:
        assert result.valid is False
