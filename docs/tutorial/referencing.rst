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

