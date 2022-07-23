import pytest

from jschon import JSON, JSONSchema, JSONPointer
from tests import metaschema_uri_2020_12


@pytest.mark.parametrize('key, value', [
    ("title", "Test Title"),
    ("description", "Test Description"),
    ("default", "Test Default"),
    ("deprecated", True),
    ("readOnly", False),
    ("writeOnly", None),
    ("examples", ["foo", 1.1, {"bar": None}]),
    ("contentMediaType", "application/json"),
    ("contentEncoding", "base64"),
])
def test_annotate(key, value):
    result = JSONSchema({key: value}, metaschema_uri=metaschema_uri_2020_12).evaluate(JSON(""))
    instpath = JSONPointer()
    assert result.valid is True
    assert result.children[key, instpath].valid is True
    assert result.children[key, instpath]._assert is False
    try:
        assert result.children[key, instpath].annotation == value
    except KeyError:
        assert value is None


def test_content_schema():
    example = {
        "contentMediaType": "application/json",
        "contentSchema": {"required": ["foo"], "properties": {"foo": {"type": "string"}}},
    }
    result = JSONSchema(example, metaschema_uri=metaschema_uri_2020_12).evaluate(JSON(""))
    instpath = JSONPointer()
    assert result.children["contentSchema", instpath].annotation == example["contentSchema"]

    del example["contentMediaType"]
    result = JSONSchema(example, metaschema_uri=metaschema_uri_2020_12).evaluate(JSON(""))
    assert "contentSchema" not in result.children
