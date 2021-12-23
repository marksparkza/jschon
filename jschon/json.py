from __future__ import annotations

import json
from collections import deque
from decimal import Decimal
from functools import cached_property
from os import PathLike
from typing import Sequence, Mapping, Type, Optional, Iterator, Union, Any, List, Dict

from jschon.jsonpointer import JSONPointer
from jschon.utils import json_loadf, json_loads

__all__ = [
    'JSON',
    'JSONCompatible',
]

JSONCompatible = Union[None, bool, int, float, Decimal, str, Sequence[Any], Mapping[str, Any]]
"""Type hint for a JSON-compatible Python object."""


class JSON(Sequence['JSON'], Mapping[str, 'JSON']):
    """An implementation of the JSON data model."""

    @classmethod
    def loadf(cls, path: Union[str, PathLike], **kwargs: Any) -> JSON:
        """Deserialize a JSON file to a :class:`JSON` instance.

        :param path: the path to the file
        :param kwargs: keyword arguments to pass to the :class:`JSON` (subclass) constructor
        """
        return cls(json_loadf(path), **kwargs)

    @classmethod
    def loads(cls, value: str, **kwargs: Any) -> JSON:
        """Deserialize a JSON string to a :class:`JSON` instance.

        :param value: the JSON string
        :param kwargs: keyword arguments to pass to the :class:`JSON` (subclass) constructor
        """
        return cls(json_loads(value), **kwargs)

    def __init__(
            self,
            value: JSONCompatible,
            *,
            parent: JSON = None,
            key: str = None,
            itemclass: Type[JSON] = None,
            **itemkwargs: Any,
    ):
        """Initialize a :class:`JSON` instance from the given JSON-compatible
        `value`.

        The `parent`, `key`, `itemclass` and `itemkwargs` parameters should
        typically only be used in the construction of compound :class:`JSON`
        documents by :class:`JSON` subclasses.

        :param value: a JSON-compatible Python object
        :param parent: the parent node of the instance
        :param key: the index of the instance within its parent
        :param itemclass: the :class:`JSON` subclass used to instantiate
            child nodes of arrays and objects (default: :class:`JSON`)
        :param itemkwargs: keyword arguments to pass to the `itemclass`
            constructor
        """

        self.type: str
        """The JSON type of the instance. One of
        ``"null"``, ``"boolean"``, ``"number"``, ``"string"``, ``"array"``, ``"object"``."""

        self.data: Union[None, bool, int, Decimal, str, List[JSON], Dict[str, JSON]]
        """The instance data.
        
        =========   ===============
        JSON type   data type
        =========   ===============
        null        None
        boolean     bool
        number      int | Decimal
        string      str
        array       list[JSON]
        object      dict[str, JSON]
        =========   ===============
        """

        self.parent: Optional[JSON] = parent
        """The containing JSON instance."""

        self.key: Optional[str] = key
        """The index of the instance within its parent."""

        if value is None:
            self.type = "null"
            self.data = None

        elif isinstance(value, bool):
            self.type = "boolean"
            self.data = value

        elif isinstance(value, (int, Decimal)):
            self.type = "number"
            self.data = value

        elif isinstance(value, float):
            self.type = "number"
            self.data = Decimal(f'{value}')

        elif isinstance(value, str):
            self.type = "string"
            self.data = value

        elif isinstance(value, Sequence):
            itemclass = itemclass or JSON
            self.type = "array"
            self.data = [
                itemclass(v, parent=self, key=str(i), **itemkwargs)
                for i, v in enumerate(value)
            ]

        elif isinstance(value, Mapping):
            itemclass = itemclass or JSON
            self.type = "object"
            self.data = {
                k: itemclass(v, parent=self, key=k, **itemkwargs)
                for k, v in value.items()
            }

        else:
            raise TypeError(f"{value=} is not JSON-compatible")

    @cached_property
    def path(self) -> JSONPointer:
        """Return the path to the instance from the document root."""
        keys = deque()
        node = self
        while node.parent is not None:
            keys.appendleft(node.key)
            node = node.parent
        return JSONPointer(keys)

    @cached_property
    def value(self) -> JSONCompatible:
        """Return the instance data as a JSON-compatible Python object."""
        if isinstance(self.data, list):
            return [item.value for item in self.data]
        if isinstance(self.data, dict):
            return {key: item.value for key, item in self.data.items()}
        return self.data

    def __repr__(self) -> str:
        """Return `repr(self)`."""
        return f'{self.__class__.__name__}({json.loads(str(self))!r})'

    def __str__(self) -> str:
        """Return `str(self)`."""
        def default(o):
            if isinstance(o, JSON):
                return o.data
            if isinstance(o, Decimal):
                return float(o)
            raise TypeError

        return json.dumps(self.data, default=default,
                          ensure_ascii=False, allow_nan=False)

    def __bool__(self) -> bool:
        """Return `bool(self)`."""
        return bool(self.data)

    def __len__(self) -> int:
        """Return `len(self)` for an instance of type ``"string"``, ``"array"``
        or ``"object"``."""
        return len(self.data)

    def __iter__(self) -> Iterator:
        """Return `iter(self)` for an instance of type ``"array"`` or ``"object"``."""
        if self.type in ("array", "object"):
            return iter(self.data)
        raise TypeError(f"{self!r} is not iterable")

    def __getitem__(self, index: Union[int, slice, str]) -> JSON:
        """Return `self[index]` for an instance of type ``"array"`` or ``"object"``."""
        if isinstance(index, (int, slice)) and self.type == "array" or \
                isinstance(index, str) and self.type == "object":
            return self.data[index]
        raise TypeError(f"{self!r} is not subscriptable by {index!r}")

    def __eq__(self, other: Union[JSON, JSONCompatible]) -> bool:
        """Return `self == other`."""
        if not isinstance(other, JSON):
            other = JSON(other)
        if self.type == other.type:
            if self.type == "array":
                return len(self) == len(other) and \
                       all(item == other[i] for i, item in enumerate(self))
            if self.type == "object":
                return self.keys() == other.keys() and \
                       all(item == other[k] for k, item in self.items())
            return self.data == other.data
        return NotImplemented

    def __ge__(self, other: Union[JSON, int, float, Decimal, str]) -> bool:
        """Return `self >= other`, for instances of type ``"number"`` or ``"string"``."""
        if isinstance(other, JSON):
            return self.data >= other.data
        if isinstance(other, float):
            return self.data >= Decimal(f'{other}')
        return self.data >= other

    def __gt__(self, other: Union[JSON, int, float, Decimal, str]) -> bool:
        """Return `self > other`, for instances of type ``"number"`` or ``"string"``."""
        if isinstance(other, JSON):
            return self.data > other.data
        if isinstance(other, float):
            return self.data > Decimal(f'{other}')
        return self.data > other

    def __le__(self, other: Union[JSON, int, float, Decimal, str]) -> bool:
        """Return `self <= other`, for instances of type ``"number"`` or ``"string"``."""
        if isinstance(other, JSON):
            return self.data <= other.data
        if isinstance(other, float):
            return self.data <= Decimal(f'{other}')
        return self.data <= other

    def __lt__(self, other: Union[JSON, int, float, Decimal, str]) -> bool:
        """Return `self < other`, for instances of type ``"number"`` or ``"string"``."""
        if isinstance(other, JSON):
            return self.data < other.data
        if isinstance(other, float):
            return self.data < Decimal(f'{other}')
        return self.data < other
