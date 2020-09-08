import re

import email_validator
import rfc3986.exceptions
import rfc3986.validators
from hypothesis import given, strategies as hs, provisional as hp

from jschon.exceptions import JSONPointerError
from jschon.json import JSONString
from jschon.jsoninstance import JSONInstance
from jschon.jsonpointer import JSONPointer
from jschon.jsonschema import JSONSchema
from jschon.keywords import FormatKeyword
from tests import metaschema_uri
from tests.strategies import jsonpointer


def evaluate_format(format_attr, instval):
    kw = FormatKeyword(JSONSchema(True, metaschema_uri=metaschema_uri), format_attr)
    kw.evaluate(instance := JSONInstance(JSONString(instval), JSONPointer(), None))
    return instance


@given(hs.emails() | hs.text())
def test_email(instval):
    result = evaluate_format("email", instval)
    try:
        email_validator.validate_email(instval, allow_smtputf8=False, check_deliverability=False)
        assert result.valid is True
    except email_validator.EmailNotValidError:
        assert result.valid is False


@given(hs.emails() | hs.text())
def test_idnemail(instval):
    result = evaluate_format("idn-email", instval)
    try:
        email_validator.validate_email(instval, allow_smtputf8=True, check_deliverability=False)
        assert result.valid is True
    except email_validator.EmailNotValidError:
        assert result.valid is False


@given(hp.urls())
def test_uri_valid(instval):
    result = evaluate_format("uri", instval)
    assert result.valid is True


@given(hs.text())
def test_uri_invalid(instval):
    result = evaluate_format("uri", instval)
    validator = rfc3986.validators.Validator().require_presence_of('scheme')
    try:
        validator.validate(rfc3986.uri_reference(instval))
        assert result.valid is True
    except rfc3986.exceptions.ValidationError:
        assert result.valid is False


@given(hp.urls() | jsonpointer)
def test_urireference_valid(instval):
    result = evaluate_format("uri-reference", instval)
    assert result.valid is True


@given(hs.text())
def test_urireference_invalid(instval):
    result = evaluate_format("uri-reference", instval)
    validator = rfc3986.validators.Validator()
    try:
        validator.validate(rfc3986.uri_reference(instval))
        assert result.valid is True
    except rfc3986.exceptions.ValidationError:
        assert result.valid is False


@given(jsonpointer)
def test_jsonpointer_valid(instval):
    result = evaluate_format("json-pointer", instval)
    assert result.valid is True


@given(hs.text())
def test_jsonpointer_invalid(instval):
    result = evaluate_format("json-pointer", instval)
    try:
        JSONPointer(instval)
        assert result.valid is True
    except JSONPointerError:
        assert result.valid is False


@given(hs.text(hs.from_regex(r'[0-9\[\]\-^+*?{},$()|]')))
def test_regex(instval):
    result = evaluate_format("regex", instval)
    try:
        re.compile(instval)
        assert result.valid is True
    except re.error:
        assert result.valid is False
