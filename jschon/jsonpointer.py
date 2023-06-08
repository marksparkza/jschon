from __future__ import annotations

import collections
import re
import urllib.parse
from typing import (
    Any, Iterable, Literal, Mapping, Sequence, Type, TYPE_CHECKING, Union, overload,
)

from jschon.exc import (
    JSONPointerMalformedError,
    JSONPointerReferenceError,
    RelativeJSONPointerMalformedError,
    RelativeJSONPointerReferenceError,
)

if TYPE_CHECKING:
    from jschon.json import JSON

__all__ = [
    'JSONPointer',
    'RelativeJSONPointer',
]

JSON_POINTER_RE = '(/([^~/]|(~[01]))*)*'
JSON_INDEX_RE = '0|([1-9][0-9]*)'
JSON_INDEX_MANIP_RE = r'((\+|-)[1-9][0-9]*)?'
RELATIVE_JSON_POINTER_RE = (
    f'(?P<up>{JSON_INDEX_RE})'
    f'(?P<over>{JSON_INDEX_MANIP_RE})'
    f'(?P<ref>#|{JSON_POINTER_RE})'
)


class JSONPointer(Sequence[str]):
    """:rfc:`6901`-conformant JSON Pointer implementation.

    A JSON pointer is a string representing a reference to some value within a
    JSON document. It consists of a series of *reference tokens* each prefixed by
    ``"/"``, each token in turn being the (escaped) JSON object key or the JSON
    array index at the next node down the path to the referenced value. The empty
    string ``""`` represents a reference to an entire JSON document.

    A :class:`JSONPointer` instance is an immutable sequence of the unescaped
    JSON object keys [#]_ and/or array indices [#]_ that comprise the path to a
    referenced value within a JSON document.

    A :class:`JSONPointer` instance is constructed by the concatenation of any
    number of arguments, each of which can be one of:

    - a string conforming to the :rfc:`6901` syntax
    - an iterable of unescaped keys (which may itself be a :class:`JSONPointer`
      instance)

    Two :class:`JSONPointer` instances compare equal if their key sequences are
    identical.

    The ``/`` operator provides a convenient syntax for extending a JSON pointer.
    It produces a new :class:`JSONPointer` instance by copying the left-hand
    argument (a :class:`JSONPointer` instance) and appending the right-hand
    argument (an unescaped key, or an iterable of unescaped keys).

    Taking an index into a :class:`JSONPointer` returns the unescaped key at
    that position. Taking a slice into a :class:`JSONPointer` returns a new
    :class:`JSONPointer` composed of the specified slice of the original's keys.

    .. [#] An *unescaped* object key is the unmodified form of the key within its
       mapping. Keys appearing in an RFC 6901 JSON pointer string, on the other
       hand, are required by the syntax to have reserved characters *escaped*.

    .. [#] Object keys and array indices are uniformly represented as strings
       and referred to as *keys* in the JSONPointer class.
    """

    malformed_exc: Type[JSONPointerMalformedError] = JSONPointerMalformedError
    """Exception raised when the input is not a valid JSON Pointer."""

    reference_exc: Type[JSONPointerReferenceError] = JSONPointerReferenceError
    """Exception raised when the JSON Pointer cannot be resolved against a document."""

    _json_pointer_re = re.compile(JSON_POINTER_RE)
    _array_index_re = re.compile(JSON_INDEX_RE)

    def __new__(cls, *values: Union[str, Iterable[str]]) -> JSONPointer:
        """Create and return a new :class:`JSONPointer` instance, constructed by
        the concatenation of the given `values`.

        :param values: each value may either be an RFC 6901 string, or an iterable
            of unescaped keys
        :raise JSONPointerMalformedError: if a string argument does not conform to
            the RFC 6901 syntax
        """
        self = object.__new__(cls)
        self._keys = []

        for value in values:
            if isinstance(value, str):
                if not JSONPointer._json_pointer_re.fullmatch(value):
                    raise cls.malformed_exc(f"'{value}' is not a valid JSON pointer")
                self._keys.extend(self.unescape(token) for token in value.split('/')[1:])

            elif isinstance(value, JSONPointer):
                self._keys.extend(value._keys)

            elif isinstance(value, Iterable):
                self._keys.extend(value)

            else:
                raise TypeError("Expecting str or Iterable[str]")

        return self

    @overload
    def __getitem__(self, index: int) -> str:
        ...

    @overload
    def __getitem__(self, index: slice) -> JSONPointer:
        ...

    def __getitem__(self, index):
        """Return `self[index]`."""
        if isinstance(index, int):
            return self._keys[index]
        if isinstance(index, slice):
            return JSONPointer(self._keys[index])
        raise TypeError("Expecting int or slice")

    def __len__(self) -> int:
        """Return `len(self)`."""
        return len(self._keys)

    @overload
    def __truediv__(self, suffix: str) -> JSONPointer:
        ...

    @overload
    def __truediv__(self, suffix: Iterable[str]) -> JSONPointer:
        ...

    def __truediv__(self, suffix) -> JSONPointer:
        """Return `self / suffix`."""
        if isinstance(suffix, str):
            return JSONPointer(self, (suffix,))
        if isinstance(suffix, Iterable):
            return JSONPointer(self, suffix)
        return NotImplemented

    def __eq__(self, other: JSONPointer) -> bool:
        """Return `self == other`."""
        if isinstance(other, JSONPointer):
            return self._keys == other._keys
        return NotImplemented

    def __le__(self, other: JSONPointer) -> bool:
        """Return `self <= other`.

        Test whether self is a prefix of other, that is,
        `self == other[:len(self)]`.
        """
        if isinstance(other, JSONPointer):
            return self._keys == other._keys[:len(self._keys)]
        return NotImplemented

    def __lt__(self, other: JSONPointer) -> bool:
        """Return `self < other`.

        Test whether self is a proper prefix of other, that is,
        `self <= other and self != other`.
        """
        if isinstance(other, JSONPointer):
            return len(self._keys) < len(other._keys) and self._keys == other._keys[:len(self._keys)]
        return NotImplemented

    def __hash__(self) -> int:
        """Return `hash(self)`."""
        return hash(tuple(self._keys))

    def __str__(self) -> str:
        """Return `str(self)`."""
        return ''.join([f'/{self.escape(key)}' for key in self._keys])

    def __repr__(self) -> str:
        """Return `repr(self)`."""
        return f"JSONPointer({str(self)!r})"

    def evaluate(self, document: Any) -> Any:
        """Return the value within `document` at the location referenced by `self`.

        `document` may be of any type, though if neither a :class:`Mapping` nor
        a :class:`Sequence`, evaluation by any non-empty :class:`JSONPointer`
        will always fail.

        :param document: any Python object
        :raise JSONPointerReferenceError: if `self` references a non-existent
            location in `document`
        """

        def resolve(value, keys):
            from jschon.json import JSON
            if not keys:
                return value

            key = keys.popleft()
            try:
                if (isjson := isinstance(value, JSON)) and value.type == "object" or \
                        not isjson and isinstance(value, Mapping):
                    return resolve(value[key], keys)

                if isjson and value.type == "array" or \
                        not isjson and isinstance(value, Sequence) and \
                        not isinstance(value, str) and \
                        JSONPointer._array_index_re.fullmatch(key):
                    return resolve(value[int(key)], keys)

            except (KeyError, IndexError):
                pass

            raise self.reference_exc(f"Path '{self}' not found in document")

        return resolve(document, collections.deque(self._keys))

    @classmethod
    def parse_uri_fragment(cls, value: str) -> JSONPointer:
        """Return a new :class:`JSONPointer` constructed from the :rfc:`6901`
        string obtained by decoding `value`.

        `value` must exclude the initial ``'#'`` of the fragment; this allows
        for sensible interoperation with :class:`~jschon.uri.URI` objects.

        :param value: a percent-encoded URI fragment
        """
        return JSONPointer(urllib.parse.unquote(value))

    def uri_fragment(self) -> str:
        """Return a percent-encoded URI fragment representation of `self`.

        The returned string excludes the initial ``'#'`` of the fragment; this
        allows for sensible interoperation with :class:`~jschon.uri.URI` objects.
        """

        # By default, urllib.parse.quote percent-encodes all characters
        # (apart from '/') defined by the "reserved" production, described
        # in RFC 3986. However, since the "fragment" production allows
        # characters in the "sub-delims" set, we include them in the safe
        # arg.
        #
        # pchar         = unreserved / pct-encoded / sub-delims / ":" / "@"
        # fragment      = *( pchar / "/" / "?" )
        # reserved      = gen-delims / sub-delims
        # gen-delims    = ":" / "/" / "?" / "#" / "[" / "]" / "@"
        # sub-delims    = "!" / "$" / "&" / "'" / "(" / ")"
        #               / "*" / "+" / "," / ";" / "="

        return urllib.parse.quote(str(self), safe="/!$&'()*+,;=")

    @staticmethod
    def escape(key: str) -> str:
        """Return the escaped form of a JSON object key / array index,
        suitable for use in an :rfc:`6901` JSON pointer string.

        :param key: an unescaped key
        """
        return key.replace('~', '~0').replace('/', '~1')

    @staticmethod
    def unescape(token: str) -> str:
        """Return the unescaped form of a reference token appearing in an
        :rfc:`6901` JSON pointer string

        :param token: an RFC 6901 reference token
        """
        return token.replace('~1', '/').replace('~0', '~')


class RelativeJSONPointer:
    malformed_exc: Type[
        RelativeJSONPointerMalformedError
    ] = RelativeJSONPointerMalformedError
    """Exception raised when the input is not a valid Relative JSON Pointer."""
    reference_exc: Type[
        RelativeJSONPointerReferenceError
    ] = RelativeJSONPointerReferenceError
    """Exception raised when the Relative JSON Pointer cannot be resolved against a document."""

    _regex = re.compile(RELATIVE_JSON_POINTER_RE)

    def __new__(
            cls,
            value: str = None,
            /,
            *,
            up: int = 0,
            over: int = 0,
            ref: Union[JSONPointer, Literal['#']] = JSONPointer(),
    ) -> RelativeJSONPointer:
        """Create and return a new :class:`RelativeJSONPointer` instance.

        :param value: a relative JSON pointer-conformant string; if `value` is
            given, keyword args are ignored
        :param up: the number of levels up from the current referenced JSON node
            from which to evaluate `ref`
        :param over: the integer value used to adjust the array index after
            applying `up`, which is only valid if that location is an array item;
            a value of 0, which is not allowed by the grammar, is treated as if
            there is no adjustment.
        :param ref: a :class:`JSONPointer` instance, or the literal ``'#'``
        :raise RelativeJSONPointerMalformedError: for any invalid arguments
        """
        self = object.__new__(cls)

        if value is not None:
            if not (match := RelativeJSONPointer._regex.fullmatch(value)):
                raise cls.malformed_exc(f"'{value}' is not a valid relative JSON pointer")

            up, over, ref = match.group('up', 'over', 'ref')
            self.up = int(up)
            self.over = int(over) if over else 0
            self.path = JSONPointer(ref) if ref != '#' else None

        else:
            self.up = up
            self.over = over
            self.path = ref if isinstance(ref, JSONPointer) else None

        self.index = ref == '#'

        if self.over:
            self._over_str = str(over) if self.over < 0 else f'+{self.over}'
        else:
            self._over_str = ''

        return self

    def __eq__(self, other: RelativeJSONPointer) -> bool:
        """Return `self == other`."""
        if isinstance(other, RelativeJSONPointer):
            return (self.up == other.up and
                    self.over == other.over and
                    self.index == other.index and
                    self.path == other.path)
        return NotImplemented

    def __hash__(self) -> int:
        """Return `hash(self)`."""
        return hash((self.up, self.over, self.index, self.path))

    def __str__(self) -> str:
        """Return `str(self)`."""
        if self.index:
            return f'{self.up}{self._over_str}#'
        return f'{self.up}{self._over_str}{self.path}'

    def __repr__(self) -> str:
        """Return `repr(self)`."""
        return f'RelativeJSONPointer({str(self)!r})'

    def evaluate(self, document: JSON) -> Union[int, str, JSON]:
        """Return the value within `document` at the location referenced by `self`.

        `document` must be an instance of :class:`JSON`, as evaluation relies
        on parent and sibling links provided by that class.

        :param document: a :class:`JSON` instance representing the document
        :raise RelativeJSONPointerReferenceError: if `self` references a non-existent
            location in `document`
        """
        node = document
        for _ in range(self.up):
            if node.parent is None:
                raise self.reference_exc('Up too many levels')
            node = node.parent

        if self.over:
            if node.parent is None:
                raise self.reference_exc('No containing node for index adjustment')
            if node.parent.type != "array":
                raise self.reference_exc(f'Index adjustment not valid for type {node.parent.type}')
            adjusted = int(node.key) + self.over
            if adjusted < 0 or adjusted >= len(node.parent):
                raise self.reference_exc(f'Index adjustment out of range')
            node = node.parent[adjusted]

        if self.index:
            if node.parent is None:
                raise self.reference_exc('No containing node')
            return int(node.key) if node.parent.type == "array" else node.key

        try:
            return self.path.evaluate(node)
        except JSONPointerReferenceError as e:
            raise self.reference_exc from e
