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

## Usage
The following example demonstrates several key steps involved in a typical
jschon use case:

* Set up a `Catalog`.
* Create a compiled `JSONSchema`.
* `validate()` the schema against its `Metaschema`.
* Create a `JSON` instance.
* `evaluate()` the instance.
* Generate `output()` from the evaluation result.

```py
import pprint

from jschon import create_catalog, JSON, JSONSchema

# initialize the catalog, with JSON Schema 2020-12 vocabulary support
create_catalog('2020-12', default=True)

# create a schema to validate a JSON greeting object
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
            "pattern": "^Hello, .+!$"
        }
    }
})

# validate the schema against its metaschema
schema_validity = schema.validate()
print(f'Schema validity check: {schema_validity.valid}')

# declare a valid JSON instance
valid_json = JSON({
    "greeting": "Hello, World!"
})

# declare an invalid JSON instance
invalid_json = JSON({
    "greeting": "Hi, World."
})

# evaluate the valid instance
valid_result = schema.evaluate(valid_json)

# evaluate the invalid instance
invalid_result = schema.evaluate(invalid_json)

# print output for the valid case
print(f'Valid JSON result: {valid_result.valid}')
print('Valid JSON basic output:')
pprint.pp(valid_result.output('basic'))

# print output for the invalid case
print(f'Invalid JSON result: {invalid_result.valid}')
print('Invalid JSON detailed output:')
pprint.pp(invalid_result.output('detailed'))
```

The script produces the following output:

```
Schema validity check: True
Valid JSON result: True
Valid JSON basic output:
{'valid': True,
 'annotations': [{'instanceLocation': '',
                  'keywordLocation': '/properties',
                  'absoluteKeywordLocation': 'https://example.com/greeting#/properties',
                  'annotation': ['greeting']}]}
Invalid JSON result: False
Invalid JSON detailed output:
{'valid': False,
 'instanceLocation': '',
 'keywordLocation': '',
 'absoluteKeywordLocation': 'https://example.com/greeting#',
 'errors': [{'instanceLocation': '/greeting',
             'keywordLocation': '/properties/greeting/$ref/pattern',
             'absoluteKeywordLocation': 'https://example.com/greeting#/$defs/greetingDefinition/pattern',
             'error': 'The text must match the regular expression "^Hello, .+!$"'}]}
```

## Documentation
Further examples of usage, and an API reference, are available at
[Read the Docs](https://jschon.readthedocs.io/en/latest/).

## Additional resources
* [Understanding JSON Schema](https://json-schema.org/understanding-json-schema/)
* JSON Schema 2020-12 [core](https://json-schema.org/draft/2020-12/json-schema-core.html)
  and [validation](https://json-schema.org/draft/2020-12/json-schema-validation.html)
  specifications
* [jschon.dev](https://jschon.dev/) - an online validator powered by jschon

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
