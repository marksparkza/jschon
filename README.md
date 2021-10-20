# jschon

[![Test Status](https://github.com/marksparkza/jschon/actions/workflows/tests.yml/badge.svg)](https://github.com/marksparkza/jschon/actions/workflows/tests.yml)
[![Code Coverage](https://codecov.io/gh/marksparkza/jschon/branch/main/graph/badge.svg)](https://codecov.io/gh/marksparkza/jschon)
[![Python Versions](https://img.shields.io/pypi/pyversions/jschon)](https://pypi.org/project/jschon)
[![PyPI](https://img.shields.io/pypi/v/jschon)](https://pypi.org/project/jschon)
[![Documentation Status](https://readthedocs.org/projects/jschon/badge/?version=latest)](https://jschon.readthedocs.io/en/latest/?badge=latest)

jschon is a pythonic and extensible implementation of the [JSON Schema](https://json-schema.org)
specification.

The development status of the project is **alpha**. API and internals may change
from one release to the next. Please keep an eye on the [change log](CHANGELOG.md)!

## Features
* JSON Schema validator
    * Implements the 2019-09 and 2020-12 JSON Schema vocabularies
    * Supports format assertion via plug-in callables
    * Compiles and indexes schemas for efficient reuse
    * Loads schemas and data from configured local and (coming soon) remote sources
    * Provides a framework for creating custom keywords, vocabularies and metaschemas
* JSON class implementing the JSON data model
* JSON pointer implementation ([RFC 6901](https://tools.ietf.org/html/rfc6901))

## Installation
    pip install jschon

## Usage
jschon enables you to create JSON schemas for annotating and validating JSON data:

```py
from jschon import create_catalog, JSON, JSONSchema

create_catalog('2020-12', default=True)

demo_schema = JSONSchema({
    "$id": "https://example.com/demo",
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "array",
    "items": {
        "anyOf": [
            {
                "type": "integer",
                "description": "It's an int!"
            },
            {
                "type": "string",
                "description": "It's a str!"
            }
        ]
    }
})

valid_json = JSON(["one", 2])

result = demo_schema.evaluate(valid_json)

print(result.output('basic'))
```

The example above produces the following output:
```
{
    "valid": True,
    "annotations": [
        {
            "instanceLocation": "",
            "keywordLocation": "/items",
            "absoluteKeywordLocation": "https://example.com/demo#/items",
            "annotation": True
        },
        {
            "instanceLocation": "/0",
            "keywordLocation": "/items/anyOf/1/description",
            "absoluteKeywordLocation": "https://example.com/demo#/items/anyOf/1/description",
            "annotation": "It's a str!"
        },
        {
            "instanceLocation": "/1",
            "keywordLocation": "/items/anyOf/0/description",
            "absoluteKeywordLocation": "https://example.com/demo#/items/anyOf/0/description",
            "annotation": "It's an int!"
        }
    ]
}
```

JSON schemas and instances can be deserialized directly from JSON files
and JSON strings:
```py
demo_schema = JSONSchema.loadf('/path/to/demo/schema.json')

invalid_json = JSON.loads('{"foo": "bar"}')

result = demo_schema.evaluate(invalid_json)

print(result.output('basic'))
```

The invalid case produces the following error output:
```
{
    "valid": False,
    "errors": [
        {
            "instanceLocation": "",
            "keywordLocation": "/type",
            "absoluteKeywordLocation": "https://example.com/demo#/type",
            "error": "The instance must be of type \"array\""
        }
    ]
}
```

## Documentation
Further examples of usage, and an API reference, are available at
[Read the Docs](https://jschon.readthedocs.io/en/latest/).

## Additional resources
* [jschon.dev](https://jschon.dev/) - an online validator powered by jschon
* JSON Schema 2020-12 [core](https://json-schema.org/draft/2020-12/json-schema-core.html)
  and [validation](https://json-schema.org/draft/2020-12/json-schema-validation.html)
  specifications
* [Understanding JSON Schema](https://json-schema.org/understanding-json-schema/)

## Running the tests
jschon is tested using the
[JSON Schema Test Suite](https://github.com/marksparkza/JSON-Schema-Test-Suite)
(excluding optional and format tests), along with custom unit tests that make
use of the [Hypothesis](https://hypothesis.readthedocs.io) testing library.

To run the tests, install jschon in editable mode, including testing dependencies:

    pip install -e git+https://github.com/marksparkza/jschon.git#egg=jschon[test]

Then, `cd` to the jschon source directory (`pip show jschon` will give you the
location), and type `tox`.

Note that a complete test run requires all of the supported Python versions
(3.8, 3.9, 3.10) to be installed on your system.

## Contributing
Please see the [guidelines for contributing](CONTRIBUTING.md).
