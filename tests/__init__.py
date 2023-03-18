from jschon import URI

metaschema_uri_2019_09 = URI("https://json-schema.org/draft/2019-09/schema")
metaschema_uri_2020_12 = URI("https://json-schema.org/draft/2020-12/schema")
metaschema_uri_next = URI("https://json-schema.org/draft/next/schema")

core_vocab_uri_2019_09 = URI("https://json-schema.org/draft/2019-09/vocab/core")
core_vocab_uri_2020_12 = URI("https://json-schema.org/draft/2020-12/vocab/core")
core_vocab_uri_next = URI("https://json-schema.org/draft/next/vocab/core")

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


schema_bundle1 = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://example.com/bundle1",
    "$defs": {
        "a": {
            "$id": "https://example.com/source1/a",
            "$ref": "../source2/b#/$defs/inner",
        },
        "b": {
            "$id": "https://example.com/source1/b",
            "$dynamicAnchor": "here",
            "type": "object",
            "$defs": {
                "inner": {
                    "$dynamicRef": "#here",
                },
            },
        },
    },
}
schema_bundle2 = {
    "$schema": "https://json-schema.org/draft/2019-09/schema",
    "$id": "https://example.com/bundle2",
    "$defs": {
        "a": {
            "$id": "https://example.com/source2/a",
            "$ref": "../source1/b#/$defs/inner",
        },
        "b": {
            "$id": "https://example.com/source2/b",
            "$recursiveAnchor": True,
            "type": "array",
            "$defs": {
                "inner": {
                    "$recursiveRef": "#"
                }
            }
        },
    },
}
