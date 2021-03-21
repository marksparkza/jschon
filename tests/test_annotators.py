from hypothesis import given

from jschon.json import JSON
from jschon.jsonschema import Scope, JSONSchema
from jschon.vocabulary.content import *
from jschon.vocabulary.metadata import *
from tests.strategies import *


def evaluate(kwclass, kwvalue):
    schema = JSONSchema(True)
    kwclass(schema, kwvalue).evaluate(JSON({}), scope := Scope(schema))
    try:
        assert scope.annotations[kwclass.__keyword__].value == kwvalue
    except KeyError:
        assert kwvalue is None
    assert scope.valid is True


@given(jsonstring)
def test_title(kwvalue):
    evaluate(TitleKeyword, kwvalue)


@given(jsonstring)
def test_description(kwvalue):
    evaluate(DescriptionKeyword, kwvalue)


@given(json)
def test_default(kwvalue):
    evaluate(DefaultKeyword, kwvalue)


@given(jsonboolean)
def test_deprecated(kwvalue):
    evaluate(DeprecatedKeyword, kwvalue)


@given(jsonboolean)
def test_read_only(kwvalue):
    evaluate(ReadOnlyKeyword, kwvalue)


@given(jsonboolean)
def test_write_only(kwvalue):
    evaluate(WriteOnlyKeyword, kwvalue)


@given(jsonarray)
def test_examples(kwvalue):
    evaluate(ExamplesKeyword, kwvalue)


@given(jsonstring)
def test_content_media_type(kwvalue):
    evaluate(ContentMediaTypeKeyword, kwvalue)


@given(jsonstring)
def test_content_encoding(kwvalue):
    evaluate(ContentEncodingKeyword, kwvalue)


@given(jsonobject)
def test_content_schema(kwvalue):
    evaluate(ContentSchemaKeyword, kwvalue)
