from jschon.catalogue import jsonschema_2019_09
from jschon.uri import URI

jsonschema_2019_09.initialize()

metaschema_uri = URI("https://json-schema.org/draft/2019-09/schema")

example_schema = {
    "$id": "recursiveRef8_main.json",
    "$defs": {
        "inner": {
            "$id": "recursiveRef8_inner.json",
            "$recursiveAnchor": True,
            "title": "inner",
            "additionalProperties": {
                "$recursiveRef": "#"
            }
        }
    },
    "if": {
        "propertyNames": {
            "pattern": "^[a-m]"
        }
    },
    "then": {
        "title": "any type of node",
        "$id": "recursiveRef8_anyLeafNode.json",
        "$recursiveAnchor": True,
        "$ref": "recursiveRef8_main.json#/$defs/inner"
    },
    "else": {
        "title": "integer node",
        "$id": "recursiveRef8_integerNode.json",
        "$recursiveAnchor": True,
        "type": ["object", "integer"],
        "$ref": "recursiveRef8_main.json#/$defs/inner"
    }
}
example_valid = {"alpha": 1.1}
example_invalid = {"november": 1.1}
