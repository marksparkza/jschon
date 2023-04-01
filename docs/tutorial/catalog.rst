The Catalog
===========
The role of the :class:`~jschon.catalog.Catalog` in jschon is twofold:

#. It acts as a schema cache, enabling schemas and subschemas to be indexed,
   re-used, and cross-referenced by URI -- allowing for the definition of multiple,
   cooperative schemas that work together to evaluate :class:`~jschon.json.JSON`
   documents.
#. It provides the infrastructure required for constructing
   :class:`~jschon.jsonschema.JSONSchema` objects. This can include meta-schemas,
   vocabularies and keyword implementations, format validators, and URI-to-directory
   mappings enabling URI-identified schemas to be located on disk.

A :class:`~jschon.catalog.Catalog` object is typically created and configured
at startup:

>>> from jschon import create_catalog
>>> catalog = create_catalog('2020-12')

The :func:`~jschon.create_catalog` function accepts a variable argument list
indicating which versions of the JSON Schema vocabularies to support. For example,
the following initialization call will enable your application to work with both
2019-09 and 2020-12 schemas:

>>> catalog = create_catalog('2019-09', '2020-12')

If your application requires distinct :class:`~jschon.catalog.Catalog`
instances with different configurations, then your setup might look something
like this:

>>> catalog_1 = create_catalog('2019-09', name='Catalog 1')
>>> catalog_2 = create_catalog('2020-12', name='Catalog 2')

The relevant :class:`~jschon.catalog.Catalog` instance - or name - can be
specified when creating new :class:`~jschon.jsonschema.JSONSchema` objects:

>>> from jschon import JSONSchema
>>> schema_1 = JSONSchema({"type": "object", ...}, catalog=catalog_1)
>>> schema_2 = JSONSchema.loadf('/path/to/schema.json', catalog='Catalog 2')

.. _catalog-reference-loading:

Reference loading
-----------------
Schema references can be resolved to files on disk, by configuring
a local directory source for a given base URI:

>>> from jschon import create_catalog, LocalSource, URI
>>> catalog = create_catalog('2020-12')
>>> catalog.add_uri_source(
...     URI("https://example.com/schemas/"),
...     LocalSource('/path/to/schemas/', suffix='.json')
... )

Now, the ``"$ref"`` in the following schema resolves to the local file
``/path/to/schemas/my/schema.json``::

    {
        "$ref": "https://example.com/schemas/my/schema",
        "$schema": "https://json-schema.org/draft/2020-12/schema"
    }

We can also retrieve :class:`~jschon.jsonschema.JSONSchema` objects by URI
directly from the catalog:

>>> my_schema = catalog.get_schema(URI("https://example.com/schemas/my/schema"))

See :doc:`../examples/file_based_schemas` for further examples of loading
schemas from disk.

Format validation
-----------------
By default, formats are not validated in jschon. Any occurrence of the ``format``
keyword simply produces an annotation consisting of the keyword's value, called
the *format attribute*.

Format validators can be registered using the :func:`~jschon.vocabulary.format.format_validator`
decorator. Format attributes must, however, be explicitly enabled for validation
in the catalog, in order to use any registered format validator. This can be done
using :meth:`~jschon.catalog.Catalog.enable_formats`.

For a working example, see :doc:`../examples/format_validation`.
