from __future__ import annotations

from typing import *

from jschon.exceptions import JSONSchemaError
from jschon.json import AnyJSON, JSON
from jschon.jsonpointer import JSONPointer
from jschon.types import AnyJSONCompatible

__all__ = [
    'EvaluationNode',
]


class Annotation(NamedTuple):
    key: str
    value: AnyJSONCompatible


class EvaluationNode(Generic[AnyJSON]):

    def __init__(
            self,
            json: JSON,
            evaluator: Callable[[EvaluationNode], None],
            *,
            path: JSONPointer = None,
            parent: EvaluationNode = None,
    ):
        self.json: AnyJSON = json
        self.evaluator: Callable[[EvaluationNode], None] = evaluator
        self.path: JSONPointer = path or JSONPointer()
        self.parent: Optional[EvaluationNode] = parent
        self.children: Dict[str, EvaluationNode] = {}
        self._valid: Optional[bool] = None
        self._annotation: Optional[Annotation] = None
        self.error: Optional[str] = None
        self.assert_: bool = True
        self._childkey: int = 0
        self.evaluator(self)

    def sibling(self, key: str) -> Optional[EvaluationNode]:
        return self.parent.children.get(key) if self.parent else None

    def descend(
            self,
            json: JSON,
            evaluator: Callable[[EvaluationNode], None],
            *,
            key: str = None,
    ) -> Optional[EvaluationNode]:
        child = EvaluationNode(
            json=json,
            evaluator=evaluator,
            path=self.path / key if key is not None else self.path,
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
        if annotation is not None:
            if hasattr(self.evaluator, '__keyword__'):
                self._annotation = Annotation(self.evaluator.__keyword__, annotation)
            else:
                raise ValueError("annotation can only be set by a keyword")
        else:
            self._annotation = None
        self.error = None

    def fail(self, error: str = None) -> None:
        self._valid = False
        self._annotation = None
        self.error = error

    @property
    def valid(self) -> bool:
        if self._valid is not None:
            return self._valid
        raise JSONSchemaError("Validity unknown")

    @valid.setter
    def valid(self, value: bool) -> None:
        self._valid = value

    @property
    def annotation(self) -> Optional[AnyJSONCompatible]:
        return self._annotation.value if self._annotation else None

    def annotations(self, key: str) -> Iterator[AnyJSONCompatible]:
        """Yield annotations produced by a given keyword in this subtree."""
        if self._valid and self._annotation and self._annotation.key == key:
            yield self._annotation.value
        for child in self.children.values():
            yield from child.annotations(key)

    def __str__(self) -> str:
        """By analogy with Bash input redirection, show which JSON value
        is being input to which evaluator."""
        evalpath = self.path or 'root'
        jsonpath = self.json.path or 'root'
        return f'{evalpath} < {jsonpath}'

    def __repr__(self) -> str:
        return f"EvaluationNode({self.json!r}, {self.evaluator!r})"
