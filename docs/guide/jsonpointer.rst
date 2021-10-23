JSON Pointer
============
The :class:`~jschon.jsonpointer.JSONPointer` class is an implementation of the
:rfc:`6901` JSON Pointer specification. In jschon, :class:`~jschon.jsonpointer.JSONPointer`
is commonly used to represent paths to nodes within :class:`~jschon.json.JSON`
and :class:`~jschon.jsonschema.JSONSchema` documents, and to extract nodes from
those documents. But :class:`~jschon.jsonpointer.JSONPointer` is designed to work
with *any* JSON-compatible Python object -- including, for example, native :class:`dict`
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
:doc:`json` guide:

>>> escape_rule[1]["/"]
JSON('~1')

If we look at the :attr:`~jschon.json.JSON.path` property of this node, we see
that the string representation of the JSON pointer includes the *escaped* form of
the ``"/"`` key:

>>> escape_rule[1]["/"].path
JSONPointer('/1/~1')

Now let's get that path into a variable and inspect it a little more closely:

>>> slash_path = escape_rule[1]["/"].path

A :class:`~jschon.jsonpointer.JSONPointer` is a :obj:`Sequence[str]`, with each
item in the sequence being the *unescaped* object key or array index at the next
node down the path to the referenced value:

>>> [key for key in slash_path]
['1', '/']

You can create a :class:`list` or :class:`tuple` of keys directly from a
:class:`~jschon.jsonpointer.JSONPointer` instance:

>>> tuple(slash_path)
('1', '/')

Notice that the array index is represented as a string, too. In fact, it
matches the :attr:`~jschon.json.JSON.key` attribute on the corresponding
:class:`~jschon.json.JSON` node:

>>> escape_rule[1].key
'1'

To extract the referenced object from a JSON document, we use the
:meth:`~jschon.jsonpointer.JSONPointer.evaluate` method:

>>> slash_path.evaluate(escape_rule)
JSON('~1')

So far, we've seen how to work with the :class:`~jschon.jsonpointer.JSONPointer`
instance that appears as the :attr:`~jschon.json.JSON.path` of a :class:`~jschon.json.JSON`
node. Now let's look at how to construct a :class:`~jschon.jsonpointer.JSONPointer`.
Consider the following example document:

>>> doc = {"a": {"b": {"c": {"d": "😎"}}}}

The obvious way to make a :class:`~jschon.jsonpointer.JSONPointer` that points
to the leaf node in this example would be:

>>> JSONPointer('/a/b/c/d')
JSONPointer('/a/b/c/d')

Then, as we'd expect:

>>> JSONPointer('/a/b/c/d').evaluate(doc)
'😎'

But here are a few alternative ways to create the same JSON pointer:

>>> JSONPointer(['a', 'b', 'c', 'd'])
JSONPointer('/a/b/c/d')

>>> JSONPointer(['a'], '/b/c', ['d'])
JSONPointer('/a/b/c/d')

>>> JSONPointer('/a/b', JSONPointer('/c/d'))
JSONPointer('/a/b/c/d')

As you can see, the :class:`~jschon.jsonpointer.JSONPointer` constructor accepts
-- and concatenates -- any number of arguments. Each argument can be either:

- an :rfc:`6901` JSON pointer string (with reserved characters escaped); or
- an iterable of unescaped keys or array indices -- which may itself be a
  :class:`~jschon.jsonpointer.JSONPointer` instance.

A special case is the :class:`~jschon.jsonpointer.JSONPointer` constructed without
any args:

>>> JSONPointer()
JSONPointer('')

This represents a reference to an entire document:

>>> JSONPointer().evaluate(doc)
{'a': {'b': {'c': {'d': '😎'}}}}

The ``/`` operator provides a convenient way to extend a :class:`~jschon.jsonpointer.JSONPointer`:

>>> JSONPointer() / 'a' / ('b', 'c', 'd')
JSONPointer('/a/b/c/d')

>>> JSONPointer('/a/b') / JSONPointer('/c/d')
JSONPointer('/a/b/c/d')

It works by copying the left-hand operand (a :class:`~jschon.jsonpointer.JSONPointer`
instance) and appending the right-hand operand (an unescaped key, or an iterable
of unescaped keys). Note that :class:`~jschon.jsonpointer.JSONPointer` is immutable,
so each invocation of ``/`` produces a new :class:`~jschon.jsonpointer.JSONPointer`
instance.

As a :class:`Sequence`, :class:`~jschon.jsonpointer.JSONPointer` supports getting
a key by its index:

>>> JSONPointer('/a/b/c/d')[-4]
'a'

And taking a slice into a :class:`~jschon.jsonpointer.JSONPointer` returns a new
:class:`~jschon.jsonpointer.JSONPointer` instance composed of the specified slice
of the original's keys:

>>> JSONPointer('/a/b/c/d')[1:-1]
JSONPointer('/b/c')
