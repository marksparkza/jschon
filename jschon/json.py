from __future__ import annotations

import json
from collections import deque
from functools import cached_property
from os import PathLike
from typing import Any, Dict, Iterator, List, Mapping, MutableMapping, MutableSequence, Optional, Sequence, Type, Union

from jschon.jsonpointer import JSONPointer
from jschon.utils import json_dumpf, json_dumps, json_loadf, json_loadr, json_loads

__all__ = [
    'JSON',
    'JSONCompatible',
]

JSONCompatible = Union[None, bool, int, float, str, Sequence[Any], Mapping[str, Any]]
"""Type hint for a JSON-compatible Python object."""


class JSON(MutableSequence['JSON'], MutableMapping[str, 'JSON']):
    """An implementation of the JSON data model."""

    @classmethod
    def loadf(cls, path: Union[str, PathLike], **kwargs: Any) -> JSON:
        """Deserialize a JSON file to a :class:`JSON` instance.

        :param path: the path to the file
        :param kwargs: keyword arguments to pass to the :class:`JSON` (subclass) constructor
        """
        return cls(json_loadf(path), **kwargs)

    @classmethod
    def loadr(cls, url: str, **kwargs: Any) -> JSON:
        """Deserialize a remote JSON resource to a :class:`JSON` instance.

        :param url: the URL of the resource
        :param kwargs: keyword arguments to pass to the :class:`JSON` (subclass) constructor
        """
        return cls(json_loadr(url), **kwargs)

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
        ``null``, ``boolean``, ``number``, ``string``, ``array``, ``object``."""

        self.data: Union[None, bool, int, float, str, List[JSON], Dict[str, JSON]]
        """The instance data.
        
        =========   ===============
        JSON type   data type
        =========   ===============
        null        None
        boolean     bool
        number      int | float
        string      str
        array       list[JSON]
        object      dict[str, JSON]
        =========   ===============
        """

        self.parent: Optional[JSON] = parent
        """The containing JSON instance."""

        self.key: Optional[str] = key
        """The index of the instance within its parent."""

        self.itemclass: Type[JSON] = itemclass or JSON
        """The :class:`JSON` class type of child instances."""

        self.itemkwargs: Dict[str, Any] = itemkwargs
        """Keyword arguments to the :attr:`itemclass` constructor."""

        if value is None:
            self.type = "null"
            self.data = None

        elif isinstance(value, bool):
            self.type = "boolean"
            self.data = value

        elif isinstance(value, (int, float)):
            self.type = "number"
            self.data = value

        elif isinstance(value, str):
            self.type = "string"
            self.data = value

        elif isinstance(value, Sequence):
            self.type = "array"
            self.data = [
                self.itemclass(v, parent=self, key=str(i), **self.itemkwargs)
                for i, v in enumerate(value)
            ]

        elif isinstance(value, Mapping):
            self.type = "object"
            self.data = {
                k: self.itemclass(v, parent=self, key=k, **self.itemkwargs)
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

    def _invalidate_path(self) -> None:
        try:
            del self.path
        except AttributeError:
            pass
        if self.type == 'array':
            for item in self.data:
                item._invalidate_path()
        elif self.type == 'object':
            for item in self.data.values():
                item._invalidate_path()

    def _invalidate_value(self) -> None:
        try:
            del self.value
        except AttributeError:
            pass
        if self.parent is not None:
            self.parent._invalidate_value()

    def dumpf(self, path: Union[str, PathLike]) -> None:
        """Serialize the instance data to a JSON file.

        :param path: the path to the file
        """
        json_dumpf(self.data, path)

    def dumps(self) -> str:
        """Serialize the instance data to a JSON string."""
        return json_dumps(self.data)

    def __repr__(self) -> str:
        """Return `repr(self)`."""
        return f'{self.__class__.__name__}({json.loads(self.dumps())!r})'

    def __str__(self) -> str:
        """Return `str(self)`."""
        return self.dumps()

    def __bool__(self) -> bool:
        """Return `bool(self)`."""
        return bool(self.data)

    def __len__(self) -> int:
        """Return `len(self)`.

        Supported for JSON types ``string``, ``array`` and ``object``.
        """
        return len(self.data)

    def __iter__(self) -> Iterator:
        """Return `iter(self)`.

        Supported for JSON types ``array`` and ``object``.
        """
        return iter(self.data)

    def __getitem__(self, index: Union[int, slice, str]) -> JSON:
        """Return `self[index]`.

        Supported for JSON types ``array`` and ``object``.
        """
        return self.data[index]

    def __setitem__(self, index: Union[int, str], obj: Union[JSON, JSONCompatible]) -> None:
        """Set `self[index]` to `obj`.

        Supported for JSON types ``array`` and ``object``.
        """
        self.data[index] = self.itemclass(
            obj.value if isinstance(obj, JSON) else obj,
            parent=self,
            key=str(index),
            **self.itemkwargs,
        )
        self._invalidate_value()

    def __delitem__(self, index: Union[int, str]) -> None:
        """Delete `self[index]`.

        Supported for JSON types ``array`` and ``object``.
        """
        del self.data[index]
        self._invalidate_value()
        if self.type == 'array':
            for item in self.data[index:]:
                item.key = str(int(item.key) - 1)
                item._invalidate_path()

    def insert(self, index: int, obj: Union[JSON, JSONCompatible]) -> None:
        """Insert `obj` before `index`.

        Supported for JSON type ``array``.
        """
        self.data.insert(index, self.itemclass(
            obj.value if isinstance(obj, JSON) else obj,
            parent=self,
            key=str(index),
            **self.itemkwargs,
        ))
        self._invalidate_value()
        for item in self.data[index + 1:]:
            item.key = str(int(item.key) + 1)
            item._invalidate_path()

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

    def __ge__(self, other: Union[JSON, int, float, str]) -> bool:
        """Return `self >= other`.

        Supported for JSON types ``number`` and ``string``.
        """
        if isinstance(other, JSON):
            return self.data >= other.data
        return self.data >= other

    def __gt__(self, other: Union[JSON, int, float, str]) -> bool:
        """Return `self > other`.

        Supported for JSON types ``number`` and ``string``.
        """
        if isinstance(other, JSON):
            return self.data > other.data
        return self.data > other

    def __le__(self, other: Union[JSON, int, float, str]) -> bool:
        """Return `self <= other`.

        Supported for JSON types ``number`` and ``string``.
        """
        if isinstance(other, JSON):
            return self.data <= other.data
        return self.data <= other

    def __lt__(self, other: Union[JSON, int, float, str]) -> bool:
        """Return `self < other`.

        Supported for JSON types ``number`` and ``string``.
        """
        if isinstance(other, JSON):
            return self.data < other.data
        return self.data < other
