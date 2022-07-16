JSON
====
The :class:`~jschon.json.JSON` class is an implementation of the JSON data model.
It is used to represent a JSON document that may be evaluated by a JSON schema.
The :class:`~jschon.jsonschema.JSONSchema` class is itself a subclass of
:class:`~jschon.json.JSON`.

A :class:`~jschon.json.JSON` instance may be constructed from any JSON-compatible
Python object. Let's take a look at a few simple examples, printing the JSON type
of each. We begin by importing the :class:`~jschon.json.JSON` class:

>>> from jschon import JSON

>>> JSON("Hello, World!").type
'string'

>>> JSON(3.14159).type
'number'

>>> JSON(None).type
'null'

>>> JSON(("a", "b", "c")).type
'array'

Instances with the JSON types ``"array"`` and ``"object"`` are constructed
recursively. Here we create an array and an object:

>>> arr = JSON([1, 2, 3])
>>> obj = JSON({"foo": True, "bar": False})

Nested :class:`~jschon.json.JSON` instances may be accessed using square-bracket
notation:

>>> arr[1]
JSON(2)

>>> obj["foo"]
JSON(True)

:class:`~jschon.json.JSON` implements the :class:`Sequence` and :class:`Mapping`
interfaces for instances with the JSON types ``"array"`` and ``"object"``, respectively:

>>> [item for item in arr]
[JSON(1), JSON(2), JSON(3)]

>>> {key: val for key, val in obj.items()}
{'foo': JSON(True), 'bar': JSON(False)}

:class:`~jschon.json.JSON` instances have several attributes, in addition to the
:attr:`~jschon.json.JSON.type` attribute seen above. These can be useful when
working with complex JSON structures. Consider the following example:

>>> document = JSON({
...     "1a": {
...         "2a": "foo",
...         "2b": "bar"
...     },
...     "1b": [
...         {"3a": "baz"},
...         {"3b": "quux"}
...     ]
... })

A leaf node's :attr:`~jschon.json.JSON.data` attribute holds the value from which
it was constructed:

>>> document["1a"]["2a"].data
'foo'

The :attr:`~jschon.json.JSON.path` property returns a :class:`~jschon.jsonpointer.JSONPointer`
instance representing the path to the node from the document root:

>>> document["1b"][0]["3a"].path
JSONPointer('/1b/0/3a')

The :attr:`~jschon.json.JSON.parent` attribute gives the containing instance:

>>> document["1a"]["2b"].parent
JSON({'2a': 'foo', '2b': 'bar'})

The :attr:`~jschon.json.JSON.key` is the index of the node within its parent:

>>> document["1b"][1]["3b"].key
'3b'

Notice that, although an array item's sequential index is an integer, its
:attr:`~jschon.json.JSON.key` is a string. This makes it interoperable with
:class:`~jschon.jsonpointer.JSONPointer`:

>>> document["1b"][1].key
'1'

An ``"object"`` node's :attr:`~jschon.json.JSON.data` is a :obj:`dict[str, JSON]`:

>>> document["1a"].data
{'2a': JSON('foo'), '2b': JSON('bar')}

An ``"array"`` node's :attr:`~jschon.json.JSON.data` is a :obj:`list[JSON]`:

>>> document["1b"].data
[JSON({'3a': 'baz'}), JSON({'3b': 'quux'})]

The :attr:`~jschon.json.JSON.value` property returns the instance data as a
JSON-compatible Python object:

>>> document["1b"].value
[{'3a': 'baz'}, {'3b': 'quux'}]

Equality testing strictly follows the JSON data model. So, whereas the
following two Python lists compare equal:

>>> [False, True] == [0, 1]
True

The :class:`~jschon.json.JSON` equivalents are not equal, because the arrays'
items have different JSON types:

>>> JSON([False, True]) == JSON([0, 1])
False

A :class:`~jschon.json.JSON` instance may be compared with *any* Python object.
Internally, the non-:class:`~jschon.json.JSON` object is coerced to its :class:`~jschon.json.JSON`
equivalent before performing the comparison. Notice that tuples and lists are
considered structurally equivalent:

>>> (7, 11) == JSON([7, 11])
True

:class:`~jschon.json.JSON` also implements the ``<``, ``<=``, ``>=`` and ``>``
inequality operators, which may be used for numeric or string comparisons:

>>> JSON(3) < 3.01
True

jschon is not a JSON encoder/decoder. However, the :class:`~jschon.json.JSON`
class supports both serialization and deserialization of JSON documents, via the
Python standard library's :mod:`json` module.

Serializing a :class:`~jschon.json.JSON` instance is simply a matter of getting
its string representation:

>>> str(JSON({"xyz": (None, False, True)}))
'{"xyz": [null, false, true]}'

:class:`~jschon.json.JSON` instances can be deserialized from JSON files and JSON
strings using the :meth:`~jschon.json.JSON.loadf` and :meth:`~jschon.json.JSON.loads`
class methods, respectively:

>>> JSON.loadf('/path/to/file.json')
JSON(...)

>>> JSON.loads('{"1": "spam", "2": "eggs"}')
JSON({'1': 'spam', '2': 'eggs'})
