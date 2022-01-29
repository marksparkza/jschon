API Reference
=============
The following classes may be imported directly from the top-level
:mod:`jschon` package:

* :class:`~jschon.catalog.Catalog`
* :class:`~jschon.exceptions.CatalogError`
* :class:`~jschon.json.JSON`
* :class:`~jschon.jsonpatch.JSONPatch`
* :class:`~jschon.exceptions.JSONPatchError`
* :class:`~jschon.jsonpatch.JSONPatchOperation`
* :class:`~jschon.jsonpointer.JSONPointer`
* :class:`~jschon.exceptions.JSONPointerError`
* :class:`~jschon.jsonpointer.RelativeJSONPointer`
* :class:`~jschon.exceptions.RelativeJSONPointerError`
* :class:`~jschon.jsonschema.JSONSchema`
* :class:`~jschon.exceptions.JSONSchemaError`
* :class:`~jschon.catalog.LocalSource`
* :class:`~jschon.catalog.RemoteSource`
* :class:`~jschon.uri.URI`
* :class:`~jschon.exceptions.URIError`

The package additionally defines the catalog initialization function:

.. autofunction:: jschon.create_catalog

.. toctree::
    :caption: Module Reference
    :glob:

    reference/*
