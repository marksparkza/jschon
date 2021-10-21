Catalog
=======
The role of the :class:`~jschon.catalog.Catalog` in jschon is twofold:

#. It acts as a schema cache, enabling schemas and subschemas to be indexed,
   re-used, and cross-referenced by URI -- allowing for the definition of multiple,
   cooperative schemas that work together to evaluate :class:`~jschon.json.JSON`
   documents.
#. It provides the infrastructure required for constructing
   :class:`~jschon.jsonschema.JSONSchema` objects. This includes metaschemas,
   vocabularies and keyword implementations, format validation functions, and
   base URI-to-directory mappings that enable URI-identified schemas to be
   located on disk.

A :class:`~jschon.catalog.Catalog` object is typically created once per
application, using the :func:`~jschon.create_catalog` function:

>>> from jschon import create_catalog
>>> create_catalog('2020-12')

:func:`~jschon.create_catalog` accepts a variable argument list indicating which
versions of the JSON Schema vocabulary to support. For example, the following
initialization call will enable our application to work with both 2019-09 and
2020-12 schemas:

>>> create_catalog('2019-09', '2020-12')

If our application requires distinct :class:`~jschon.catalog.Catalog`
instances with different configurations, then our setup might look something
like this:

>>> cat201909 = create_catalog('2019-09', default=False)
>>> cat202012 = create_catalog('2020-12', default=False)

When `default` is set to ``False``, then the relevant :class:`~jschon.catalog.Catalog`
instance must be specified when creating new :class:`~jschon.jsonschema.JSONSchema`
objects:

>>> schema201909 = JSONSchema({"type": "object", ...}, catalog=cat201909)
>>> schema202012 = JSONSchema.loadf('/path/to/schema.json', catalog=cat202012)

.. _catalog-uri-directory-mapping:

URI-to-directory mappings
-------------------------
Suppose that we have a number of schemas stored locally in JSON text files,
in a directory hierarchy such as the following::

    /path/to/schema/
        v1/
            foo.json
            bar.json
        v2/
            foo.json
            bar.json

If our schemas share a common base URI, say ``"https://example.com/schema/"``,
then we can configure a base URI-to-directory mapping on the catalog:

>>> from jschon import create_catalog
>>> catalog = create_catalog('2020-12')
>>> catalog.add_directory(URI("https://example.com/schema/"), '/path/to/schema/')

Now, we can retrieve :class:`~jschon.jsonschema.JSONSchema` objects with the
:meth:`~jschon.catalog.Catalog.get_schema` method:

>>> foo1_schema = catalog.get_schema(URI("https://example.com/schema/v1/foo.json"))

The ``".json"`` part of the filename may be omitted:

>>> bar2_schema = catalog.get_schema(URI("https://example.com/schema/v2/bar"))

Further examples demonstrating the usage of URI-to-directory mappings are
given in :doc:`../examples/file_based_schemas`.

Format validators
-----------------
jschon does not provide built-in support for validating any
`formats <https://json-schema.org/draft/2020-12/json-schema-validation.html#rfc.section.7.3>`_
defined in the JSON Schema specification. By default, any occurrence of the
``"format"`` keyword in a schema passes, with its value -- its *format attribute* --
simply collected as an annotation. However, we can assign *format validators*
to any format attributes -- including custom format attributes -- that we wish
to validate.

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
>>> from jschon import create_catalog
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
