Recursive schema extension
==========================
The following script implements the
`recursive schema extension example <https://json-schema.org/draft/2020-12/json-schema-core.html#recursive-example>`_,
described in the JSON Schema 2020-12 core specification.

.. literalinclude:: ../../examples/recursive_schema_extension.py

The script produces the output shown below. The ``'verbose'`` output
format reflects the complete dynamic evaluation path through a schema
and any referenced schemas.

.. literalinclude:: ../../examples/output/recursive_schema_extension.txt
