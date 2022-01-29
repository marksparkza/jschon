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
2019-09 and 2020-12 schemas:

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

Format validators
-----------------
jschon does not provide built-in support for validating JSON Schema
`formats <https://json-schema.org/draft/2020-12/json-schema-validation.html#rfc.section.7.3>`_.
By default, any occurrence of the ``"format"`` keyword in a schema simply passes,
with its value -- its *format attribute* -- collected as an annotation.

To validate a given format attribute, we can define a *format validator*.

The :meth:`~jschon.catalog.Catalog.add_format_validators` method accepts a
dictionary of :class:`~jschon.vocabulary.format.FormatValidator` objects indexed
by format attribute. A :class:`~jschon.vocabulary.format.FormatValidator`
is simply a callable that accepts a single argument -- the value to be validated --
and raises a :exc:`ValueError` if a supplied value is invalid.

For example, suppose that we'd like to validate that any occurrence of an IP address
or hostname in a JSON document conforms to the ``"ipv4"``, ``"ipv6"`` or ``"hostname"``
format. For the IP address formats, we can use the :class:`ipaddress.IPv*Address`
classes, available in the Python standard library, since their constructors raise
a :exc:`ValueError` for an invalid constructor argument. For the hostname format,
we'll define a validation function using a hostname `regex <https://stackoverflow.com/a/106223>`_.
Our catalog setup looks like this:

>>> import ipaddress
>>> import re
>>> from jschon import Catalog
...
>>> def validate_hostname(value):
...     hostname_regex = re.compile(r"^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$")
...     if not hostname_regex.match(value):
...         raise ValueError(f"'{value}' is not a valid hostname")
...
>>> catalog = create_catalog('2020-12')
>>> catalog.add_format_validators({
...     "ipv4": ipaddress.IPv4Address,
...     "ipv6": ipaddress.IPv6Address,
...     "hostname": validate_hostname,
... })

Now, we can define a schema that returns a validation failure for any JSON document
that contains incorrectly formatted IP addresses or hostnames. The following
simple example validates a single string instance:

>>> from jschon import JSONSchema
>>> schema = JSONSchema({
...     "$schema": "https://json-schema.org/draft/2020-12/schema",
...     "type": "string",
...     "anyOf": [
...         {"format": "ipv4"},
...         {"format": "ipv6"},
...         {"format": "hostname"}
...     ]
... })

For a complete working example, see :doc:`../examples/format_validation`.
