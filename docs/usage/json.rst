JSON
====
The :class:`JSON` class is an implementation of the JSON data model.
It is used to represent a JSON document that may be evaluated by a
JSON schema. The :class:`JSONSchema` class is itself a subclass of
:class:`JSON`.

A :class:`JSON` instance may be constructed from any JSON-compatible
Python object. Let's take a look at a few simple examples, printing
the JSON type of each. We begin by importing the :class:`JSON` class:

>>> from jschon import JSON

>>> JSON(None).type
'null'

>>> JSON(True).type
'boolean'

>>> JSON(3.14159).type
'number'

>>> JSON("Hello, World!").type
'string'

>>> JSON((1, 2, 3)).type
'array'

>>> JSON({"foo": True, "bar": False}).type
'object'

Instances with the JSON types "array" and "object" are constructed
recursively. Here we create an array and an object:

>>> arr = JSON([1, 2, 3])
>>> obj = JSON({"foo": True, "bar": False})

Nested :class:`JSON` instances may be accessed using square-bracket
notation:

>>> arr[1]
JSON(2)

>>> obj["foo"]
JSON(True)

:class:`JSON` implements the :class:`Sequence` and :class:`Mapping`
interfaces for instances with the JSON types "array" and "object",
respectively:

>>> [item for item in arr]
[JSON(1), JSON(2), JSON(3)]

>>> {key: val for key, val in obj.items()}
{'foo': JSON(True), 'bar': JSON(False)}

:class:`JSON` instances have several attributes, in addition to the
:attr:`type` attribute seen above. These can be useful when working
with complex JSON structures. Consider the following example:

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

A leaf node's :attr:`value` is the value from which it was constructed:

>>> document["1a"]["2a"].value
'foo'

The :attr:`parent` attribute gives the containing instance:

>>> document["1a"]["2b"].parent
JSON({'2a': 'foo', '2b': 'bar'})

The :attr:`path` property returns a :class:`JSONPointer` instance
representing the path to the node from the document root:

>>> document["1b"][0]["3a"].path
JSONPointer('/1b/0/3a')

The :attr:`key` is the index of the node within its parent:

>>> document["1b"][1]["3b"].key
'3b'

Notice that, although an array item's sequential index is an integer,
its :attr:`key` is a string. This makes it interoperable with
:class:`JSONPointer`:

>>> document["1b"][1].key
'1'

The :attr:`value` of an "object" node is a :obj:`dict[str, JSON]`:

>>> document["1a"].value
{'2a': JSON('foo'), '2b': JSON('bar')}

The :attr:`value` of an "array" node is a :obj:`list[JSON]`:

>>> document["1b"].value
[JSON({'3a': 'baz'}), JSON({'3b': 'quux'})]

Equality testing strictly follows the JSON data model. So, whereas the
following two Python lists compare equal:

>>> [False, True] == [0, 1]
True

The :class:`JSON` equivalents are not equal, because the arrays' items
have different JSON types:

>>> JSON([False, True]) == JSON([0, 1])
False

:class:`JSON` also implements the ``<``, ``<=``, ``>=``, ``>`` and
``!=`` comparison operators, which may be used wherever it makes sense
for the types of the given operands:

>>> JSON(3) < JSON(3.01)
True

A :class:`JSON` instance may be compared with *any* Python object.
Internally, the non-:class:`JSON` object is cast to its :class:`JSON`
equivalent before performing the comparison. Notice that tuples and
lists are considered structurally equivalent:

>>> (7, 11) == JSON([7, 11])
True

jschon is not a JSON encoder/decoder. However, the :class:`JSON` class
supports both serialization and deserialization of JSON documents, via
the Python standard library's :mod:`json` module.

Serializing a :class:`JSON` instance is simply a matter of getting its
string representation:

>>> str(JSON({"xyz": (None, False, True)}))
'{"xyz": [null, false, true]}'

:class:`JSON` instances can be deserialized from JSON files and JSON
strings using the :meth:`loadf` and :meth:`loads` class methods,
respectively:

>>> JSON.loadf('/path/to/file.json')
JSON(...)

>>> JSON.loads('{"1": "spam", "2": "eggs"}')
JSON({'1': 'spam', '2': 'eggs'})

Finally, a word on floating point numbers:

To ensure reliable operation of the JSON Schema "multipleOf" keyword,
:class:`float` values are converted to :class:`decimal.Decimal` by the
:class:`JSON` constructor, and parsed as :class:`decimal.Decimal`
during deserialization:

>>> JSON(5.1).value
Decimal('5.1')

>>> JSON.loads('{"pi": 3.14159}')["pi"].value
Decimal('3.14159')
