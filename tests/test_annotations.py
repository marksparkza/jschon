import pytest

from jschon import JSON
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
def test_annotate(key, value, catalogue):
    result = catalogue.create_schema({key: value}, metaschema_uri=metaschema_uri_2020_12).evaluate(JSON(""))
    assert result.valid is True
    assert result.children[key].valid is True
    assert result.children[key]._assert is False
    try:
        assert result.children[key].annotations[key].value == value
    except KeyError:
        assert value is None


def test_content_schema(catalogue):
    example = {
        "contentMediaType": "application/json",
        "contentSchema": {"required": ["foo"], "properties": {"foo": {"type": "string"}}},
    }
    result = catalogue.create_schema(example, metaschema_uri=metaschema_uri_2020_12).evaluate(JSON(""))
    assert result.children["contentSchema"].annotations["contentSchema"].value == example["contentSchema"]

    del example["contentMediaType"]
    result = catalogue.create_schema(example, metaschema_uri=metaschema_uri_2020_12).evaluate(JSON(""))
    assert "contentSchema" not in result.children
