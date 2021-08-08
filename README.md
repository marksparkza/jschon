# jschon

[![Test Status](https://github.com/marksparkza/jschon/actions/workflows/tests.yml/badge.svg)](https://github.com/marksparkza/jschon/actions/workflows/tests.yml)
[![Code Coverage](https://codecov.io/gh/marksparkza/jschon/branch/main/graph/badge.svg)](https://codecov.io/gh/marksparkza/jschon)
[![Python Versions](https://img.shields.io/pypi/pyversions/jschon)](https://pypi.org/project/jschon)
[![PyPI](https://img.shields.io/pypi/v/jschon)](https://pypi.org/project/jschon)
[![Documentation Status](https://readthedocs.org/projects/jschon/badge/?version=latest)](https://jschon.readthedocs.io/en/latest/?badge=latest)

jschon is a pythonic and extensible implementation of the [JSON Schema](https://json-schema.org)
specification.

## Features
* JSON Schema 2019-09 and 2020-12 vocabulary implementations
* Support for custom metaschemas, vocabularies and format validators
* JSON class implementing the JSON data model
* JSON pointer implementation ([RFC 6901](https://tools.ietf.org/html/rfc6901))

## Installation
    pip install jschon

## Hello World Example
```python
from jschon import create_catalog, JSON, JSONSchema
from pprint import pp

create_catalog('2020-12', default=True)

schema = JSONSchema({
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://example.com/greeting",
    "type": "object",
    "properties": {
        "greeting": {"$ref": "#/$defs/greetingDefinition"}
    },
    "$defs": {
        "greetingDefinition": {
            "type": "string",
            "minLength": 10
        }
    }
})

valid_instance = JSON({
    "greeting": "Hello, World!"
})

invalid_instance = JSON({
    "greeting": "Hi, World"
})

pp(schema.evaluate(valid_instance).valid)
# True

pp(schema.evaluate(invalid_instance).output('detailed'))
# {'valid': False,
#  'instanceLocation': '',
#  'keywordLocation': '',
#  'absoluteKeywordLocation': 'https://example.com/greeting#',
#  'errors': [{'instanceLocation': '/greeting',
#              'keywordLocation': '/properties/greeting/$ref/minLength',
#              'absoluteKeywordLocation': 'https://example.com/greeting#/$defs/greetingDefinition/minLength',
#              'error': 'The text is too short (minimum 10 characters)'}]}
```

## Documentation
Further examples, as well as a user guide and API reference, are available at
[Read the Docs](https://jschon.readthedocs.io).

## Testing
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
