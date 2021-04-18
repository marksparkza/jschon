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
* [JSONPointer](#jsonpointer)
* [JSONSchema](#jsonschema)

### A quick demo
For a demonstration, let's implement this
[example](https://json-schema.org/draft/2020-12/json-schema-core.html#recursive-example),
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
The following code snippets may be copy-pasted into a Python console;
expected values of expressions are shown in the adjacent comments.
We begin by importing the `JSON` class:
```py
from jschon import JSON
```
A `JSON` instance may be constructed from any JSON-compatible Python object.
Let's take a look at a few simple examples, printing the JSON type of each:
```py
JSON(None).type                           # 'null'
```
```py
JSON(True).type                           # 'boolean'
```
```py
JSON(3.14159).type                        # 'number'
```
```py
JSON("Hello, World!").type                # 'string'
```
```py
JSON((1, 2, 3)).type                      # 'array'
```
```py
JSON({"foo": True, "bar": False}).type    # 'object'
```
Instances with the JSON types "array" and "object" are constructed recursively.
Here we create an array and an object:
```py
arr = JSON([1, 2, 3])
obj = JSON({"foo": True, "bar": False})
```
Nested `JSON` instances may be accessed using square-bracket notation:
```py
arr[1]                                    # JSON(2)
```
```py
obj["foo"]                                # JSON(True)
```
`JSON` implements the `Sequence` and `Mapping` interfaces for instances with
the JSON types "array" and "object", respectively:
```py
[item for item in arr]                    # [JSON(1), JSON(2), JSON(3)]
```
```py
{key: val for key, val in obj.items()}    # {'foo': JSON(True), 'bar': JSON(False)}
```
`JSON` instances have several attributes, in addition to the `type` attribute
seen above. These can be useful when working with complex JSON structures.
Consider the following example:
```py
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
A leaf node's `value` is the value from which it was constructed:
```py
document["1a"]["2a"].value                # 'foo'
```
The `parent` attribute gives the containing instance:
```py
document["1a"]["2b"].parent               # JSON({'2a': 'foo', '2b': 'bar'})
```
The `path` property returns a `JSONPointer` instance representing the path to the
node from the document root:
```py
document["1b"][0]["3a"].path              # JSONPointer('/1b/0/3a')
```
The `key` is the index of the node within its parent:
```py
document["1b"][1]["3b"].key               # '3b'
```
Notice that, although an array item's sequential index is an integer, its `key`
attribute is a string. This makes it interoperable with `JSONPointer`:
```py
document["1b"][1].key                     # '1'
```
The `value` of an "object" node is a `dict[str, JSON]`:
```py
document["1a"].value                      # {'2a': JSON('foo'), '2b': JSON('bar')}
```
The `value` of an "array" node is a `list[JSON]`:
```py
document["1b"].value                      # [JSON({'3a': 'baz'}), JSON({'3b': 'qux'})]
```
Equality testing strictly follows the JSON data model. So, whereas the following two
Python lists compare equal:
```py
[False, True] == [0, 1]                   # True
```
The `JSON` equivalents are not equal, because the arrays' items have different
JSON types:
```py
JSON([False, True]) == JSON([0, 1])       # False
```
`JSON` also implements the `<`, `<=`, `>=`, `>` and `!=` comparison operators, which
may be used wherever it makes sense for the types of the given operands:
```py
JSON(3) < JSON(3.01)                      # True
```
A `JSON` instance may be compared with _any_ Python object. Internally, the non-`JSON`
object is cast to its `JSON` equivalent before performing the comparison. Notice that
tuples and lists are considered structurally equivalent:
```py
(7, 11) == JSON([7, 11])                  # True
```
Jschon is not a JSON encoder/decoder. However, the `JSON` class supports both
serialization and deserialization of JSON documents, via the Python standard library's
`json` module.

Serializing a `JSON` instance is simply a matter of getting its string representation;
for example:
```py
str(JSON({'xyz': (None, False, True)}))   # '{"xyz": [null, false, true]}'
```
`JSON` instances can be deserialized from JSON files and JSON strings using the
`loadf` and `loads` class methods, respectively:
```py
JSON.loadf('/path/to/file.json')          # JSON(...)
```
```py
JSON.loads('{"1": "spam", "2": "eggs"}')  # JSON({'1': 'spam', '2': 'eggs'})
```
Finally, a word on floating point numbers:

To ensure reliable operation of the JSON Schema "multipleOf" keyword, `float` values
are converted to `decimal.Decimal` by the `JSON` constructor, and floats are parsed as
`decimal.Decimal` during deserialization:
```py
JSON(5.1).value                           # Decimal('5.1')
```

### JSONPointer


### JSONSchema


## Contributing
See the [guidelines for contributing](CONTRIBUTING.md).
