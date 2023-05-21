JSON Schema
===========
The :class:`~jschon.jsonschema.JSONSchema` class represents a *compiled* JSON
schema document. Once instantiated, a :class:`~jschon.jsonschema.JSONSchema`
object contains all the structural information and executable code it requires
for evaluating :class:`~jschon.json.JSON` instances, and it may be re-used any
number of times for such evaluation. References to other schemas are resolved
during construction, guaranteeing further that any referenced schemas are also
fully loaded, compiled and ready for use and re-use.

:class:`~jschon.jsonschema.JSONSchema` is a specialization of the :class:`~jschon.json.JSON`
class, and provides all the capabilities of its ancestor, as described in the
:doc:`json` guide. Only its JSON type is limited -- to one of ``"object"`` and
``"boolean"`` -- in accordance with the JSON Schema specification. As we might
expect, :class:`~jschon.jsonschema.JSONSchema` introduces several new properties
and behaviours, which we'll explore in the following sections.

Initializing the catalog
------------------------
Before we can begin creating and working with schemas, we must set up a catalog.
For the examples shown on the remainder of this page, we'll use the following:

>>> from jschon import create_catalog
>>> catalog = create_catalog('2020-12')

Creating a schema
-----------------
There are several different ways to instantiate a :class:`~jschon.jsonschema.JSONSchema`:

* Create it directly from a schema-compatible Python object such as a
  :class:`dict` or a :class:`bool`.
* Deserialize it from a JSON file or a JSON string using the
  :meth:`~jschon.json.JSON.loadf` or :meth:`~jschon.json.JSON.loads`
  class method.
* Retrieve it from the :class:`~jschon.catalog.Catalog` by providing
  a schema URI, which maps to a schema file on disk.

But first, let's import the classes that we'll be using:

>>> from jschon import JSONSchema, URI

Creating a schema from a Python object
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
A :class:`~jschon.jsonschema.JSONSchema` object can be created directly from
any schema-compatible Python object, such as a :class:`dict` or a :class:`bool`.

For boolean schemas and empty schemas, it's as simple as:

>>> true_schema = JSONSchema(True)
>>> false_schema = JSONSchema(False)
>>> empty_schema = JSONSchema({})

Creating a :class:`~jschon.jsonschema.JSONSchema` object from any non-empty
:class:`Mapping`, however, requires that we specify a meta-schema. Here's a
very basic example of a schema that simply ensures that a JSON value represents
an integer:

>>> int_schema = JSONSchema({
...     "type": "integer"
... }, metaschema_uri=URI("https://json-schema.org/draft/2020-12/schema"))

The `metaschema_uri` parameter resolves to a :class:`~jschon.vocabulary.Metaschema`
object, which provides the new :class:`~jschon.jsonschema.JSONSchema` instance
with :class:`~jschon.vocabulary.Keyword` classes for each of its keywords. The
meta-schema URI may be parameterized, as above, or it may be provided using the
``"$schema"`` keyword:

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

The schema URI is used as the key for caching the schema in the catalog, and
is required for resolving references to itself and to any subschemas it may
contain. If the schema is intended to be referenced from other schemas in the
catalog, then a URI should be provided explicitly. This may either be passed via
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

Deserializing a schema from a JSON text document
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Suppose that we have a string containing a JSON schema, such as the following,
which validates a numeric JSON value:

>>> schema_text = '''{
...     "$schema": "https://json-schema.org/draft/2020-12/schema",
...     "$id": "https://example.com/num-schema",
...     "type": "number"
... }'''

We can deserialize this JSON text into a new :class:`~jschon.jsonschema.JSONSchema`
instance using the :meth:`~jschon.json.JSON.loads` class method:

>>> num_schema = JSONSchema.loads(schema_text)

If the schema is stored in a JSON text file, we can deserialize directly from
the file by providing the file path to the :meth:`~jschon.json.JSON.loadf` class
method:

>>> num_schema = JSONSchema.loadf('/path/to/num-schema.json')

The argument to :meth:`~jschon.json.JSON.loadf` may be a plain :class:`str`, or
any :class:`PathLike` object; for example:

>>> import pathlib
>>> schema_path = pathlib.Path(__file__).parent / 'num-schema.json'
>>> num_schema = JSONSchema.loadf(schema_path)

Both :meth:`~jschon.json.JSON.loads` and :meth:`~jschon.json.JSON.loadf` accept
keyword arguments that are passed through to the :class:`~jschon.jsonschema.JSONSchema`
constructor, in case we need to parameterize the meta-schema URI, the schema URI, or
any other :class:`~jschon.jsonschema.JSONSchema` constructor argument:

>>> num_schema = JSONSchema.loads(schema_text, metaschema_uri=URI("https://json-schema.org/draft/2020-12/schema"))

>>> num_schema = JSONSchema.loadf(schema_path, uri=URI("https://example.com/num-schema"))

Retrieving a schema from the catalog
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Finally, a :class:`~jschon.jsonschema.JSONSchema` object may be instantiated implicitly,
when retrieving it by URI from the :class:`~jschon.catalog.Catalog`. If the schema is not
already cached, it is loaded from disk and compiled on the fly. This approach requires
the catalog to be configured with an appropriate base URI-to-directory mapping. For
more information, see :ref:`catalog-reference-loading`.
