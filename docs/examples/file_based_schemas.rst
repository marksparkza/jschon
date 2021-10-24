File-based schemas
==================
Suppose that we've created several JSON schema files that we'd like to use
to validate organization data. For this example, our schemas and our data are
stored in a ``data`` directory, relative to the location of the Python scripts
that follow.

The primary schema is an org schema, stored in ``data/org-schema.json``:

.. literalinclude:: ../../examples/data/org-schema.json

The org schema references a person schema, stored in ``data/person-schema.json``:

.. literalinclude:: ../../examples/data/person-schema.json

We're going to use the org schema to validate our org data, which can be
found in ``data/org-data.json``:

.. literalinclude:: ../../examples/data/org-data.json

There are several different ways to ensure that all our schemas are loaded
and available as needed.

The first way is to load all of our schemas up front. In this case, when
the ``"$ref"`` keyword is encountered in the org schema, the target (person)
schema is found already cached in the catalog.

.. literalinclude:: ../../examples/load_from_files_1.py

Note that, when using this approach, the schemas *must* be loaded in
``"$ref"`` dependency order.

Another way is to set up a base URI-to-directory mapping on the catalog.
In this case, when the ``"$ref"`` keyword is encountered in the org schema,
the catalog knows where to find the person schema on disk, and loads it on
the fly.

.. literalinclude:: ../../examples/load_from_files_2.py

Finally, yet another way is again to set up a base URI-to-directory mapping
on the catalog, but this time we retrieve our primary schema from the catalog
rather than loading it explicitly.

.. literalinclude:: ../../examples/load_from_files_3.py

This last approach is well-suited to schema re-use, in which JSON document
evaluations are done independently with knowledge only of a schema's URI.
The schema is loaded and compiled the first time it is retrieved; thereafter,
it is simply read from the cache.
