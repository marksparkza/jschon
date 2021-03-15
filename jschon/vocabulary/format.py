from typing import Callable, Dict, Mapping

from jschon.json import AnyJSONCompatible, JSON
from jschon.jsonschema import Keyword, JSONSchema, Scope

__all__ = [
    'FormatKeyword',
]

FormatValidator = Callable[[AnyJSONCompatible], None]


class FormatKeyword(Keyword):
    __keyword__ = "format"
    __schema__ = {"type": "string"}

    _validators: Dict[str, FormatValidator] = {}

    @classmethod
    def register_validators(cls, validators: Mapping[str, FormatValidator]):
        cls._validators.update(validators)

    def __init__(self, parentschema: JSONSchema, value: str):
        super().__init__(parentschema, value)
        self.validator: FormatValidator = self._validators.get(value)

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        scope.annotate(instance, "format", self.json.value)
        if self.validator is not None:
            try:
                self.validator(instance.value)
            except ValueError as e:
                scope.fail(instance, f'The instance is invalid against the "{self.json.value}" format: {e}')
