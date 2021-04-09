# Jschon

[![Test Status](https://github.com/marksparkza/jschon/actions/workflows/tests.yml/badge.svg)](https://github.com/marksparkza/jschon/actions/workflows/tests.yml)
[![Code Coverage](https://codecov.io/gh/marksparkza/jschon/branch/main/graph/badge.svg)](https://codecov.io/gh/marksparkza/jschon)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/jschon)](https://pypi.org/project/jschon)
[![PyPI](https://img.shields.io/pypi/v/jschon)](https://pypi.org/project/jschon)

Welcome to Jschon, a JSON Schema implementation for Python!

## Features

* [JSON Schema](https://json-schema.org) implementation, supporting specification drafts
  2019-09 and 2020-12
* [RFC 6901](https://tools.ietf.org/html/rfc6901) conformant JSON Pointer implementation
* JSON document class
* URI class (wraps rfc3986.URIReference)

## Installation

    pip install jschon

## Usage

For a demonstration, let's implement
[this example](https://json-schema.org/draft/2020-12/json-schema-core.html#recursive-example):

```python
from jschon.catalogue import jsonschema_2020_12
from jschon.json import JSON
from jschon.jsonschema import JSONSchema

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
}).validate()  # validate the schema against its metaschema

# define a strict-tree schema, which guards against misspelled properties
strict_tree_schema = JSONSchema({
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://example.com/strict-tree",
    "$dynamicAnchor": "node",
    "$ref": "tree",
    "unevaluatedProperties": False
}).validate()  # validate the schema against its metaschema

# declare a JSON instance with a misspelled field
tree_instance = JSON({
    "children": [{"daat": 1}]
})

print(tree_schema.evaluate(tree_instance).valid)  # True
print(strict_tree_schema.evaluate(tree_instance).valid)  # False
```

## Contributing

See the [guidelines for contributing](CONTRIBUTING.md).
