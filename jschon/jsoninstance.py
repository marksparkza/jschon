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
            evaluator: Callable[[JSONInstance], None],
            *,
            dynamicpath: JSONPointer = None,
            parent: JSONInstance = None,
    ):
        self.json: AnyJSON = json
        self.evaluator: Callable[[JSONInstance], None] = evaluator
        self.dynamicpath: JSONPointer = dynamicpath or JSONPointer()
        self.parent: Optional[JSONInstance] = parent
        self.children: Dict[str, JSONInstance] = {}
        self._valid: Optional[bool] = None
        self.annotation: Optional[AnyJSONCompatible] = None
        self.error: Optional[str] = None
        self.assert_: bool = True
        self._childkey: int = 0
        self.evaluator(self)

    def sibling(self, key: str) -> Optional[JSONInstance]:
        return self.parent.children.get(key) if self.parent else None

    def descend(
            self,
            json: JSON,
            evaluator: Callable[[JSONInstance], None],
            *,
            key: str = None,
    ) -> Optional[JSONInstance]:
        child = JSONInstance(
            json=json,
            evaluator=evaluator,
            dynamicpath=self.dynamicpath / key if key is not None else self.dynamicpath,
            parent=self,
        )
        if child._valid is not None:
            if key is None:
                key = str(self._childkey)
                self._childkey += 1
            self.children[key] = child
            return child

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
        return f'{self.dynamicpath}: {self.json}'

    def __repr__(self) -> str:
        return f'JSONInstance({self})'
