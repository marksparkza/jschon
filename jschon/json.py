from __future__ import annotations

import collections
import json
import re
import typing as _t
import urllib.parse

from jschon.exceptions import JSONPointerError
from jschon.types import JSONCompatible

__all__ = [
    'JSON',
    'JSONNull',
    'JSONBoolean',
    'JSONNumber',
    'JSONInteger',
    'JSONString',
    'JSONArray',
    'JSONObject',
    'JSONPointer',
]


class JSON:

    typemap: _t.Dict[str, _t.Type[JSON]] = ...

    def __new__(
            cls,
            value: JSONCompatible,
            *,
            location: JSONPointer = None,
    ) -> JSON:
        if cls is not JSON:
            raise TypeError(f"{cls.__name__} cannot be instantiated directly")
        if value is None:
            return object.__new__(JSONNull)
        if isinstance(value, bool):
            return object.__new__(JSONBoolean)
        if isinstance(value, float):
            return object.__new__(JSONNumber)
        if isinstance(value, int):
            return object.__new__(JSONInteger)
        if isinstance(value, str):
            return object.__new__(JSONString)
        if isinstance(value, _t.Sequence):
            return object.__new__(JSONArray)
        if isinstance(value, _t.Mapping):
            return object.__new__(JSONObject)
        raise TypeError(f"{value=} is not one of {JSONCompatible}")

    def __init__(
            self,
            value: JSONCompatible,
            *,
            location: JSONPointer = None,
    ) -> None:
        self.value: JSONCompatible = value
        self.location: JSONPointer = location or JSONPointer('')

    def __eq__(self, other: _t.Union[JSON, 'JSONCompatible']) -> bool:
        if isinstance(other, type(self)):
            return self.value == other.value
        if isinstance(other, JSONCompatible):
            return self.value == other
        return NotImplemented

    def __str__(self) -> str:
        return json.dumps(self.value)

    def __repr__(self) -> str:
        return f"JSON({self})"

    def is_type(self, jsontype: str):
        return self.jsontype == jsontype

    @property
    def jsontype(self) -> str:
        raise NotImplementedError


class JSONNull(JSON):

    @property
    def jsontype(self) -> str:
        return "null"


class JSONBoolean(JSON):

    @property
    def jsontype(self) -> str:
        return "boolean"

    def __eq__(self, other: _t.Union[JSONBoolean, bool]) -> bool:
        if isinstance(other, JSONBoolean):
            return self.value is other.value
        if isinstance(other, bool):
            return self.value is other
        return NotImplemented


class JSONNumber(JSON):

    @property
    def jsontype(self) -> str:
        return "number"

    def __eq__(self, other: _t.Union[JSONNumber, int, float]) -> bool:
        if isinstance(other, JSONNumber):
            return self.value == other.value
        if isinstance(other, (int, float)) and not isinstance(other, bool):
            return self.value == other
        return NotImplemented

    def __ge__(self, other: _t.Union[JSONNumber, int, float]) -> bool:
        if isinstance(other, JSONNumber):
            return self.value >= other.value
        if isinstance(other, (int, float)) and not isinstance(other, bool):
            return self.value >= other
        return NotImplemented

    def __gt__(self, other: _t.Union[JSONNumber, int, float]) -> bool:
        if isinstance(other, JSONNumber):
            return self.value > other.value
        if isinstance(other, (int, float)) and not isinstance(other, bool):
            return self.value > other
        return NotImplemented

    def __le__(self, other: _t.Union[JSONNumber, int, float]) -> bool:
        if isinstance(other, JSONNumber):
            return self.value <= other.value
        if isinstance(other, (int, float)) and not isinstance(other, bool):
            return self.value <= other
        return NotImplemented

    def __lt__(self, other: _t.Union[JSONNumber, int, float]) -> bool:
        if isinstance(other, JSONNumber):
            return self.value < other.value
        if isinstance(other, (int, float)) and not isinstance(other, bool):
            return self.value < other
        return NotImplemented

    def __mod__(self, other: _t.Union[JSONNumber, int, float]) -> _t.Union[int, float]:
        if isinstance(other, JSONNumber):
            return self.value % other.value
        if isinstance(other, (int, float)) and not isinstance(other, bool):
            return self.value % other
        return NotImplemented


class JSONInteger(JSONNumber):

    @property
    def jsontype(self) -> str:
        return "integer"

    def is_type(self, jsontype: str):
        return jsontype in ("integer", "number")


class JSONString(JSON, _t.Sized):

    def __len__(self) -> int:
        return len(self.value)

    @property
    def jsontype(self) -> str:
        return "string"


class JSONArray(JSON, _t.Sequence[JSON]):

    def __init__(
            self,
            array: _t.Sequence['JSONCompatible'],
            *,
            location: JSONPointer = None,
    ) -> None:
        super().__init__(array, location=location)
        self._items = [
            JSON(value, location=self.location + JSONPointer(f'/{index}'))
            for index, value in enumerate(array)
        ]

    def __getitem__(self, index: int) -> JSON:
        return self._items[index]

    def __len__(self) -> int:
        return len(self._items)

    def __eq__(self, other: _t.Union[JSONArray, _t.Sequence]) -> bool:
        if isinstance(other, (JSONArray, _t.Sequence)) and not isinstance(other, str):
            return len(self) == len(other) and all(item == other[i] for i, item in enumerate(self))
        return NotImplemented

    @property
    def jsontype(self) -> str:
        return "array"


class JSONObject(JSON, _t.Mapping[str, JSON]):

    def __init__(
            self,
            obj: _t.Mapping[str, 'JSONCompatible'],
            *,
            location: JSONPointer = None,
    ) -> None:
        super().__init__(obj, location=location)
        self._properties = {}
        for key, value in obj.items():
            if not isinstance(key, str):
                raise TypeError("JSON object keys must be strings")
            self._properties[key] = JSON(value, location=self.location + JSONPointer(f'/{key}'))

    def __getitem__(self, key: str) -> JSON:
        return self._properties[key]

    def __iter__(self) -> _t.Iterator[str]:
        yield from self._properties

    def __len__(self) -> int:
        return len(self._properties)

    def __eq__(self, other: _t.Union[JSONObject, _t.Mapping]) -> bool:
        if isinstance(other, (JSONObject, _t.Mapping)):
            return self.keys() == other.keys() and all(item == other[k] for k, item in self.items())
        return NotImplemented

    @property
    def jsontype(self) -> str:
        return "object"


JSON.typemap = {
    "null": JSONNull,
    "boolean": JSONBoolean,
    "number": JSONNumber,
    "integer": JSONInteger,
    "string": JSONString,
    "array": JSONArray,
    "object": JSONObject,
}


class JSONPointer:

    _json_pointer_re = re.compile(r'^(/([^~/]|(~[01]))*)*$')
    _array_index_re = re.compile(r'^0|([1-9][0-9]*)$')

    def __init__(self, value: str) -> None:
        if value and not self._json_pointer_re.fullmatch(value):
            raise JSONPointerError(f"'{value}' is not a valid JSON pointer")
        self._tokens: _t.List[str] = [token for token in value.split('/')[1:]]

    def __add__(self, other: JSONPointer) -> JSONPointer:
        if not isinstance(other, JSONPointer):
            return NotImplemented
        result = JSONPointer('')
        result._tokens = self._tokens + other._tokens
        return result

    def __eq__(self, other: JSONPointer) -> bool:
        if not isinstance(other, JSONPointer):
            return NotImplemented
        return self._tokens == other._tokens

    def __str__(self) -> str:
        return ''.join([f'/{token}' for token in self._tokens])

    def __repr__(self) -> str:
        return f"JSONPointer('{self}')"

    def is_root(self) -> bool:
        return not self._tokens

    def evaluate(self, document: _t.Union[JSONObject, JSONArray]) -> JSON:

        def resolve(value: JSON, tokens: _t.Deque[str]) -> _t.Optional[JSON]:
            if not tokens:
                return value
            token = tokens.popleft()
            try:
                if isinstance(value, JSONObject):
                    return resolve(value[token.replace('~1', '/').replace('~0', '~')], tokens)
                if isinstance(value, JSONArray) and self._array_index_re.fullmatch(token):
                    return resolve(value[int(token)], tokens)
            except (KeyError, IndexError):
                pass

        target = resolve(document, collections.deque(self._tokens))
        if target is None:
            raise JSONPointerError(f"Failed to resolve '{self}' against the given document")

        return target

    @classmethod
    def parse_uri_fragment(cls, value: str) -> JSONPointer:
        if not value.startswith('#'):
            raise JSONPointerError(f"'{value}' is not a valid URI fragment")
        return JSONPointer(urllib.parse.unquote(value[1:]))

    def uri_fragment(self) -> str:
        return f'#{urllib.parse.quote(str(self))}'
