# jschon

[![Test Status](https://github.com/marksparkza/jschon/actions/workflows/tests.yml/badge.svg)](https://github.com/marksparkza/jschon/actions/workflows/tests.yml)
[![Code Coverage](https://codecov.io/gh/marksparkza/jschon/branch/main/graph/badge.svg)](https://codecov.io/gh/marksparkza/jschon)
[![Python Versions](https://img.shields.io/pypi/pyversions/jschon)](https://pypi.org/project/jschon)
[![PyPI](https://img.shields.io/pypi/v/jschon)](https://pypi.org/project/jschon)

Welcome to jschon, a JSON Schema implementation for Python!

## Features
* [JSON Schema](https://json-schema.org) implementation, supporting specification drafts
  2019-09 and 2020-12
* Catalogue supporting custom metaschemas, vocabularies and format validators
* JSON class implementing the JSON data model
* [RFC 6901](https://tools.ietf.org/html/rfc6901) conformant JSON Pointer implementation
* URI class (wraps rfc3986.URIReference)

## Installation
    pip install jschon

## Usage
* [JSON](#json)
* [JSON Pointer](#jsonpointer)
* [JSON Schema](#jsonschema)

### A quick demo
Let's implement this [example](https://json-schema.org/draft/2020-12/json-schema-core.html#recursive-example),
described in the JSON Schema core specification. We define a recursive tree structure,
where each node in a tree can have a "data" field of any type. The first schema
allows and ignores other instance properties. The second - an extension of the first -
is more strict and only allows the "data" and "children" properties.

An example JSON instance with "data" misspelled as "daat" passes evaluation by the first
schema, but fails against the second.

```python
from jschon import JSON, JSONSchema
from jschon.catalogue import jsonschema_2020_12

# initialize the JSON Schema 2020-12 metaschema and vocabularies
jsonschema_2020_12.initialize()

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

print(tree_schema.evaluate(tree_instance).valid)  # True
print(strict_tree_schema.evaluate(tree_instance).valid)  # False
```

### JSON
All of the following code snippets may be copy-pasted into a Python console.
The expected output of an expression is shown in a comment, where applicable.
Begin by importing the `JSON` class:
```
from jschon import JSON
```
A `JSON` instance may be constructed from any JSON-compatible Python object.
Let's take a look at a few simple examples, printing the JSON type of each:
```
JSON(None).type                          # 'null'
```
```
JSON(True).type                          # 'boolean'
```
```
JSON(3.14159).type                       # 'number'
```
```
JSON("Hello, World!").type               # 'string'
```
```
JSON((1, 2, 3)).type                     # 'array'
```
```
JSON({"foo": True, "bar": False}).type   # 'object'
```
Instances with the JSON types "array" and "object" are constructed recursively.
Let's create an array and an object:
```
arr = JSON([1, 2, 3])
obj = JSON({"foo": True, "bar": False})
```
Nested `JSON` instances may be accessed using square-bracket notation:
```
arr[1]                                   # JSON(2)
```
```
obj["foo"]                               # JSON(True)
```
`JSON` implements the `Sequence` and `Mapping` interfaces for instances with
the JSON types "array" and "object", respectively.
```
[item for item in arr]                   # [JSON(1), JSON(2), JSON(3)]
```
```
{key: val for key, val in obj.items()}   # {'foo': JSON(True), 'bar': JSON(False)}
```
`JSON` instances have a number of attributes, in addition to the `type` attribute
seen above. These can be useful when working with complex JSON structures.
Consider the following example:
```
document = JSON({
    "1a": {
        "2a": "foo",
        "2b": "bar"
    },
    "1b": [
        {"3a": "baz"},
        {"3b": "qux"}
    ]
})
```
```
document["1a"]["2a"].value               # 'foo'
```
```
document["1a"]["2b"].parent              # JSON({'2a': 'foo', '2b': 'bar'})
```
```
document["1b"][0]["3a"].key              # '3a'
```
```
document["1b"][1]["3b"].path             # JSONPointer('/1b/1/3b')
```
Notice that, although an array item's index is an integer, its `key` attribute is a
string. This makes it interoperable with `JSONPointer`:
```
document["1b"][1].key                    # '1'
```
The `value` of a non-leaf node consists of `JSON` instances (though the keys of a
JSON "object" are always strings):
```
document["1a"].value                     # {'2a': JSON('foo'), '2b': JSON('bar')}
```
```
document["1b"].value                     # [JSON({'3a': 'baz'}), JSON({'3b': 'qux'})]
```

### JSONPointer


### JSONSchema


## Contributing
See the [guidelines for contributing](CONTRIBUTING.md).
