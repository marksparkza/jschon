from __future__ import annotations

import collections
import re
import typing as _t
import urllib.parse

from jschon.exceptions import JSONPointerError

__all__ = [
    'JSONPointer',
]


class JSONPointer(_t.Sequence[str]):
    """JSON Pointer :rfc:`6901`

    A JSON Pointer represents a reference to some value within a JSON document.
    A ``JSONPointer`` instance is composed of an immutable sequence of unescaped
    JSON object keys and/or array indices that comprise the path to the referenced
    value.

    A ``JSONPointer`` instance may be constructed either from a string conforming
    to the :rfc:`6901` syntax (comprising escaped reference tokens), from an existing
    ``JSONPointer`` instance optionally extended with a :rfc:`6901` JSON Pointer string,
    or from an iterable of unescaped JSON object keys and array indices.

    The ``/`` operator produces a new ``JSONPointer`` instance by copying the left-hand
    argument (a ``JSONPointer`` instance) and appending the right-hand argument (an
    unescaped JSON object key or array index).

    Taking an index into a ``JSONPointer`` returns the unescaped JSON object key or
    array index at that position. Taking a slice into a ``JSONPointer`` returns a new
    ``JSONPointer`` composed of the specified slice of the original's tokens.
    """

    _json_pointer_re = re.compile(r'^(/([^~/]|(~[01]))*)*$')
    _array_index_re = re.compile(r'^0|([1-9][0-9]*)$')

    @_t.overload
    def __init__(self, value: str) -> None:
        ...

    @_t.overload
    def __init__(self, value: JSONPointer, extend: str = None) -> None:
        ...

    @_t.overload
    def __init__(self, value: _t.Iterable[str]) -> None:
        ...

    def __init__(
            self,
            value: _t.Union[str, JSONPointer, _t.Iterable[str]],
            extend: str = None,
    ) -> None:
        self._tokens: _t.List[str]  # list of escaped reference tokens

        if isinstance(value, str):
            if value and not self._json_pointer_re.fullmatch(value):
                raise JSONPointerError(f"'{value}' is not a valid JSON pointer")
            self._tokens = [token for token in value.split('/')[1:]]

        elif isinstance(value, JSONPointer):
            if extend and not self._json_pointer_re.fullmatch(extend):
                raise JSONPointerError(f"'{extend}' is not a valid JSON pointer")
            self._tokens = value._tokens + [token for token in extend.split('/')[1:]]

        elif isinstance(value, _t.Iterable):
            self._tokens = [self.escape(key) for key in value]
            if not self._json_pointer_re.fullmatch(str(self)):
                raise JSONPointerError(f"Cannot construct a valid JSON pointer from {value}")

        else:
            raise TypeError("Expecting str, JSONPointer, or Iterable[str]")

    @_t.overload
    def __getitem__(self, index: int) -> str:
        ...

    @_t.overload
    def __getitem__(self, index: slice) -> JSONPointer:
        ...

    def __getitem__(self, index: _t.Union[int, slice]) -> _t.Union[str, JSONPointer]:
        if isinstance(index, int):
            return self.unescape(self._tokens[index])
        if isinstance(index, slice):
            return JSONPointer(self.unescape(token) for token in self._tokens[index])
        raise TypeError("Expecting int or slice")

    def __len__(self) -> int:
        return len(self._tokens)

    def __truediv__(self, key: str):
        return JSONPointer(self, f'/{self.escape(key)}')

    def __eq__(self, other: JSONPointer) -> bool:
        if not isinstance(other, JSONPointer):
            return NotImplemented
        return self._tokens == other._tokens

    def __str__(self) -> str:
        return ''.join([f'/{token}' for token in self._tokens])

    def __repr__(self) -> str:
        return f"JSONPointer('{self}')"

    @property
    def is_root(self) -> bool:
        return not self._tokens

    def evaluate(self, document: _t.Union[_t.Mapping, _t.Sequence]) -> _t.Any:
        """Return the value from within the given document that is referenced by this JSON Pointer.

        :raises JSONPointerError: if the JSON Pointer refers to a nonexistent location within the document
        """
        def resolve(value, tokens):
            if not tokens:
                return value
            token = tokens.popleft()
            try:
                if isinstance(value, _t.Mapping):
                    return resolve(value[self.unescape(token)], tokens)
                if isinstance(value, _t.Sequence) and not isinstance(value, str) and \
                        self._array_index_re.fullmatch(token):
                    return resolve(value[int(token)], tokens)
            except (KeyError, IndexError):
                pass
            raise JSONPointerError(f"Failed to resolve '{self}' against the given document")

        return resolve(document, collections.deque(self._tokens))

    @classmethod
    def parse_uri_fragment(cls, value: str) -> JSONPointer:
        if not value.startswith('#'):
            raise JSONPointerError(f"'{value}' is not a valid URI fragment")
        return JSONPointer(urllib.parse.unquote(value[1:]))

    def uri_fragment(self) -> str:
        return f'#{urllib.parse.quote(str(self))}'

    @staticmethod
    def escape(key: str):
        return key.replace('~', '~0').replace('/', '~1')

    @staticmethod
    def unescape(token: str):
        return token.replace('~1', '/').replace('~0', '~')
