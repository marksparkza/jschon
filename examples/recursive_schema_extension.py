import pprint

from jschon import create_catalog, JSON, JSONSchema

# create a catalog with support for JSON Schema version 2020-12
create_catalog('2020-12')

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
tree_json = JSON({
    "children": [{"daat": 1}]
})

# evaluate the JSON instance with the tree schema
tree_result = tree_schema.evaluate(tree_json)

# evaluate the JSON instance with the strict-tree schema
strict_tree_result = strict_tree_schema.evaluate(tree_json)

# print output for the tree case
print('Tree schema verbose output:')
pprint.pp(tree_result.output('verbose'))

# print output for the strict-tree case
print('Strict tree schema verbose output:')
pprint.pp(strict_tree_result.output('verbose'))
