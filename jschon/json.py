from __future__ import annotations

import json
from decimal import Decimal
from typing import *

from jschon.jsonpointer import JSONPointer

__all__ = [
    'JSONCompatible',
    'AnyJSONCompatible',
    'JSON',
    'AnyJSON',
    'JSONNull',
    'JSONBoolean',
    'JSONNumber',
    'JSONInteger',
    'JSONString',
    'JSONArray',
    'JSONObject',
]

# for runtime type checks
JSONCompatible = (type(None), bool, int, float, Decimal, str, Sequence, Mapping)
JSONCompatibleNumber = (int, float, Decimal)

# for type hints
AnyJSONCompatible = TypeVar('AnyJSONCompatible', 'None', bool, int, float, Decimal, str, Sequence, Mapping)
AnyJSONCompatibleNumber = TypeVar('AnyJSONCompatibleNumber', int, float, Decimal)


class JSON:
    __type__: str = ...

    class _Encoder(json.JSONEncoder):
        def __init__(self, *args, **kwargs):
            kwargs.update({'ensure_ascii': False, 'allow_nan': False})
            super().__init__(*args, **kwargs)

        def default(self, o: Any) -> AnyJSONCompatible:
            if isinstance(o, JSON):
                return self.default(o.value)
            if isinstance(o, Decimal):
                return float(o)
            return super().default(o)

    @classmethod
    def classfor(cls, jsontype: str):
        try:
            return {
                "null": JSONNull,
                "boolean": JSONBoolean,
                "number": JSONNumber,
                "integer": JSONInteger,
                "string": JSONString,
                "array": JSONArray,
                "object": JSONObject,
            }[jsontype]
        except KeyError:
            raise ValueError(f"{jsontype=} is not a recognized JSON type")

    @classmethod
    def iscompatible(cls, value: Any) -> bool:
        raise NotImplementedError

    def __new__(
            cls,
            value: AnyJSONCompatible,
            **kwargs: Any,
    ) -> JSON:
        for c in (JSONNull, JSONBoolean, JSONInteger, JSONNumber, JSONString, JSONArray, JSONObject):
            if c.iscompatible(value):
                return object.__new__(c)

        raise TypeError(f"{value=} is not JSON-compatible")

    def __init__(
            self,
            value: AnyJSONCompatible,
            *,
            path: JSONPointer = None,
    ) -> None:
        self.value: AnyJSONCompatible = value
        self.path: JSONPointer = path or JSONPointer()

    def __eq__(self, other: Union[JSON, AnyJSONCompatible]) -> bool:
        if isinstance(other, type(self)):
            return self.value == other.value
        if isinstance(other, JSONCompatible):
            return self.value == other
        return NotImplemented

    def __str__(self) -> str:
        return json.dumps(self.value, cls=self._Encoder)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.value!r})'

    def istype(self, jsontype: str) -> bool:
        return self.__type__ == jsontype


AnyJSON = TypeVar('AnyJSON', bound=JSON)


class JSONNull(JSON):
    __type__ = "null"

    @classmethod
    def iscompatible(cls, value: Any) -> bool:
        return value is None


class JSONBoolean(JSON):
    __type__ = "boolean"

    @classmethod
    def iscompatible(cls, value: Any) -> bool:
        return isinstance(value, bool)

    def __eq__(self, other: Union[JSONBoolean, bool]) -> bool:
        if isinstance(other, JSONBoolean):
            return self.value is other.value
        if isinstance(other, bool):
            return self.value is other
        return NotImplemented


class JSONNumber(JSON):
    __type__ = "number"

    @classmethod
    def iscompatible(cls, value: Any) -> bool:
        return isinstance(value, JSONCompatibleNumber) and not isinstance(value, bool)

    def istype(self, jsontype: str) -> bool:
        if jsontype == "integer":
            return JSONInteger.iscompatible(self.value)
        return jsontype == "number"

    def __eq__(self, other: Union[JSONNumber, AnyJSONCompatibleNumber]) -> bool:
        if isinstance(other, JSONNumber):
            return self.value == other.value
        if self.iscompatible(other):
            return self.value == other
        return NotImplemented

    def __ge__(self, other: Union[JSONNumber, AnyJSONCompatibleNumber]) -> bool:
        if isinstance(other, JSONNumber):
            return self.value >= other.value
        if self.iscompatible(other):
            return self.value >= other
        return NotImplemented

    def __gt__(self, other: Union[JSONNumber, AnyJSONCompatibleNumber]) -> bool:
        if isinstance(other, JSONNumber):
            return self.value > other.value
        if self.iscompatible(other):
            return self.value > other
        return NotImplemented

    def __le__(self, other: Union[JSONNumber, AnyJSONCompatibleNumber]) -> bool:
        if isinstance(other, JSONNumber):
            return self.value <= other.value
        if self.iscompatible(other):
            return self.value <= other
        return NotImplemented

    def __lt__(self, other: Union[JSONNumber, AnyJSONCompatibleNumber]) -> bool:
        if isinstance(other, JSONNumber):
            return self.value < other.value
        if self.iscompatible(other):
            return self.value < other
        return NotImplemented

    def __mod__(self, other: Union[JSONNumber, AnyJSONCompatibleNumber]) -> AnyJSONCompatibleNumber:
        if isinstance(other, JSONNumber):
            try:
                return self.value % other.value
            except TypeError:  # cannot mod float and Decimal
                return Decimal(self.value) % Decimal(other.value)
        if self.iscompatible(other):
            try:
                return self.value % other
            except TypeError:  # cannot mod float and Decimal
                return Decimal(self.value) % Decimal(other)
        return NotImplemented


class JSONInteger(JSONNumber):
    __type__ = "integer"

    @classmethod
    def iscompatible(cls, value: Any) -> bool:
        return isinstance(value, int) and not isinstance(value, bool) or \
               isinstance(value, (float, Decimal)) and value == int(value)

    def istype(self, jsontype: str) -> bool:
        return jsontype in ("integer", "number")


class JSONString(JSON, Sized):
    __type__ = "string"

    @classmethod
    def iscompatible(cls, value: Any) -> bool:
        return isinstance(value, str)

    def __len__(self) -> int:
        return len(self.value)


class JSONArray(JSON, Sequence[AnyJSON]):
    __type__ = "array"

    @classmethod
    def iscompatible(cls, value: Any) -> bool:
        return isinstance(value, Sequence) and not isinstance(value, str)

    def __init__(
            self,
            value: Sequence[Union[JSON, AnyJSONCompatible]],
            *,
            path: JSONPointer = None,
    ) -> None:
        super().__init__(value, path=path)
        self._items = [
            v if isinstance(v, JSON) else JSON(v, path=self.path / str(i))
            for i, v in enumerate(value)
        ]

    def __getitem__(self, index: int) -> AnyJSON:
        return self._items[index]

    def __len__(self) -> int:
        return len(self._items)

    def __eq__(self, other: Union[JSONArray, Sequence]) -> bool:
        if isinstance(other, (JSONArray, Sequence)) and not isinstance(other, str):
            return len(self) == len(other) and all(item == other[i] for i, item in enumerate(self))
        return NotImplemented


class JSONObject(JSON, Mapping[str, AnyJSON]):
    __type__ = "object"

    @classmethod
    def iscompatible(cls, value: Any) -> bool:
        return isinstance(value, Mapping) and all(isinstance(k, str) for k in value)

    def __init__(
            self,
            value: Mapping[str, Union[JSON, AnyJSONCompatible]],
            *,
            path: JSONPointer = None,
    ) -> None:
        super().__init__(value, path=path)
        self._properties = {
            k: v if isinstance(v, JSON) else JSON(v, path=self.path / k)
            for k, v in value.items()
        }

    def __getitem__(self, key: str) -> AnyJSON:
        return self._properties[key]

    def __iter__(self) -> Iterator[str]:
        yield from self._properties

    def __len__(self) -> int:
        return len(self._properties)

    def __eq__(self, other: Union[JSONObject, Mapping]) -> bool:
        if isinstance(other, (JSONObject, Mapping)):
            return self.keys() == other.keys() and all(item == other[k] for k, item in self.items())
        return NotImplemented
