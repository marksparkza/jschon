import pytest

from jschon.json import JSON
from jschon.jsonschema import Scope, JSONSchema
from jschon.vocabulary.annotation import AnnotationKeyword


@pytest.mark.parametrize('key, value', [
    ("title", "Test Title"),
    ("description", "Test Description"),
    ("default", "Test Default"),
    ("deprecated", True),
    ("readOnly", False),
    ("writeOnly", True),
    ("examples", ["foo", 1.1, {"bar": None}]),
    ("contentMediaType", "application/json"),
    ("contentEncoding", "base64"),
    ("contentSchema", {"required": ["foo"], "properties": {"foo": {"type": "string"}}}),
])
def test_annotate(key, value):
    AnnotationKeyword(schema := JSONSchema(True), key, value).evaluate(JSON({}), scope := Scope(schema))
    try:
        assert scope.annotations[key].value == value
    except KeyError:
        assert value is None
    assert scope.valid is True
    assert scope._assert is False
