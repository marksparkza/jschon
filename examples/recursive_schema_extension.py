import pprint

from jschon import Catalog, JSON, JSONSchema

# create a catalog with support for JSON Schema version 2020-12
catalog = Catalog('2020-12')

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
print(f'Tree schema result: {tree_result.valid}')
print('Tree schema flag output:')
pprint.pp(tree_result.output('flag'))
print('Tree schema basic output:')
pprint.pp(tree_result.output('basic'))
print('Tree schema detailed output:')
pprint.pp(tree_result.output('detailed'))
print('Tree schema verbose output:')
pprint.pp(tree_result.output('verbose'))

# print output for the strict-tree case
print(f'Strict tree schema result: {strict_tree_result.valid}')
print('Strict tree schema flag output:')
pprint.pp(strict_tree_result.output('flag'))
print('Strict tree schema basic output:')
pprint.pp(strict_tree_result.output('basic'))
print('Strict tree schema detailed output:')
pprint.pp(strict_tree_result.output('detailed'))
print('Strict tree schema verbose output:')
pprint.pp(strict_tree_result.output('verbose'))
