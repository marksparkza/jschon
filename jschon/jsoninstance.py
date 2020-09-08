from __future__ import annotations

from typing import Generic, Optional, Dict, Callable

from jschon.exceptions import JSONSchemaError
from jschon.json import AnyJSON, JSON
from jschon.jsonpointer import JSONPointer
from jschon.types import AnyJSONCompatible


__all__ = [
    'JSONInstance',
]


class JSONInstance(Generic[AnyJSON]):

    def __init__(
            self,
            json: JSON,
            path: JSONPointer,
            parent: Optional[JSONInstance],
    ):
        self.json: AnyJSON = json
        self.path: JSONPointer = path
        self.parent: Optional[JSONInstance] = parent
        self.children: Dict[str, JSONInstance] = {}
        self._valid: Optional[bool] = None
        self.annotation: Optional[AnyJSONCompatible] = None
        self.error: Optional[str] = None
        self.assert_: bool = True

    def sibling(self, key: str) -> Optional[JSONInstance]:
        return self.parent.children.get(key) if self.parent else None

    def descend(
            self,
            key: str,
            json: JSON,
            evaluatefn: Callable[[JSONInstance], None],
            *,
            extendpath: bool = True,
    ) -> Optional[JSONInstance]:
        self.children[key] = (child := JSONInstance(
            json=json,
            path=self.path / key if extendpath else self.path,
            parent=self,
        ))

        evaluatefn(child)
        if child._valid is not None:
            return child

        del self.children[key]

    def pass_(self, annotation: AnyJSONCompatible = None) -> None:
        self._valid = True
        self.annotation = annotation
        self.error = None

    def fail(self, error: str = None) -> None:
        self._valid = False
        self.annotation = None
        self.error = error

    @property
    def valid(self) -> bool:
        if self._valid is not None:
            return self._valid
        raise JSONSchemaError("Validity unknown")

    @valid.setter
    def valid(self, value: bool) -> None:
        self._valid = value

    def __str__(self) -> str:
        return f'{self.path}: {self.json}'

    def __repr__(self) -> str:
        return f'JSONInstance({self})'
