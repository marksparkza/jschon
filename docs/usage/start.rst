Getting Started
===============

Installation
------------
::

    pip install jschon

A basic example
---------------
The following example demonstrates several key steps involved in a typical
jschon use case:

* Set up a :class:`~jschon.catalog.Catalog`.
* Create a compiled :class:`~jschon.jsonschema.JSONSchema` object.
* :meth:`~jschon.jsonschema.JSONSchema.validate` the schema against its :class:`~jschon.vocabulary.Metaschema`.
* Create a :class:`~jschon.json.JSON` instance.
* :meth:`~jschon.jsonschema.JSONSchema.evaluate` the instance.
* Generate :meth:`~jschon.jsonschema.Scope.output` from the evaluation result.

.. literalinclude:: ../../examples/hello_world.py

The script produces the following output:

.. literalinclude:: ../../examples/output/hello_world.txt
