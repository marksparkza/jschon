Getting Started
===============

Installation
------------
::

    pip install jschon

A basic example
---------------
The example shown below illustrates several key aspects of jschon usage:

* :class:`~jschon.catalog.Catalog` setup
* Construction of a compiled, reusable :class:`~jschon.jsonschema.JSONSchema` object
* Validation of the schema by a :class:`~jschon.vocabulary.Metaschema`
* Construction of a :class:`~jschon.json.JSON` instance
* Evaluation of the instance
* Output generation

.. literalinclude:: ../../examples/hello_world.py

The script produces the following output:

.. literalinclude:: ../../examples/output/hello_world.txt
