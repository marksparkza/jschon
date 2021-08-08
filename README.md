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
_Note: the `create_catalogue` function will be available from v0.7.0. For v0.6.0
installations, use `Catalogue.create_default_catalogue('2020-12')`._

```python
from jschon import create_catalogue, JSON, JSONSchema
from pprint import pp

create_catalogue('2020-12', default=True)

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
The tests can be run with tox. You will need to have the relevant Python
interpreters installed on your system.

Install jschon in editable mode:

    pip install -e git+https://github.com/marksparkza/jschon.git#egg=jschon[test]

Then, `cd` to the jschon source directory (`pip show jschon` will give you the
location), and type `tox`.

## Contributing
Please see the [guidelines for contributing](CONTRIBUTING.md).
