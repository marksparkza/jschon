from __future__ import annotations

import enum
import re
import urllib.parse


class Pointer:

    _pointer_re = re.compile(r'^(/([^~/]|(~[01]))*)*$')
    _array_index_re = re.compile(r'^0|([1-9][0-9]*)$')

    class _TokenType(enum.Enum):
        object_index = 1
        array_index = 2
        array_append = 3

    class _Token:
        def __init__(self, value: str) -> None:
            self.value = value
            if value == '-':
                self.token_type = Pointer._TokenType.array_append
            elif Pointer._array_index_re.fullmatch(value):
                self.token_type = Pointer._TokenType.array_index
                self.array_index = int(value)
            else:
                self.token_type = Pointer._TokenType.object_index
                self.object_index = value.replace('~1', '/').replace('~0', '~')

        def __eq__(self, other: Pointer._Token) -> bool:
            return self.value == other.value

    def __init__(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("Expecting str")
        if value and not self._pointer_re.fullmatch(value):
            raise ValueError(f"'{value}' is not a valid JSON pointer")
        self._tokens = [self._Token(token_str) for token_str in value.split('/')[1:]]

    def __add__(self, other: Pointer) -> Pointer:
        if not isinstance(other, Pointer):
            return NotImplemented
        ret = Pointer('')
        ret._tokens = self._tokens + other._tokens
        return ret

    def __eq__(self, other: Pointer) -> bool:
        if not isinstance(other, Pointer):
            return NotImplemented
        return self._tokens == other._tokens

    def __str__(self) -> str:
        return ''.join([f'/{token.value}' for token in self._tokens])

    def __repr__(self) -> str:
        return f"Pointer('{self}')"

    def is_root(self) -> bool:
        return not self._tokens

    @classmethod
    def parse_uri_fragment(cls, value: str) -> Pointer:
        if not value.startswith('#'):
            raise ValueError(f"'{value}' is not a valid URI fragment")
        return Pointer(urllib.parse.unquote(value[1:]))

    def uri_fragment(self) -> str:
        return f'#{urllib.parse.quote(str(self))}'
