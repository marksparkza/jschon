from __future__ import annotations

import json
from typing import *

from jschon.jsonpointer import JSONPointer
from jschon.types import JSONCompatible, AnyJSONCompatible

__all__ = [
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


class JSON:
    __type__: str = ...

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

    def __new__(
            cls,
            value: AnyJSONCompatible,
            **kwargs: Any,
    ) -> JSON:
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
        if isinstance(value, Sequence):
            return object.__new__(JSONArray)
        if isinstance(value, Mapping):
            return object.__new__(JSONObject)
        raise TypeError(f"{value=} is not one of {JSONCompatible}")

    def __init__(
            self,
            value: AnyJSONCompatible,
            *,
            location: JSONPointer = None,
    ) -> None:
        self.value: AnyJSONCompatible = value
        self.location: JSONPointer = location or JSONPointer()

    def __eq__(self, other: Union[JSON, AnyJSONCompatible]) -> bool:
        if isinstance(other, type(self)):
            return self.value == other.value
        if isinstance(other, JSONCompatible):
            return self.value == other
        return NotImplemented

    def __str__(self) -> str:
        return json.dumps(self.value)

    def __repr__(self) -> str:
        return f"JSON({self})"

    def istype(self, jsontype: str) -> bool:
        return self.__type__ == jsontype


AnyJSON = TypeVar('AnyJSON', bound=JSON)


class JSONNull(JSON):
    __type__ = "null"

    def __new__(
            cls,
            value: None,
            **kwargs: Any,
    ) -> JSONNull:
        if isinstance(value, bool):
            return object.__new__(JSONNull)
        raise TypeError("Expecting None")


class JSONBoolean(JSON):
    __type__ = "boolean"

    def __new__(
            cls,
            value: bool,
            **kwargs: Any,
    ) -> JSONBoolean:
        if isinstance(value, bool):
            return object.__new__(JSONBoolean)
        raise TypeError("Expecting bool")

    def __eq__(self, other: Union[JSONBoolean, bool]) -> bool:
        if isinstance(other, JSONBoolean):
            return self.value is other.value
        if isinstance(other, bool):
            return self.value is other
        return NotImplemented


class JSONNumber(JSON):
    __type__ = "number"

    def __new__(
            cls,
            value: Union[int, float],
            **kwargs: Any,
    ) -> JSONNumber:
        if isinstance(value, (int, float)):
            return object.__new__(JSONNumber)
        raise TypeError("Expecting int or float")

    def __eq__(self, other: Union[JSONNumber, int, float]) -> bool:
        if isinstance(other, JSONNumber):
            return self.value == other.value
        if isinstance(other, (int, float)) and not isinstance(other, bool):
            return self.value == other
        return NotImplemented

    def __ge__(self, other: Union[JSONNumber, int, float]) -> bool:
        if isinstance(other, JSONNumber):
            return self.value >= other.value
        if isinstance(other, (int, float)) and not isinstance(other, bool):
            return self.value >= other
        return NotImplemented

    def __gt__(self, other: Union[JSONNumber, int, float]) -> bool:
        if isinstance(other, JSONNumber):
            return self.value > other.value
        if isinstance(other, (int, float)) and not isinstance(other, bool):
            return self.value > other
        return NotImplemented

    def __le__(self, other: Union[JSONNumber, int, float]) -> bool:
        if isinstance(other, JSONNumber):
            return self.value <= other.value
        if isinstance(other, (int, float)) and not isinstance(other, bool):
            return self.value <= other
        return NotImplemented

    def __lt__(self, other: Union[JSONNumber, int, float]) -> bool:
        if isinstance(other, JSONNumber):
            return self.value < other.value
        if isinstance(other, (int, float)) and not isinstance(other, bool):
            return self.value < other
        return NotImplemented

    def __mod__(self, other: Union[JSONNumber, int, float]) -> Union[int, float]:
        if isinstance(other, JSONNumber):
            return self.value % other.value
        if isinstance(other, (int, float)) and not isinstance(other, bool):
            return self.value % other
        return NotImplemented


class JSONInteger(JSONNumber):
    __type__ = "integer"

    def __new__(
            cls,
            value: int,
            **kwargs: Any,
    ) -> JSONInteger:
        if isinstance(value, int):
            return object.__new__(JSONInteger)
        raise TypeError("Expecting int")

    def istype(self, jsontype: str) -> bool:
        return jsontype in ("integer", "number")


class JSONString(JSON, Sized):
    __type__ = "string"

    def __new__(
            cls,
            value: str,
            **kwargs: Any,
    ) -> JSONString:
        if isinstance(value, str):
            return object.__new__(JSONString)
        raise TypeError("Expecting str")

    def __len__(self) -> int:
        return len(self.value)


class JSONArray(JSON, Sequence[AnyJSON]):
    __type__ = "array"

    def __new__(
            cls,
            value: Sequence[Union[JSON, AnyJSONCompatible]],
            **kwargs: Any,
    ) -> JSONArray:
        if isinstance(value, Sequence) and not isinstance(value, str):
            return object.__new__(JSONArray)
        raise TypeError("Expecting Sequence")

    def __init__(
            self,
            value: Sequence[Union[JSON, AnyJSONCompatible]],
            *,
            location: JSONPointer = None,
    ) -> None:
        super().__init__(value, location=location)
        self._items = [
            v if isinstance(v, JSON) else JSON(v, location=self.location / str(i))
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

    def __new__(
            cls,
            value: Mapping[str, Union[JSON, AnyJSONCompatible]],
            **kwargs: Any,
    ) -> JSONObject:
        if isinstance(value, Mapping) and all(isinstance(k, str) for k in value):
            return object.__new__(JSONObject)
        raise TypeError("Expecting Mapping[str, Any]")

    def __init__(
            self,
            value: Mapping[str, Union[JSON, AnyJSONCompatible]],
            *,
            location: JSONPointer = None,
    ) -> None:
        super().__init__(value, location=location)
        self._properties = {
            k: v if isinstance(v, JSON) else JSON(v, location=self.location / k)
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
