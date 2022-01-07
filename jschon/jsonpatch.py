from __future__ import annotations

from enum import Enum
from typing import List, Mapping, MutableSequence, Optional, Sequence, Union, overload

from jschon.exceptions import JSONPatchError, JSONPointerError
from jschon.json import JSON, JSONCompatible
from jschon.jsonpointer import JSONPointer

__all__ = [
    'JSONPatch',
    'JSONPatchOperation',
    'apply_add',
    'apply_remove',
    'apply_replace',
    'apply_move',
    'apply_copy',
    'apply_test',
]


class JSONPatchOperation:
    def __new__(cls, **kwargs: JSONCompatible) -> JSONPatchOperation:
        self = object.__new__(cls)
        try:
            self.op: str = kwargs['op']
        except KeyError:
            raise JSONPatchError('Missing "op" keyword')

        try:
            self.path: JSONPointer = JSONPointer(kwargs['path'])
        except KeyError:
            raise JSONPatchError('Missing "path" keyword')
        except JSONPointerError:
            raise JSONPatchError('Invalid "path" value')

        self.value: JSONCompatible = None
        self.from_: Optional[JSONPointer] = None

        if self.op in ('add', 'replace', 'test'):
            try:
                self.value = kwargs['value']
            except KeyError:
                raise JSONPatchError('Missing "value" keyword')

        elif self.op == 'remove':
            pass

        elif self.op in ('move', 'copy'):
            try:
                self.from_ = JSONPointer(kwargs['from'])
            except KeyError:
                raise JSONPatchError('Missing "from" keyword')
            except JSONPointerError:
                raise JSONPatchError('Invalid "from" value')

        else:
            raise JSONPatchError('Invalid "op" value')

        return self

    def __eq__(self, other: JSONPatchOperation) -> bool:
        return self.op == other.op and \
               self.path == other.path and \
               self.value == other.value and \
               self.from_ == other.from_

    def evaluate(self, document: JSONCompatible) -> JSONCompatible:
        if self.op == 'add':
            return apply_add(document, self.path, self.value)
        if self.op == 'remove':
            return apply_remove(document, self.path)
        if self.op == 'replace':
            return apply_replace(document, self.path, self.value)
        if self.op == 'move':
            return apply_move(document, self.path, self.from_)
        if self.op == 'copy':
            return apply_copy(document, self.path, self.from_)
        if self.op == 'test':
            return apply_test(document, self.path, self.value)


class JSONPatch(MutableSequence[JSONPatchOperation]):
    def __init__(self, *operations: Union[JSONPatchOperation, Mapping[str, JSONCompatible]]) -> None:
        """Initialize a :class:`JSONPatch` instance from the given `operations`,
        each of which may be a :class:`JSONPatchOperation` or a JSON patch
        operation-conformant dictionary.
        """
        self._operations: List[JSONPatchOperation] = [
            operation if isinstance(operation, JSONPatchOperation) else JSONPatchOperation(**operation)
            for operation in operations
        ]

    def evaluate(self, document: JSONCompatible) -> JSONCompatible:
        result = document
        for operation in self._operations:
            result = operation.evaluate(result)
        return result

    @overload
    def __getitem__(self, index: int) -> JSONPatchOperation:
        ...

    @overload
    def __getitem__(self, index: slice) -> JSONPatch:
        ...

    def __getitem__(self, index):
        """Return `self[index]`."""
        if isinstance(index, int):
            return self._operations[index]
        if isinstance(index, slice):
            return JSONPatch(*self._operations[index])
        raise TypeError("Expecting int or slice")

    def __setitem__(self, index: int, operation: Union[JSONPatchOperation, Mapping[str, JSONCompatible]]) -> None:
        """Set `self[index]` to `operation`."""
        if not isinstance(operation, JSONPatchOperation):
            operation = JSONPatchOperation(**operation)
        self._operations[index] = operation

    def __delitem__(self, index: int) -> None:
        """Delete `self[index]`."""
        del self._operations[index]

    def __len__(self) -> int:
        """Return `len(self)`."""
        return len(self._operations)

    def insert(self, index: int, operation: Union[JSONPatchOperation, Mapping[str, JSONCompatible]]) -> None:
        """Insert `operation` before `index`."""
        if not isinstance(operation, JSONPatchOperation):
            operation = JSONPatchOperation(**operation)
        self._operations.insert(index, operation)

    def __eq__(self, other: JSONPatch) -> bool:
        return self._operations == other._operations


class LocationStatus(Enum):
    ROOT = 0
    ARRAY_INDEX_EXISTS = 1
    ARRAY_INDEX_NEW = 2
    OBJECT_INDEX_EXISTS = 3
    OBJECT_INDEX_NEW = 4


class Location:
    def __init__(self, document: JSONCompatible, path: JSONPointer):
        if not path:
            self.status = LocationStatus.ROOT
            self.parent = None
            self.index = None
            return

        try:
            self.parent = (parent := path[:-1].evaluate(document))
            key = path[-1]
        except JSONPointerError:
            raise JSONPatchError(f'An array/object does not exist at location {path[:-1]}')

        if isinstance(parent, Sequence):
            try:
                if key == '-' or int(key) == len(parent):
                    self.status = LocationStatus.ARRAY_INDEX_NEW
                    self.index = len(parent)
                elif 0 <= int(key) < len(parent):
                    self.status = LocationStatus.ARRAY_INDEX_EXISTS
                    self.index = int(key)
                else:
                    raise ValueError
            except ValueError:
                raise JSONPatchError(f'Invalid array index {key}')

        elif isinstance(parent, Mapping):
            self.status = LocationStatus.OBJECT_INDEX_EXISTS if key in parent \
                else LocationStatus.OBJECT_INDEX_NEW
            self.index = key

        else:
            assert False


def apply_add(document: JSONCompatible, path: JSONPointer, value: JSONCompatible) -> JSONCompatible:
    pathloc = Location(document, path)
    if pathloc.status == LocationStatus.ROOT:
        return value

    if pathloc.status in (LocationStatus.ARRAY_INDEX_NEW, LocationStatus.ARRAY_INDEX_EXISTS):
        pathloc.parent.insert(pathloc.index, value)
    elif pathloc.status in (LocationStatus.OBJECT_INDEX_NEW, LocationStatus.OBJECT_INDEX_EXISTS):
        pathloc.parent[pathloc.index] = value

    return document


def apply_remove(document: JSONCompatible, path: JSONPointer) -> JSONCompatible:
    pathloc = Location(document, path)
    if pathloc.status == LocationStatus.ROOT:
        return None

    if pathloc.status in (LocationStatus.ARRAY_INDEX_EXISTS, LocationStatus.OBJECT_INDEX_EXISTS):
        del pathloc.parent[pathloc.index]
    else:
        raise JSONPatchError(f'Cannot remove nonexistent location {path}')

    return document


def apply_replace(document: JSONCompatible, path: JSONPointer, value: JSONCompatible) -> JSONCompatible:
    pathloc = Location(document, path)
    if pathloc.status == LocationStatus.ROOT:
        return value

    if pathloc.status in (LocationStatus.ARRAY_INDEX_EXISTS, LocationStatus.OBJECT_INDEX_EXISTS):
        pathloc.parent[pathloc.index] = value
    else:
        raise JSONPatchError(f'Cannot replace nonexistent location {path}')

    return document


def apply_move(document: JSONCompatible, path: JSONPointer, from_: JSONPointer) -> JSONCompatible:
    try:
        value = from_.evaluate(document)
    except JSONPointerError:
        raise JSONPatchError(f'Cannot move from nonexistent location {from_}')

    document = apply_remove(document, from_)
    return apply_add(document, path, value)


def apply_copy(document: JSONCompatible, path: JSONPointer, from_: JSONPointer) -> JSONCompatible:
    try:
        value = from_.evaluate(document)
    except JSONPointerError:
        raise JSONPatchError(f'Cannot copy from nonexistent location {from_}')

    return apply_add(document, path, value)


def apply_test(document: JSONCompatible, path: JSONPointer, value: JSONCompatible) -> JSONCompatible:
    pathloc = Location(document, path)
    if pathloc.status in (LocationStatus.ROOT, LocationStatus.ARRAY_INDEX_EXISTS, LocationStatus.OBJECT_INDEX_EXISTS):
        if JSON(path.evaluate(document)) != JSON(value):
            raise JSONPatchError(f'The value at {path} does not equal {value}')
    else:
        raise JSONPatchError(f'Cannot test nonexistent location {path}')

    return document
