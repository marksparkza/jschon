Catalogue
=========
The role of the :class:`~jschon.catalogue.Catalogue` in jschon is twofold:

#. It acts as a schema cache, enabling schemas and subschemas to be indexed,
   re-used, and cross-referenced by URI - allowing for the definition of multiple,
   cooperative schemas that work together to evaluate :class:`~jschon.json.JSON`
   documents.
#. It provides the infrastructure required for constructing
   :class:`~jschon.jsonschema.JSONSchema` objects. This includes metaschemas,
   vocabularies and keyword implementations, format validation functions, and
   base URI-to-directory mappings that enable URI-identified schemas to be
   located on disk.

A :class:`~jschon.catalogue.Catalogue` object is typically created once per
application, using the :func:`~jschon.create_catalogue` function:

>>> from jschon import create_catalogue
>>> create_catalogue('2020-12', default=True)

:func:`~jschon.create_catalogue` accepts a variable argument list indicating which
versions of the JSON Schema vocabulary to support. For example, the following
initialization call will enable our application to work with both 2019-09 and
2020-12 schemas:

>>> create_catalogue('2019-09', '2020-12', default=True)

The `default` parameter (which is ``False`` by default) indicates that the created
:class:`~jschon.catalogue.Catalogue` instance should be used by any new
:class:`~jschon.jsonschema.JSONSchema` objects that our application creates.
To be precise, setting `default` to ``True`` means that the `catalogue` parameter
of the :class:`~jschon.jsonschema.JSONSchema` constructor can be omitted, in which
case it implicitly takes the value of the default :class:`~jschon.catalogue.Catalogue`
instance.

If our application requires distinct :class:`~jschon.catalogue.Catalogue`
instances with different configurations, then our setup might look something
like this:

>>> cat201909 = create_catalogue('2019-09')
>>> cat202012 = create_catalogue('2020-12')

Then, when we create :class:`~jschon.jsonschema.JSONSchema` objects, we must
pass the relevant :class:`~jschon.catalogue.Catalogue` instance via the
`catalogue` parameter. For example:

>>> schema201909 = JSONSchema({"type": "object", ...}, catalogue=cat201909)
>>> schema202012 = JSONSchema.loadf('/path/to/schema.json', catalogue=cat202012)

.. _catalogue-uri-directory-mapping:

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
then we can configure a base URI-to-directory mapping on the catalogue:

>>> from jschon import create_catalogue
>>> catalogue = create_catalogue('2020-12', default=True)
>>> catalogue.add_directory(URI("https://example.com/schema/"), '/path/to/schema/')

Now, we can retrieve :class:`~jschon.jsonschema.JSONSchema` objects with the
:meth:`~jschon.catalogue.Catalogue.get_schema` method:

>>> foo1_schema = catalogue.get_schema(URI("https://example.com/schema/v1/foo.json"))

The ``".json"`` part of the filename may be omitted:

>>> bar2_schema = catalogue.get_schema(URI("https://example.com/schema/v2/bar"))

Format validators
-----------------
jschon does not provide built-in support for validating the ``"format"`` keyword.
By default, any occurrence of ``"format"`` in a schema passes, with its value -
also known as its *format attribute* - simply collected as an annotation.
However, we can enable validation for any format attribute - whether a format
`defined <https://json-schema.org/draft/2020-12/json-schema-validation.html#rfc.section.7.3>`_
in the JSON Schema specification, or a custom format - by associating it with
a *format validator*.

The :meth:`~jschon.catalogue.Catalogue.add_format_validators` method accepts a
dictionary of :class:`~jschon.vocabulary.format.FormatValidator` objects indexed
by format attribute. A :class:`~jschon.vocabulary.format.FormatValidator`
is simply a callable that accepts a single argument - the value to be validated -
and raises a :exc:`ValueError` if a supplied value is invalid.

For example, suppose that we'd like to validate that any occurrence of an IP address
or hostname in a JSON document conforms to the ``"ipv4"``, ``"ipv6"`` or ``"hostname"``
format. For the IP address formats, we can use the :class:`ipaddress.IPv*Address`
classes, available in the Python standard library, since their constructors raise
a :exc:`ValueError` for an invalid constructor argument. For the hostname format,
we'll define a validation function using a hostname `regex <https://stackoverflow.com/a/106223>`_.
Our catalogue setup looks like this:

>>> import ipaddress
>>> import re
>>> from jschon import create_catalogue
...
>>> def validate_hostname(value):
...     hostname_regex = re.compile(r"^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$")
...     if not hostname_regex.match(value):
...         raise ValueError(f"'{value}' is not a valid hostname")
...
>>> catalogue = create_catalogue('2020-12', default=True)
>>> catalogue.add_format_validators({
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
