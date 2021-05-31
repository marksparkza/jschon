JSON Schema
===========
On this page, we'll take a look at the classes involved in setting up
JSON schemas and evaluating JSON documents.

We'll require the following classes:

>>> from jschon import Catalogue, JSON, JSONSchema, URI

The catalogue
-------------
The :class:`~jschon.catalogue.Catalogue` may be thought of as the operational
infrastructure of jschon. It provides a schema cache, enabling schemas and
subschemas to reference each other. It supports base URI-to-directory mappings,
so that URI-identified schemas - including the all-important JSON Schema
metaschemas - can be loaded from disk. And it supports the plugging in of
``"format"`` keyword validators.

A :class:`~jschon.catalogue.Catalogue` may be initialized with the metaschema(s)
for any number of supported versions of the JSON Schema specification. For example,
to prepare a :class:`~jschon.catalogue.Catalogue` for use with both 2019-09 and
2020-12 schemas:

>>> catalogue = Catalogue('2019-09', '2020-12')

In the following examples (and in many use cases), a single :class:`~jschon.catalogue.Catalogue`
instance will suffice. We can create a *default catalogue* - which will then be
used implicitly by :class:`~jschon.jsonschema.JSONSchema` unless otherwise
instructed - and here we'll initialize it with just the JSON Schema 2020-12
metaschema:

>>> catalogue = Catalogue.create_default_catalogue('2020-12')

A basic example
---------------
First, let's consider a very basic example. Here is a schema that simply ensures
that a JSON value represents an integer:

>>> int_schema = JSONSchema({
...     "type": "integer"
... })
jschon.exceptions.JSONSchemaError: The schema's metaschema URI has not been set

Oops! As you can see, without specifying a *metaschema*, jschon won't know how to
interpret ``"type"`` or any other keyword. The metaschema URI may be parameterized,
or it may be provided using the ``"$schema"`` keyword:

>>> int_schema = JSONSchema({
...     "type": "integer"
... }, metaschema_uri=URI("https://json-schema.org/draft/2020-12/schema"))

>>> int_schema = JSONSchema({
...     "type": "integer",
...     "$schema": "https://json-schema.org/draft/2020-12/schema"
... })

If both are provided, the ``"$schema"`` keyword takes precedence:

>>> int_schema = JSONSchema({
...     "type": "integer",
...     "$schema": "https://json-schema.org/draft/2020-12/schema"
... }, metaschema_uri=URI("https://json-schema.org/draft/2019-09/schema"))

>>> int_schema.metaschema_uri
URI('https://json-schema.org/draft/2020-12/schema')

An identifying URI is automatically generated for every root schema:

>>> int_schema.uri
URI('urn:uuid:f3adf4a3-c03d-4f30-9072-5bc7b8e9f078')

The schema URI is used as the key for caching the schema in the catalogue, and
is required for resolving references to itself and to any subschemas it may
contain. If the schema is intended to be referenced from other schemas in the
catalogue, then a URI should be provided explicitly. This may either be passed via
the `uri` parameter to the constructor, or declared in the schema document itself
using the ``"$id"`` keyword. If both are provided, the ``"$id"`` keyword takes
precedence:

>>> int_schema = JSONSchema({
...     "type": "integer",
...     "$schema": "https://json-schema.org/draft/2020-12/schema",
...     "$id": "https://example.com/the-real-id"
... }, uri="https://example.com/not-the-real-id")

>>> int_schema.uri
URI('https://example.com/the-real-id')

Format validators
-----------------
jschon does not provide built-in support for ``"format"`` keyword validation.
By default, any occurrence of ``"format"`` in a schema passes, with its value
simply collected as an annotation. However, jschon allows you to plug in
validators for *any* format, whether one of the
`defined formats <https://json-schema.org/draft/2020-12/json-schema-validation.html#rfc.section.7.3>`_
as per the JSON Schema spec, or a custom format known only to your organization.

To support the schema that we'll be creating in the next section, let's set up
validators for the ``"ipv4"``, ``"ipv6"`` and ``"hostname"`` formats. The
:meth:`~jschon.catalogue.Catalogue.add_format_validators` method accepts a
dictionary of :class:`~jschon.vocabulary.format.FormatValidator` objects indexed
by *format attribute*. A :class:`~jschon.vocabulary.format.FormatValidator`
is simply a callable that accepts a single argument - the value to be validated -
and raises a :exc:`ValueError` if a supplied value is invalid.

For the IP address formats, we can use the :class:`ipaddress.IPv*Address`
constructors, available in the Python standard library. For the hostname format,
we'll define a validation function using a hostname `regex <https://stackoverflow.com/a/106223>`_:

>>> import ipaddress
>>> import re
...
>>> def validate_hostname(value):
...     hostname_regex = re.compile(r"^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$")
...     if not hostname_regex.match(value):
...         raise ValueError(f"'{value}' is not a valid hostname")
...
>>> catalogue.add_format_validators({
...     "ipv4": ipaddress.IPv4Address,
...     "ipv6": ipaddress.IPv6Address,
...     "hostname": validate_hostname,
... })

A more realistic example
------------------------
The objective for this example will be to ensure that a JSON document consists
of an array of host records, where each record has an IP address and a hostname.
We can create the schema, and validate it against its metaschema, in one go:

>>> hosts_schema = JSONSchema({
...     "$schema": "https://json-schema.org/draft/2020-12/schema",
...     "$id": "https://example.com/hosts-schema",
...     "type": "array",
...     "items": {
...         "type": "object",
...         "properties": {
...             "ipaddress": {
...                 "type": "string",
...                 "oneOf": [
...                     {"format": "ipv4"},
...                     {"format": "ipv6"}
...                 ]
...             },
...             "hostname": {
...                 "type": "string",
...                 "format": "hostname"
...             }
...         },
...         "required": ["ipaddress", "hostname"]
...     }
... }).validate()

Before we move on to evaluating JSON documents with this schema, let's take a
quick peek under the hood.

:class:`~jschon.jsonschema.JSONSchema` is a specialization of the :class:`~jschon.json.JSON`
class. As with any ``"object"``-type :class:`~jschon.json.JSON` instance, the schema is
constructed recursively, with nested schemas themselves being :class:`~jschon.jsonschema.JSONSchema`
instances:

>>> hosts_schema["items"]["properties"]["ipaddress"]
JSONSchema({'type': 'string', 'oneOf': [{'format': 'ipv4'}, {'format': 'ipv6'}]})

Descending further down the schema tree, we see that the entire schema may be
composed of a complex hierarchy of :class:`~jschon.json.JSON` and :class:`~jschon.jsonschema.JSONSchema`
nodes:

>>> hosts_schema["items"]["properties"]["ipaddress"]["oneOf"]
JSON([{'format': 'ipv4'}, {'format': 'ipv6'}])

>>> hosts_schema["items"]["properties"]["ipaddress"]["oneOf"][0]
JSONSchema({'format': 'ipv4'})

Although a schema's structure is fully described by the :class:`~jschon.json.JSON`
class, its behaviour depends on its :attr:`~jschon.jsonschema.JSONSchema.keywords`.
At the top level, we have:

>>> hosts_schema.keywords
{'$id': <jschon.vocabulary.core.IdKeyword object at 0x7f21fcee8430>, '$schema': <jschon.vocabulary.core.SchemaKeyword object at 0x7f21fcee8d90>, 'type': <jschon.vocabulary.validation.TypeKeyword object at 0x7f21fcee89a0>, 'items': <jschon.vocabulary.applicator.ItemsKeyword object at 0x7f21fcee8f40>}

While in a deeply nested schema:

>>> hosts_schema["items"]["properties"]["ipaddress"]["oneOf"][0].keywords
{'format': <jschon.vocabulary.format.FormatKeyword object at 0x7f21fcec87f0>}

Now, let's create two JSON host record arrays, which we'll evaluate using our
hosts schema:

>>> valid_host_records = JSON([
...     {"ipaddress": "127.0.0.1", "hostname": "localhost"},
...     {"ipaddress": "10.0.0.8", "hostname": "server.local"},
... ])

>>> invalid_host_records = JSON([
...     {"ipaddress": "127.0.0.1", "hostname": "~localhost"},
...     {"ipaddress": "10.0.0", "hostname": "server.local"},
... ])

To quickly check the validity of these arrays, we can simply read the
:attr:`~jschon.jsonschema.Scope.valid` property of the result:

>>> hosts_schema.evaluate(valid_host_records).valid
True

>>> hosts_schema.evaluate(invalid_host_records).valid
False

Alternatively, we can use the :meth:`~jschon.jsonschema.Scope.output` method to
generate a JSON-compatible dictionary formatted in accordance with one of the
`output formats <https://json-schema.org/draft/2020-12/json-schema-core.html#output>`_
described by the JSON Schema core specification [#]_:

>>> hosts_schema.evaluate(valid_host_records).output('flag')
{'valid': True}

>>> hosts_schema.evaluate(invalid_host_records).output('basic')
{'valid': False, 'errors': [{'instanceLocation': '', 'keywordLocation': '', 'absoluteKeywordLocation': 'https://example.com/hosts-schema#', 'error': 'The instance failed validation against the schema'}, {'instanceLocation': '/0', 'keywordLocation': '/items', 'absoluteKeywordLocation': 'https://example.com/hosts-schema#/items', 'error': 'The instance failed validation against the schema'}, {'instanceLocation': '/1', 'keywordLocation': '/items', 'absoluteKeywordLocation': 'https://example.com/hosts-schema#/items', 'error': 'The instance failed validation against the schema'}, {'instanceLocation': '/0', 'keywordLocation': '/items/properties', 'absoluteKeywordLocation': 'https://example.com/hosts-schema#/items/properties', 'error': "Properties ['hostname'] are invalid"}, {'instanceLocation': '/0/hostname', 'keywordLocation': '/items/properties/hostname', 'absoluteKeywordLocation': 'https://example.com/hosts-schema#/items/properties/hostname', 'error': 'The instance failed validation against the schema'}, {'instanceLocation': '/0/hostname', 'keywordLocation': '/items/properties/hostname/format', 'absoluteKeywordLocation': 'https://example.com/hosts-schema#/items/properties/hostname/format', 'error': 'The instance is invalid against the "hostname" format: \'~localhost\' is not a valid hostname'}, {'instanceLocation': '/1', 'keywordLocation': '/items/properties', 'absoluteKeywordLocation': 'https://example.com/hosts-schema#/items/properties', 'error': "Properties ['ipaddress'] are invalid"}, {'instanceLocation': '/1/ipaddress', 'keywordLocation': '/items/properties/ipaddress', 'absoluteKeywordLocation': 'https://example.com/hosts-schema#/items/properties/ipaddress', 'error': 'The instance failed validation against the schema'}, {'instanceLocation': '/1/ipaddress', 'keywordLocation': '/items/properties/ipaddress/oneOf', 'absoluteKeywordLocation': 'https://example.com/hosts-schema#/items/properties/ipaddress/oneOf', 'error': 'The instance must be valid against exactly one subschema; it is valid against [] and invalid against [0, 1]'}, {'instanceLocation': '/1/ipaddress', 'keywordLocation': '/items/properties/ipaddress/oneOf/0', 'absoluteKeywordLocation': 'https://example.com/hosts-schema#/items/properties/ipaddress/oneOf/0', 'error': 'The instance failed validation against the schema'}, {'instanceLocation': '/1/ipaddress', 'keywordLocation': '/items/properties/ipaddress/oneOf/0/format', 'absoluteKeywordLocation': 'https://example.com/hosts-schema#/items/properties/ipaddress/oneOf/0/format', 'error': 'The instance is invalid against the "ipv4" format: Expected 4 octets in \'10.0.0\''}, {'instanceLocation': '/1/ipaddress', 'keywordLocation': '/items/properties/ipaddress/oneOf/1', 'absoluteKeywordLocation': 'https://example.com/hosts-schema#/items/properties/ipaddress/oneOf/1', 'error': 'The instance failed validation against the schema'}, {'instanceLocation': '/1/ipaddress', 'keywordLocation': '/items/properties/ipaddress/oneOf/1/format', 'absoluteKeywordLocation': 'https://example.com/hosts-schema#/items/properties/ipaddress/oneOf/1/format', 'error': 'The instance is invalid against the "ipv6" format: At least 3 parts expected in \'10.0.0\''}]}

The scope tree
--------------
What exactly is the object that the :meth:`~jschon.jsonschema.JSONSchema.evaluate`
method returns?

>>> hosts_schema.evaluate(valid_host_records)
<jschon.jsonschema.Scope object at 0x7f9ff98d9a00>

:class:`~jschon.jsonschema.Scope` is a tree whose structure reflects the dynamic
evaluation path that was taken through a schema (and any referenced schemas) while
evaluating a JSON instance. Each node in the :class:`~jschon.jsonschema.Scope`
tree holds the results of evaluating an instance node against a schema node - or,
to be precise, the results of evaluating an instance *subtree* against a schema
*subtree*. So, the root node of the :class:`~jschon.jsonschema.Scope` tree represents
the result of evaluating the entire instance against the entire schema.

Applications will typically only need to read the :attr:`~jschon.jsonschema.Scope.valid`
property or use the :meth:`~jschon.jsonschema.Scope.output` method at the root of
a :class:`~jschon.jsonschema.Scope` tree, to see the result of evaluating a JSON
instance. But for custom keyword development, it will be important to understand
how the :class:`~jschon.jsonschema.Scope` class works - and this will be explained
in the next guide (to do!).

.. [#] jschon currently supports only the ``'flag'`` and ``'basic'`` output formats.
