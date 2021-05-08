JSON Pointer
============
The :class:`~jschon.jsonpointer.JSONPointer` class is an implementation of the
:rfc:`6901` JSON Pointer specification. In jschon, :class:`~jschon.jsonpointer.JSONPointer`
is commonly used to represent paths to nodes within :class:`~jschon.json.JSON`
and :class:`~jschon.jsonschema.JSONSchema` documents, and to extract nodes from
those documents. But :class:`~jschon.jsonpointer.JSONPointer` is designed to work
with *any* JSON-compatible Python object - including, for example, native :class:`dict`
and :class:`list` objects.

Let's see how :class:`~jschon.jsonpointer.JSONPointer` works. We begin with an import:

>>> from jschon import JSON, JSONPointer

Now, consider the following example. This :class:`~jschon.json.JSON` instance describes
how characters in JSON object keys must be escaped in order to form *reference tokens*
within an :rfc:`6901` JSON pointer string:

>>> escape_rule = JSON([
...     {"~": "~0"},
...     {"/": "~1"}
... ])

Nodes within this instance can be referenced in the usual way, as described in the
:doc:`json` guide.

>>> escape_rule[1]["/"]
JSON('~1')

If we look at the :attr:`~jschon.json.JSON.path` property of this node, we see
that the string representation of the JSON pointer includes the *escaped* form of
the ``"/"`` key.

>>> escape_rule[1]["/"].path
JSONPointer('/1/~1')

Now let's get that path into a variable and inspect it a little more closely:

>>> slash_path = escape_rule[1]["/"].path

A :class:`~jschon.jsonpointer.JSONPointer` is a :obj:`Sequence[str]`, with each
item in the sequence being the *unescaped* object key and/or array index at the
next node down the path to the referenced value:

>>> [key for key in slash_path]
['1', '/']

Notice that the array index is represented as a string, too. In fact, it
matches the :attr:`~jschon.json.JSON.key` attribute on the corresponding
:class:`~jschon.json.JSON` node:

>>> escape_rule[1].key
'1'

The :meth:`~jschon.jsonpointer.JSONPointer.evaluate` method is used to extract
the referenced value from the JSON document:

>>> slash_path.evaluate(escape_rule)
JSON('~1')
