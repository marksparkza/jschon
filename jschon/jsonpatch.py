from enum import Enum
from typing import Mapping, List, Optional, Sequence

from jschon.exceptions import JSONPatchError, JSONPointerError
from jschon.json import JSONCompatible, JSON
from jschon.jsonpointer import JSONPointer

__all__ = [
    'JSONPatch',
]


class JSONPatch:
    def __init__(self, *operations: Mapping[str, JSONCompatible]):
        """Initialize a :class:`JSONPatch` instance from the given `operations`.

        :param operations: a sequence of JSON Patch operation-conformant objects
        """
        self.operations: List[Operation] = [
            Operation(operation) for operation in operations
        ]

    def evaluate(self, document: JSONCompatible) -> JSONCompatible:
        result = document
        for operation in self.operations:
            result = operation.evaluate(result)
        return result


class Operation:
    def __init__(self, operation: Mapping[str, JSONCompatible]):
        try:
            self.op: str = operation['op']
        except KeyError:
            raise JSONPatchError('Missing "op" keyword')

        try:
            self.path: JSONPointer = JSONPointer(operation['path'])
        except KeyError:
            raise JSONPatchError('Missing "path" keyword')
        except JSONPointerError:
            raise JSONPatchError('Invalid "path" value')

        self.value: JSONCompatible = None
        self.from_: Optional[JSONPointer] = None

        if self.op in ('add', 'replace', 'test'):
            try:
                self.value = operation['value']
            except KeyError:
                raise JSONPatchError('Missing "value" keyword')

        elif self.op == 'remove':
            pass

        elif self.op in ('move', 'copy'):
            try:
                self.from_ = JSONPointer(operation['from'])
            except KeyError:
                raise JSONPatchError('Missing "from" keyword')
            except JSONPointerError:
                raise JSONPatchError('Invalid "from" value')

        else:
            raise JSONPatchError('Invalid "op" value')

    def evaluate(self, document: JSONCompatible) -> JSONCompatible:
        if self.op == 'add':
            return self._add(document, self.path, self.value)
        if self.op == 'remove':
            return self._remove(document, self.path)
        if self.op == 'replace':
            return self._replace(document, self.path, self.value)
        if self.op == 'move':
            return self._move(document, self.path, self.from_)
        if self.op == 'copy':
            return self._copy(document, self.path, self.from_)
        if self.op == 'test':
            return self._test(document, self.path, self.value)

    @staticmethod
    def _add(document: JSONCompatible, path: JSONPointer, value: JSONCompatible) -> JSONCompatible:
        pathloc = Location(document, path)
        if pathloc.status == LocationStatus.ROOT:
            return value

        if pathloc.status in (LocationStatus.ARRAY_INDEX_NEW, LocationStatus.ARRAY_INDEX_EXISTS):
            pathloc.parent.insert(pathloc.index, value)
        elif pathloc.status in (LocationStatus.OBJECT_INDEX_NEW, LocationStatus.OBJECT_INDEX_EXISTS):
            pathloc.parent[pathloc.index] = value

        return document

    @staticmethod
    def _remove(document: JSONCompatible, path: JSONPointer) -> JSONCompatible:
        pathloc = Location(document, path)
        if pathloc.status == LocationStatus.ROOT:
            return None

        if pathloc.status in (LocationStatus.ARRAY_INDEX_EXISTS, LocationStatus.OBJECT_INDEX_EXISTS):
            del pathloc.parent[pathloc.index]
        else:
            raise JSONPatchError(f'Cannot remove nonexistent location {path}')

        return document

    @staticmethod
    def _replace(document: JSONCompatible, path: JSONPointer, value: JSONCompatible) -> JSONCompatible:
        pathloc = Location(document, path)
        if pathloc.status == LocationStatus.ROOT:
            return value

        if pathloc.status in (LocationStatus.ARRAY_INDEX_EXISTS, LocationStatus.OBJECT_INDEX_EXISTS):
            pathloc.parent[pathloc.index] = value
        else:
            raise JSONPatchError(f'Cannot replace nonexistent location {path}')

        return document

    @staticmethod
    def _move(document: JSONCompatible, path: JSONPointer, from_: JSONPointer) -> JSONCompatible:
        try:
            value = from_.evaluate(document)
        except JSONPointerError:
            raise JSONPatchError(f'Cannot move from nonexistent location {from_}')

        document = Operation._remove(document, from_)
        return Operation._add(document, path, value)

    @staticmethod
    def _copy(document: JSONCompatible, path: JSONPointer, from_: JSONPointer) -> JSONCompatible:
        try:
            value = from_.evaluate(document)
        except JSONPointerError:
            raise JSONPatchError(f'Cannot copy from nonexistent location {from_}')

        return Operation._add(document, path, value)

    @staticmethod
    def _test(document: JSONCompatible, path: JSONPointer, value: JSONCompatible) -> JSONCompatible:
        pathloc = Location(document, path)
        if pathloc.status in (LocationStatus.ROOT, LocationStatus.ARRAY_INDEX_EXISTS, LocationStatus.OBJECT_INDEX_EXISTS):
            if JSON(path.evaluate(document)) != JSON(value):
                raise JSONPatchError(f'The value at {path} does not equal {value}')
        else:
            raise JSONPatchError(f'Cannot test nonexistent location {path}')

        return document


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
