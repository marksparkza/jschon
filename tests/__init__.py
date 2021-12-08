from jschon import URI

metaschema_uri_2019_09 = URI("https://json-schema.org/draft/2019-09/schema")
metaschema_uri_2020_12 = URI("https://json-schema.org/draft/2020-12/schema")

example_schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "dynamicRef8_main.json",
    "$defs": {
        "inner": {
            "$id": "dynamicRef8_inner.json",
            "$dynamicAnchor": "foo",
            "title": "inner",
            "additionalProperties": {
                "$dynamicRef": "#foo"
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
        "$id": "dynamicRef8_anyLeafNode.json",
        "$dynamicAnchor": "foo",
        "$ref": "dynamicRef8_main.json#/$defs/inner"
    },
    "else": {
        "title": "integer node",
        "$id": "dynamicRef8_integerNode.json",
        "$dynamicAnchor": "foo",
        "type": ["object", "integer"],
        "$ref": "dynamicRef8_main.json#/$defs/inner"
    }
}
example_valid = {"alpha": 1.1}
example_invalid = {"november": 1.1}
