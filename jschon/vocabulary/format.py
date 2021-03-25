from typing import Callable, Any

from jschon.exceptions import CatalogueError
from jschon.json import AnyJSONCompatible, JSON
from jschon.jsonschema import Keyword, JSONSchema, Scope

__all__ = [
    'FormatKeyword',
    'FormatValidator',
]

FormatValidator = Callable[[AnyJSONCompatible], None]


class FormatKeyword(Keyword):

    def __init__(
            self,
            parentschema: JSONSchema,
            key: str,
            value: str,
            *args: Any,
            **kwargs: Any,
    ):
        super().__init__(parentschema, key, value, *args, **kwargs)

        from jschon.catalogue import Catalogue
        try:
            self.validator: FormatValidator = Catalogue.get_format_validator(value)
        except CatalogueError:
            self.validator = None

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        scope.annotate(instance, self.key, self.json.value)
        if self.validator is not None:
            try:
                self.validator(instance.value)
            except ValueError as e:
                scope.fail(instance, f'The instance is invalid against the "{self.json.value}" format: {e}')
        else:
            scope.noassert()
