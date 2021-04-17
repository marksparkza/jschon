from __future__ import annotations

import json
from collections import deque
from decimal import Decimal
from os import PathLike
from typing import Sequence, Mapping, TypeVar, Type, Optional, Iterator, Union, Any

from jschon.jsonpointer import JSONPointer
from jschon.utils import json_loadf, json_loads

__all__ = [
    'JSON',
    'AnyJSONCompatible',
]

AnyJSONCompatible = TypeVar('AnyJSONCompatible', 'None', bool, int, float, Decimal, str, Sequence, Mapping)


class JSON(Sequence['JSON'], Mapping[str, 'JSON']):

    @classmethod
    def loadf(cls, path: Union[str, PathLike], **kwargs: Any) -> JSON:
        """Deserialize a JSON file to a ``JSON`` instance."""
        return cls(json_loadf(path), **kwargs)

    @classmethod
    def loads(cls, value: str, **kwargs: Any) -> JSON:
        """Deserialize a JSON string to a ``JSON`` instance."""
        return cls(json_loads(value), **kwargs)

    def __init__(
            self,
            value: AnyJSONCompatible,
            *,
            parent: JSON = None,
            key: str = None,
            itemclass: Type[JSON] = None,
    ):
        self.value: AnyJSONCompatible
        self.type: str
        self.parent: Optional[JSON] = parent
        self.key: Optional[str] = key

        if value is None:
            self.type = "null"
            self.value = None

        elif isinstance(value, bool):
            self.type = "boolean"
            self.value = value

        elif isinstance(value, (int, Decimal)):
            self.type = "number"
            self.value = value

        elif isinstance(value, float):
            self.type = "number"
            self.value = Decimal(f'{value}')

        elif isinstance(value, str):
            self.type = "string"
            self.value = value

        elif isinstance(value, Sequence):
            self.type = "array"
            self.value = []
            itemclass = itemclass or JSON
            for i, v in enumerate(value):
                if isinstance(v, JSON):
                    v = v.value
                self.value += [itemclass(v, parent=self, key=str(i))]

        elif isinstance(value, Mapping) and all(isinstance(k, str) for k in value):
            self.type = "object"
            self.value = {}
            itemclass = itemclass or JSON
            for k, v in value.items():
                if isinstance(v, JSON):
                    v = v.value
                self.value[k] = itemclass(v, parent=self, key=k)

        else:
            raise TypeError(f"{value=} is not JSON-compatible")

    @property
    def path(self) -> JSONPointer:
        keys = deque()
        node = self
        while node.parent is not None:
            keys.appendleft(node.key)
            node = node.parent
        return JSONPointer(keys)

    def __repr__(self) -> str:
        # ugly but useful!
        return f'{self.__class__.__name__}({json.loads(str(self))!r})'

    def __str__(self) -> str:
        def default(o):
            if isinstance(o, JSON):
                return o.value
            if isinstance(o, Decimal):
                return float(o)
            raise TypeError

        return json.dumps(self.value, default=default,
                          ensure_ascii=False, allow_nan=False)

    def __bool__(self) -> bool:
        return bool(self.value)

    def __len__(self) -> int:
        return len(self.value)

    def __iter__(self) -> Iterator:
        if self.type in ("array", "object"):
            return iter(self.value)
        raise TypeError(f"{self!r} is not iterable")

    def __getitem__(self, index: Union[int, slice, str]) -> JSON:
        if isinstance(index, (int, slice)) and self.type == "array" or \
                isinstance(index, str) and self.type == "object":
            return self.value[index]
        raise TypeError(f"{self!r} is not subscriptable")

    def __eq__(self, other: Union[JSON, AnyJSONCompatible]) -> bool:
        if not isinstance(other, JSON):
            other = JSON(other)
        if self.type == other.type:
            if self.type == "array":
                return len(self) == len(other) and \
                       all(item == other[i] for i, item in enumerate(self))
            if self.type == "object":
                return self.keys() == other.keys() and \
                       all(item == other[k] for k, item in self.items())
            return self.value == other.value
        return NotImplemented

    def __ge__(self, other: Union[JSON, AnyJSONCompatible]) -> bool:
        if not isinstance(other, JSON):
            other = JSON(other)
        if self.type == other.type:
            return self.value >= other.value
        return NotImplemented

    def __gt__(self, other: Union[JSON, AnyJSONCompatible]) -> bool:
        if not isinstance(other, JSON):
            other = JSON(other)
        if self.type == other.type:
            return self.value > other.value
        return NotImplemented

    def __le__(self, other: Union[JSON, AnyJSONCompatible]) -> bool:
        if not isinstance(other, JSON):
            other = JSON(other)
        if self.type == other.type:
            return self.value <= other.value
        return NotImplemented

    def __lt__(self, other: Union[JSON, AnyJSONCompatible]) -> bool:
        if not isinstance(other, JSON):
            other = JSON(other)
        if self.type == other.type:
            return self.value < other.value
        return NotImplemented
