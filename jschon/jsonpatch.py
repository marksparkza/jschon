from __future__ import annotations

from copy import deepcopy
from enum import Enum
from typing import Dict, Iterable, List, Mapping, MutableSequence, Optional, Sequence, Union, overload

from jschon.exceptions import JSONPatchError, JSONPointerError
from jschon.json import JSON, JSONCompatible
from jschon.jsonpointer import JSONPointer

__all__ = [
    'JSONPatch',
    'JSONPatchOperation',
    'PatchOp',
    'apply_add',
    'apply_remove',
    'apply_replace',
    'apply_move',
    'apply_copy',
    'apply_test',
]


class PatchOp(str, Enum):
    ADD = 'add'
    REMOVE = 'remove'
    REPLACE = 'replace'
    MOVE = 'move'
    COPY = 'copy'
    TEST = 'test'

    def __repr__(self) -> str:
        return f'PatchOp.{self.name}'


class JSONPatchOperation:
    """:rfc:`6902`-conformant JSON patch operation object."""

    def __new__(
            cls,
            *,
            op: PatchOp,
            path: Union[str, JSONPointer],
            value: JSONCompatible = None,
            from_: Optional[Union[str, JSONPointer]] = None,
            **kwargs: Union[str, JSONPointer],
    ) -> JSONPatchOperation:
        """Create and return a new :class:`JSONPatchOperation` instance.

        :param op: The operation to perform. One of ``add``, ``remove``,
            ``replace``, ``move``, ``copy``, ``test``.
        :param path: A JSON pointer to the target location.
        :param value: For ``add`` and ``replace`` operations, the value
            to set at the target location. For ``test``, the value to
            compare with the target.
        :param from_: The location from which to ``move`` or ``copy``.
            An alias for `from`, which may be passed via `kwargs`.
        """
        self = object.__new__(cls)
        self.op = PatchOp(op)
        self.path = JSONPointer(path) if isinstance(path, str) else path
        self.value = value
        if from_ is None:
            from_ = kwargs.pop('from', None)
        self.from_ = JSONPointer(from_) if isinstance(from_, str) else from_
        return self

    def apply(self, document: JSONCompatible) -> JSONCompatible:
        """Apply the patch operation to `document` and return the
        resultant document."""
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

    def asdict(self) -> Dict[str, JSONCompatible]:
        """Return `self` as a dict."""
        result = {
            'op': self.op.value,
            'path': str(self.path),
        }
        if self.op in ('add', 'replace', 'test'):
            result['value'] = self.value
        elif self.op in ('move', 'copy'):
            result['from'] = str(self.from_)

        return result

    def __eq__(self, other: Union[JSONPatchOperation, Mapping[str, JSONCompatible]]) -> bool:
        """Return `self == other`."""
        if not isinstance(other, JSONPatchOperation):
            other = JSONPatchOperation(**other)
        return (self.op == other.op and
                self.path == other.path and
                self.from_ == other.from_ and
                JSON(self.value) == JSON(other.value))

    def __repr__(self) -> str:
        """Return `repr(self)`."""
        return f'JSONPatchOperation(op={self.op!r}, path={self.path!r}, from_={self.from_!r}, value={self.value!r})'


class JSONPatch(MutableSequence[JSONPatchOperation]):
    """:rfc:`6902`-conformant JSON Patch implementation."""

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
        """Return the result of sequentially applying all patch operations
        to `document`, as a new document. `document` itself is not modified."""
        result = deepcopy(document)
        for operation in self._operations:
            result = operation.apply(result)
        return result

    def aslist(self) -> List[Dict[str, JSONCompatible]]:
        """Return `self` as a list of operation dicts."""
        return [
            operation.asdict()
            for operation in self._operations
        ]

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
        raise TypeError('Expecting int or slice')

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

    def __eq__(self, other: Union[JSONPatch, Iterable[Union[JSONPatchOperation, Mapping[str, JSONCompatible]]]]) -> bool:
        """Return `self == other`."""
        if not isinstance(other, JSONPatch):
            other = JSONPatch(*other)
        return self._operations == other._operations

    def __repr__(self) -> str:
        """Return `repr(self)`."""
        return f'JSONPatch(*{self._operations!r})'


class NodeType(Enum):
    ROOT = 0
    ARRAY_ITEM = 1
    ARRAY_ITEM_NEW = 2
    OBJECT_PROPERTY = 3
    OBJECT_PROPERTY_NEW = 4


class Node:
    def __init__(self, document: JSONCompatible, path: JSONPointer):
        if not path:
            self.type = NodeType.ROOT
            self.parent = None
            self.index = None
            return

        try:
            self.parent = (parent := path[:-1].evaluate(document))
            key = path[-1]
        except JSONPointerError as e:
            raise JSONPatchError(f'Expecting an array or object at {path[:-1]}') from e

        if isinstance(parent, Sequence):
            try:
                if key == '-' or int(key) == len(parent):
                    self.type = NodeType.ARRAY_ITEM_NEW
                    self.index = len(parent)
                elif 0 <= int(key) < len(parent):
                    self.type = NodeType.ARRAY_ITEM
                    self.index = int(key)
                else:
                    raise ValueError
            except ValueError:
                raise JSONPatchError(f'Invalid array index {key}')

        elif isinstance(parent, Mapping):
            self.type = NodeType.OBJECT_PROPERTY if key in parent \
                else NodeType.OBJECT_PROPERTY_NEW
            self.index = key

        else:
            assert False


def apply_add(document: JSONCompatible, path: JSONPointer, value: JSONCompatible) -> JSONCompatible:
    target = Node(document, path)
    value = deepcopy(value)
    if target.type == NodeType.ROOT:
        return value

    if target.type in (NodeType.ARRAY_ITEM, NodeType.ARRAY_ITEM_NEW):
        target.parent.insert(target.index, value)

    elif target.type in (NodeType.OBJECT_PROPERTY, NodeType.OBJECT_PROPERTY_NEW):
        target.parent[target.index] = value

    return document


def apply_remove(document: JSONCompatible, path: JSONPointer) -> JSONCompatible:
    target = Node(document, path)
    if target.type == NodeType.ROOT:
        return None

    if target.type in (NodeType.ARRAY_ITEM, NodeType.OBJECT_PROPERTY):
        del target.parent[target.index]

    else:
        raise JSONPatchError(f'Cannot remove nonexistent target at {path}')

    return document


def apply_replace(document: JSONCompatible, path: JSONPointer, value: JSONCompatible) -> JSONCompatible:
    target = Node(document, path)
    value = deepcopy(value)
    if target.type == NodeType.ROOT:
        return value

    if target.type in (NodeType.ARRAY_ITEM, NodeType.OBJECT_PROPERTY):
        target.parent[target.index] = value

    else:
        raise JSONPatchError(f'Cannot replace nonexistent target at {path}')

    return document


def apply_move(document: JSONCompatible, path: JSONPointer, from_: JSONPointer) -> JSONCompatible:
    try:
        value = from_.evaluate(document)
    except JSONPointerError as e:
        raise JSONPatchError(f'Cannot move from nonexistent location {from_}') from e

    document = apply_remove(document, from_)
    return apply_add(document, path, value)


def apply_copy(document: JSONCompatible, path: JSONPointer, from_: JSONPointer) -> JSONCompatible:
    try:
        value = from_.evaluate(document)
    except JSONPointerError as e:
        raise JSONPatchError(f'Cannot copy from nonexistent location {from_}') from e

    return apply_add(document, path, value)


def apply_test(document: JSONCompatible, path: JSONPointer, value: JSONCompatible) -> JSONCompatible:
    target = Node(document, path)
    if target.type in (NodeType.ROOT, NodeType.ARRAY_ITEM, NodeType.OBJECT_PROPERTY):
        if JSON(path.evaluate(document)) != JSON(value):
            raise JSONPatchError(f'The value at {path} does not equal {value}')

    else:
        raise JSONPatchError(f'Cannot test nonexistent target at {path}')

    return document
