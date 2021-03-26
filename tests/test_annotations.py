import pytest

from jschon.json import JSON
from jschon.jsonschema import JSONSchema
from tests import metaschema_uri_2019_09


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
    result = JSONSchema({key: value}, metaschema_uri=metaschema_uri_2019_09).evaluate(JSON({}))
    try:
        assert result.children[key].annotations[key].value == value
    except KeyError:
        assert value is None
    assert result.valid is True
    assert result.children[key].valid is True
    assert result.children[key]._assert is False
