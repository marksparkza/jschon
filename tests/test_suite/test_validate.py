from jschon.json import JSON
from jschon.jsonschema import JSONSchema
from tests import metaschema_uri


def test_validate(schema, data, valid):
    s = JSONSchema(schema, metaschema_uri=metaschema_uri)
    assert s.evaluate(JSON(data)).valid is valid
