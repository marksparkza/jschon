from __future__ import annotations

import json
import typing as _t

from jschon.pointer import Pointer
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
]


class JSON:

    def __new__(
            cls,
            value: JSONCompatible,
            *,
            location: Pointer = None,
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
        raise TypeError(f"value must be one of {JSONCompatible}")

    def __init__(
            self,
            value: JSONCompatible,
            *,
            location: Pointer = None,
    ) -> None:
        self._valueref = lambda: value
        self.location = location or Pointer('')

    def __eq__(self, other: _t.Union[JSON, 'JSONCompatible']) -> bool:
        if isinstance(other, JSON):
            return self.value == other.value
        if isinstance(other, JSONCompatible):
            return self.value == other
        return NotImplemented

    def __str__(self) -> str:
        return json.dumps(self.value)

    def __repr__(self) -> str:
        return f"JSON({self})"

    @property
    def value(self) -> JSONCompatible:
        return self._valueref()

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


class JSONNumber(JSON):

    @property
    def jsontype(self) -> str:
        return "number"


class JSONInteger(JSONNumber):

    @property
    def jsontype(self) -> str:
        return "integer"


class JSONString(JSON):

    @property
    def jsontype(self) -> str:
        return "string"


class JSONArray(JSON, _t.Sequence[JSON]):

    def __init__(
            self,
            array: _t.Sequence['JSONCompatible'],
            *,
            location: Pointer = None,
    ) -> None:
        super().__init__(array, location=location)
        self._items = [
            JSON(value, location=self.location + Pointer(f'/{index}'))
            for index, value in enumerate(array)
        ]

    def __getitem__(self, index: int) -> JSON:
        return self._items[index]

    def __len__(self) -> int:
        return len(self._items)

    @property
    def jsontype(self) -> str:
        return "array"


class JSONObject(JSON, _t.Mapping[str, JSON]):

    def __init__(
            self,
            obj: _t.Mapping[str, 'JSONCompatible'],
            *,
            location: Pointer = None,
    ) -> None:
        super().__init__(obj, location=location)
        self._properties = {}
        for key, value in obj.items():
            if not isinstance(key, str):
                raise TypeError("JSON object keys must be strings")
            self._properties[key] = JSON(value, location=self.location + Pointer(f'/{key}'))

    def __getitem__(self, key: str) -> JSON:
        return self._properties[key]

    def __iter__(self) -> _t.Iterator[str]:
        yield from self._properties

    def __len__(self) -> int:
        return len(self._properties)

    @property
    def jsontype(self) -> str:
        return "object"
