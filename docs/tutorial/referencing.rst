Advanced Referencing
====================
The vast majority of referencing scenarios can be handled as described in the
earlier parts of this tutorial.  However, consider the following
`schema bundles <https://www.ietf.org/archive/id/draft-bhutton-json-schema-01.html#name-bundling>`_:

>>> bundle1 = {
...     "$schema": "https://json-schema.org/draft/2020-12/schema",
...     "$id": "https://example.com/bundle1",
...     "$defs": {
...         "a": {
...             "$id": "https://example.com/source1/a",
...             "$ref": "../source2/b"
...         },
...         "b": {
...             "$id": "https://example.com/source1/b",
...             "type": "object"
...         }
...     }
... }
>>> bundle2 = {
...     "$schema": "https://json-schema.org/draft/2020-12/schema",
...     "$id": "https://example.com/bundle2",
...     "$defs": {
...         "a": {
...             "$id": "https://example.com/source2/a",
...             "$ref": "../source1/b"
...         },
...         "b": {
...             "$id": "https://example.com/source2/b",
...             "type": "array"
...         }
...     }
... }

There are several conditions here, including one not visible in the schemas
but plausible in many software environments:

* Mutual references (which the normal :class:`~jschon.jsonschema.JSONSchema`
  constructor call cannot handle)
* References only to URIs from subschema ``"$id"`` keywords (which the normal
  :class:`~jschon.catalog.LocalSource` or :class:`~jschon.catalog.RemoteSource`
  configurations cannot handle)
* Your code may need to handle schemas with contents that it does not know
  in advance.  (which prevents creative use of a :class:`~jschon.catalog.Source`
  subclass to map the subschema ``"$id"`` URIs to their top-level ``"$id"``
  in some way, assuming that the top-level ``"$id"`` would normally be findable)

Together, these conditions require an extra step to manage.

Deferring reference resolution
------------------------------
Reference resolution can be deferred using a :class:`~jschon.jsonschema.JSONSchema`
constructor parameter.  Deferred references **must** be resolved by calling
:meth:`~jschon.jsonschema.JSONSchema.resolve_references` prior to calling
:meth:`~jschon.jsonschema.JSONSchema.evaluate`:

>>> schema1 = JSONSchema(bundle1, resolve_references=False)
>>> schema2 = JSONSchema(bundle2)
>>> schema1.resolve_references()

We could have deferred reference resolution on both schemas, and then called
:meth:`~jschon.jsonschema.JSONSchema.resolve_references` on both of them.
But since ``schema1`` was already present in the catalog, the catalog was
already aware of the ``"$id"`` URIs needed to resolve references for ``schema2``.

Deferring through the Catalog
-----------------------------
If schemas such as our mutually referencing bundles are being loaded through
the :class:`~jschon.catalog.Catalog`, we need to configure the catalog to
defer resolution on all loaded schemas.  This can be done through
:func:`jschon.create_catalog`:

>>> from jschon import create_catalog, URI, LocalSource
>>> deferred_catalog = create_catalog('2020-12', name='deferred', resolve_references=False)
>>> deferred_catalog.add_uri_source(
...     URI('https://example.com/'),
...     LocalSource(base_dir='/opt/schemas/', suffix='.json'),
... )
>>> cat_bundle1 = deferred_catalog.get_schema(URI("https://example.com/bundle1"))
>>> cat_bundle2 = deferred_catalog.get_schema(URI("https://example.com/bundle2"))
>>> cat_bundle1.references_resolved
False
>>> cat_bundle2.references_resolved
False

We can use the :meth:`jschon.catalog.Catalog.resolve_references` convenience
method to resolve all references in all schemas in a particular schema cache.
We are using the default cache here so we do not need to pass a ``cacheid``:

>>> deferred_catalog.resolve_references()
>>> cat_bundle1.references_resolved
True
>>> cat_bundle2.references_resolved
True

You can access this method through a :class:`~jschon.jsonschema.JSONSchema`
instance, in which case it is a good idea to pass the ``cacheid`` unless you
are certain the schema is using the default cache:

>>> cat_bundle1.catalog.resolve_references(cacheid=cat_bundle1.cacheid)

Note that resolving references may cause additional schemas to be loaded.
:meth:`~jschon.catalog.Catalog.resolve_references` will resolve references
in newly loaded schemas as well, until either the entire schema cache is
fully resolved as it would have been without deferral, or an error occurs.

Metaschemas and deferred resolution
-----------------------------------
The :meth:`~jschon.catalog.Catalog.create_metaschema` method validates
the metaschema when it is created.  Therefore it also resolves references
in the metaschema cache just prior to calling
:meth:`~jschon.vocabulary.Metaschema.validate`.
