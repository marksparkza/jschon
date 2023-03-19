The Catalog
===========
The role of the :class:`~jschon.catalog.Catalog` in jschon is twofold:

#. It acts as a schema cache, enabling schemas and subschemas to be indexed,
   re-used, and cross-referenced by URI -- allowing for the definition of multiple,
   cooperative schemas that work together to evaluate :class:`~jschon.json.JSON`
   documents.
#. It provides the infrastructure required for constructing
   :class:`~jschon.jsonschema.JSONSchema` objects. This can include metaschemas,
   vocabularies and keyword implementations, format validators, and URI-to-directory
   mappings enabling URI-identified schemas to be located on disk.

A :class:`~jschon.catalog.Catalog` object is typically created and configured
at startup:

>>> from jschon import create_catalog
>>> catalog = create_catalog('2020-12')

The :func:`~jschon.create_catalog` function accepts a variable argument list
indicating which versions of the JSON Schema vocabulary to support. For example,
the following initialization call will enable our application to work with both
2019-09 and 2020-12 schemas by pre-loading the metaschemas for both versions:

>>> catalog = create_catalog('2019-09', '2020-12')

If our application requires distinct :class:`~jschon.catalog.Catalog`
instances with different configurations, then our setup might look something
like this:

>>> catalog_1 = create_catalog('2019-09', name='Catalog 1')
>>> catalog_2 = create_catalog('2020-12', name='Catalog 2')

The relevant :class:`~jschon.catalog.Catalog` instance - or name - can be
specified when creating new :class:`~jschon.jsonschema.JSONSchema` objects:

>>> from jschon import JSONSchema
>>> schema_1 = JSONSchema({"type": "object", ...}, catalog=catalog_1)
>>> schema_2 = JSONSchema.loadf('/path/to/schema.json', catalog='Catalog 2')

The :class:`~jschon.jsonschema.JSONSchema` constructor automatically uses
the unnamed default catalog unless a different one is provided.

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
directly from the catalog, using the same method that the catalog uses
to resolve references:

>>> my_schema = catalog.get_schema(URI("https://example.com/schemas/my/schema"))

See :doc:`../examples/file_based_schemas` for further examples of loading
schemas from disk, and :mod:`jschon.catalog` for documentation on other
possible sources.

Schema and metaschema caching
-----------------------------
Whether a :class:`~jschon.jsonschema.JSONSchema` is instantiated directly or
through :meth:`~jschon.catalog.Catalog.get_schema`, it is cached within its
associated :class:`~jschon.catalog.Catalog` instance.

The :class:`~jschon.catalog.Catalog` supports multiple caches, each using
its own ``cacheid``, which can be provided as a parameter to the
:class:`~jschon.jsonschema.JSONSchema` constructor and to methods
such as :meth:`~jschon.jsonschema.Catalog.get_schema`.

>>> from jschon import create_catalog, JSONSchema, URI, CatalogError
>>> catalog = create_catalog('2020-12')
>>> schema_data = {
...     "$schema": "https://json-schema.org/draft/2020-12/schema",
...     "$id": "https://example.com/foo",
...     "type": "object"
... }
>>> schema_uri = URI(schema_data['$id'])
>>> schema = JSONSchema(schema_data, cacheid='other')
>>> cached = catalog.get_schema(URI(schema_data['$id']), cacheid='other')
>>> cached is schema
True

Caches are isolated from each other, and references are only resolved within
the same cache.  However, the same schema data can be instantiated as
separate objects in different caches:

>>> try:
...     catalog.get_schema(schema_uri)
... except CatalogError as e:
...     print(f'{type(e).__name__}: {e}')
CatalogError: A source is not available for "https://example.com/foo"
>>> schema_in_default_cache = JSONSchema(schema_data)
>>> cached_from_default = catalog.get_schema(schema_uri)
>>> cached_from_default is schema_in_default_cache
True
>>> cached_from_default is cached
False

:class:`~jschon.vocabulary.Metaschema` instances are automatically cached
separately from regular :class:`~jschon.jsonschema.JSONSchema` instances.
This special metaschema cache is used by the
:meth:`~jschon.jsonschema.JSONSchema.validate` method.  Catalogs constructed
by the :func:`~jschon.create_metaschema` function have their metaschema cache
automatically populated by the standard metaschemas for the JSON Schema
version(s) passed to that function.

>>> catalog_2019 = create_catalog('2019-09', name='2019-09 Catalog')
>>> JSONSchema(
...     {"$schema": "https://json-schema.org/draft/2019-09/schema"},
...     catalog=catalog_2019
... ).validate().valid
True
>>> try:
...     JSONSchema(
...         {"$schema": "https://json-schema.org/draft/2020-12/schema"},
...         catalog=catalog_2019
...     ).validate().valid
... except CatalogError as e:
...     print(f'{type(e).__name__}: {e}')
CatalogError: A source is not available for "https://json-schema.org/draft/2020-12/schema"

Metaschemas can also be added using the
:meth:`~jschon.catalog.Catalog.create_metaschema` method.

The metaschema cache and the :class:`~jschon.catalog.Source` configurations
for a :class:`~jschon.catalog.Catalog` are shared across all of the regular
:class:`~jschon.jsonschema.JSONSchema` caches within that catalog.

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
