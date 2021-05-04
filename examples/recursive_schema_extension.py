from jschon import Catalogue, JSON, JSONSchema

# create a catalogue, initialized with the JSON Schema 2020-12
# metaschema and vocabularies
Catalogue.create_default_catalogue('2020-12')

# define an extensible tree schema
tree_schema = JSONSchema({
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://example.com/tree",
    "$dynamicAnchor": "node",
    "type": "object",
    "properties": {
        "data": True,
        "children": {
            "type": "array",
            "items": {
                "$dynamicRef": "#node"
            }
        }
    }
})

# define a strict-tree schema, which guards against misspelled properties
strict_tree_schema = JSONSchema({
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://example.com/strict-tree",
    "$dynamicAnchor": "node",
    "$ref": "tree",
    "unevaluatedProperties": False
})

# declare a JSON instance with a misspelled field
tree_instance = JSON({
    "children": [{"daat": 1}]
})

print(tree_schema.evaluate(tree_instance).valid)
# True

print(strict_tree_schema.evaluate(tree_instance).valid)
# False
