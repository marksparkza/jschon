Welcome to jschon!
==================

|tests| |codecov| |pypi| |python| |docs| |license|

jschon is a pythonic and extensible implementation of the
`JSON Schema <https://json-schema.org/>`_ specification.

Features
--------
* JSON Schema validator implementation (drafts 2019-09, 2020-12)

  * Schema compilation and indexing
  * $ref loading from local and remote sources
  * Support for custom keywords, vocabularies and meta-schemas
  * Support for format validation

* JSON class implementing the JSON data model
* JSON Pointer (`RFC 6901 <https://tools.ietf.org/html/rfc6901.html>`_)
* JSON Patch (`RFC 6902 <https://tools.ietf.org/html/rfc6902.html>`_)
* Relative JSON Pointer (`draft <https://json-schema.org/draft/2020-12/relative-json-pointer.html>`_)

Installation
------------
::

    pip install jschon

For remote $ref support, the requests library is required. It may be installed with::

    pip install jschon[requests]

Usage
-----
Create a JSON schema:

.. code-block:: python

    from jschon import create_catalog, JSON, JSONSchema

    create_catalog('2020-12')

    demo_schema = JSONSchema({
        "$id": "https://example.com/demo",
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "array",
        "items": {
            "anyOf": [
                {
                    "type": "string",
                    "description": "Cool! We got a string here!"
                },
                {
                    "type": "integer",
                    "description": "Hey! We got an integer here!"
                }
            ]
        }
    })

Validate JSON data:

.. code-block:: python

    result = demo_schema.evaluate(
        JSON([12, "Monkeys"])
    )

Generate JSON Schema-conformant output:

>>> result.output('basic')
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
            "annotation": "Hey! We got an integer here!"
        },
        {
            "instanceLocation": "/1",
            "keywordLocation": "/items/anyOf/0/description",
            "absoluteKeywordLocation": "https://example.com/demo#/items/anyOf/0/description",
            "annotation": "Cool! We got a string here!"
        }
    ]
}

Links
-----
* Documentation: https://jschon.readthedocs.io
* GitHub repository: https://github.com/marksparkza/jschon
* PyPI package: https://pypi.org/project/jschon
* Online validator: https://jschon.dev

.. |tests| image:: https://github.com/marksparkza/jschon/actions/workflows/tests.yml/badge.svg
    :target: https://github.com/marksparkza/jschon/actions/workflows/tests.yml
    :alt: Test Status

.. |codecov| image:: https://codecov.io/gh/marksparkza/jschon/branch/main/graph/badge.svg
    :target: https://codecov.io/gh/marksparkza/jschon
    :alt: Code Coverage

.. |pypi| image:: https://img.shields.io/pypi/v/jschon
    :target: https://pypi.org/project/jschon
    :alt: PyPI Package Version

.. |python| image:: https://img.shields.io/pypi/pyversions/jschon
    :target: https://pypi.org/project/jschon
    :alt: Python Versions

.. |docs| image:: https://readthedocs.org/projects/jschon/badge/?version=latest
    :target: https://jschon.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. |license| image:: https://img.shields.io/github/license/marksparkza/jschon
    :target: https://github.com/marksparkza/jschon/blob/main/LICENSE
    :alt: License
