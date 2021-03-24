from hypothesis import given

from jschon.json import JSON
from jschon.jsonschema import Scope, JSONSchema
from jschon.vocabulary.content import *
from jschon.vocabulary.metadata import *
from tests.strategies import *


def evaluate(kwclass, key, kwvalue):
    schema = JSONSchema(True)
    kwclass(schema, key, kwvalue, ()).evaluate(JSON({}), scope := Scope(schema))
    try:
        assert scope.annotations[key].value == kwvalue
    except KeyError:
        assert kwvalue is None
    assert scope.valid is True


@given(jsonstring)
def test_title(kwvalue):
    evaluate(TitleKeyword, "title", kwvalue)


@given(jsonstring)
def test_description(kwvalue):
    evaluate(DescriptionKeyword, "description", kwvalue)


@given(json)
def test_default(kwvalue):
    evaluate(DefaultKeyword, "default", kwvalue)


@given(jsonboolean)
def test_deprecated(kwvalue):
    evaluate(DeprecatedKeyword, "deprecated", kwvalue)


@given(jsonboolean)
def test_read_only(kwvalue):
    evaluate(ReadOnlyKeyword, "readOnly", kwvalue)


@given(jsonboolean)
def test_write_only(kwvalue):
    evaluate(WriteOnlyKeyword, "writeOnly", kwvalue)


@given(jsonarray)
def test_examples(kwvalue):
    evaluate(ExamplesKeyword, "examples", kwvalue)


@given(jsonstring)
def test_content_media_type(kwvalue):
    evaluate(ContentMediaTypeKeyword, "contentMediaType", kwvalue)


@given(jsonstring)
def test_content_encoding(kwvalue):
    evaluate(ContentEncodingKeyword, "contentEncoding", kwvalue)


@given(jsonobject)
def test_content_schema(kwvalue):
    evaluate(ContentSchemaKeyword, "contentSchema", kwvalue)
