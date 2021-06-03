from typing import Callable

from jschon.exceptions import CatalogueError
from jschon.json import AnyJSONCompatible, JSON
from jschon.jsonschema import JSONSchema, Scope
from jschon.vocabulary import Keyword

__all__ = [
    'FormatKeyword',
    'FormatValidator',
]

FormatValidator = Callable[[AnyJSONCompatible], None]
"""The type of a ``"format"`` keyword validator.

A :class:`~jschon.vocabulary.format.FormatValidator` is a
callable accepting a JSON-compatible Python object as its
only argument. It must raise a :exc:`ValueError` if the
argument is invalid per the applicable format specification.
"""


class FormatKeyword(Keyword):
    key = "format"

    def __init__(self, parentschema: JSONSchema, value: str):
        super().__init__(parentschema, value)

        try:
            self.validator: FormatValidator = parentschema.catalogue.get_format_validator(value)
        except CatalogueError:
            self.validator = None

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        scope.annotate(self.json.value)
        if self.validator is not None:
            try:
                self.validator(instance.value)
            except ValueError as e:
                scope.fail(f'The instance is invalid against the "{self.json.value}" format: {e}')
        else:
            scope.noassert()
