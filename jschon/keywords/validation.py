import re
import typing as _t

from jschon.json import *
from jschon.schema import KeywordResult, Keyword, Schema

__all__ = [
    'TypeKeyword',
    'EnumKeyword',
    'ConstKeyword',
    'MultipleOfKeyword',
    'MaximumKeyword',
    'ExclusiveMaximumKeyword',
    'MinimumKeyword',
    'ExclusiveMinimumKeyword',
    'MaxLengthKeyword',
    'MinLengthKeyword',
    'PatternKeyword',
    'MaxItemsKeyword',
    'MinItemsKeyword',
    'UniqueItemsKeyword',
]


class TypeKeyword(Keyword):
    __keyword__ = "type"
    __schema__ = {
        "anyOf": [
            {"enum": ["null", "boolean", "number", "integer", "string", "array", "object"]},
            {
                "type": "array",
                "items": {"enum": ["null", "boolean", "number", "integer", "string", "array", "object"]},
                "minItems": 1,
                "uniqueItems": True
            }
        ]
    }
    __types__ = JSON

    def __init__(
            self,
            superschema: Schema,
            value: _t.Union[str, _t.Sequence[str]],
    ) -> None:
        if isinstance(value, str):
            value = [value]
        super().__init__(superschema, value)

    def evaluate(self, instance: JSON) -> KeywordResult:
        return KeywordResult(
            valid=(valid := instance.jsontype in self.value),
            error=f"The value must be of type {self.value}" if not valid else None,
        )


class EnumKeyword(Keyword):
    __keyword__ = "enum"
    __schema__ = {"type": "array", "items": True}
    __types__ = JSON

    def evaluate(self, instance: JSON) -> KeywordResult:
        return KeywordResult(
            valid=(valid := instance.value in self.value),
            error=f"The value must be one of {self.value}" if not valid else None,
        )


class ConstKeyword(Keyword):
    __keyword__ = "const"
    __schema__ = True
    __types__ = JSON

    def evaluate(self, instance: JSON) -> KeywordResult:
        return KeywordResult(
            valid=(valid := instance.value == self.value),
            error=f"The value must be equal to {self.value}" if not valid else None,
        )


class MultipleOfKeyword(Keyword):
    __keyword__ = "multipleOf"
    __schema__ = {"type": "number", "exclusiveMinimum": 0}
    __types__ = JSONNumber

    def evaluate(self, instance: JSONNumber) -> KeywordResult:
        return KeywordResult(
            valid=(valid := instance.value % self.value == 0),
            error=f"The value must be a multiple of {self.value}" if not valid else None,
        )


class MaximumKeyword(Keyword):
    __keyword__ = "maximum"
    __schema__ = {"type": "number"}
    __types__ = JSONNumber

    def evaluate(self, instance: JSONNumber) -> KeywordResult:
        return KeywordResult(
            valid=(valid := instance.value <= self.value),
            error=f"The value may not be greater than {self.value}" if not valid else None,
        )


class ExclusiveMaximumKeyword(Keyword):
    __keyword__ = "exclusiveMaximum"
    __schema__ = {"type": "number"}
    __types__ = JSONNumber

    def evaluate(self, instance: JSONNumber) -> KeywordResult:
        return KeywordResult(
            valid=(valid := instance.value < self.value),
            error=f"The value must be less than {self.value}" if not valid else None,
        )


class MinimumKeyword(Keyword):
    __keyword__ = "minimum"
    __schema__ = {"type": "number"}
    __types__ = JSONNumber

    def evaluate(self, instance: JSONNumber) -> KeywordResult:
        return KeywordResult(
            valid=(valid := instance.value >= self.value),
            error=f"The value may not be less than {self.value}" if not valid else None,
        )


class ExclusiveMinimumKeyword(Keyword):
    __keyword__ = "exclusiveMinimum"
    __schema__ = {"type": "number"}
    __types__ = JSONNumber

    def evaluate(self, instance: JSONNumber) -> KeywordResult:
        return KeywordResult(
            valid=(valid := instance.value > self.value),
            error=f"The value must be greater than {self.value}" if not valid else None,
        )


class MaxLengthKeyword(Keyword):
    __keyword__ = "maxLength"
    __schema__ = {"type": "integer", "minimum": 0}
    __types__ = JSONString

    def evaluate(self, instance: JSONString) -> KeywordResult:
        return KeywordResult(
            valid=(valid := len(instance.value) <= self.value),
            error=f"The text is too long (maximum {self.value} characters)" if not valid else None,
        )


class MinLengthKeyword(Keyword):
    __keyword__ = "minLength"
    __schema__ = {"type": "integer", "minimum": 0}
    __types__ = JSONString

    def evaluate(self, instance: JSONString) -> KeywordResult:
        return KeywordResult(
            valid=(valid := len(instance.value) >= self.value),
            error=f"The text is too short (minimum {self.value} characters)" if not valid else None,
        )


class PatternKeyword(Keyword):
    __keyword__ = "pattern"
    __schema__ = {"type": "string", "format": "regex"}
    __types__ = JSONString

    def __init__(
            self,
            superschema: Schema,
            value: str,
    ) -> None:
        super().__init__(superschema, value)
        self.regex = re.compile(value)

    def evaluate(self, instance: JSONString) -> KeywordResult:
        return KeywordResult(
            valid=(valid := self.regex.search(instance.value) is not None),
            error=f"The text must match the regular expression {self.value}" if not valid else None,
        )


class MaxItemsKeyword(Keyword):
    __keyword__ = "maxItems"
    __schema__ = {"type": "integer", "minimum": 0}
    __types__ = JSONArray

    def evaluate(self, instance: JSONArray) -> KeywordResult:
        return KeywordResult(
            valid=(valid := len(instance.value) <= self.value),
            error=f"The array has too many elements (maximum {self.value})" if not valid else None,
        )


class MinItemsKeyword(Keyword):
    __keyword__ = "minItems"
    __schema__ = {"type": "integer", "minimum": 0}
    __types__ = JSONArray

    def evaluate(self, instance: JSONArray) -> KeywordResult:
        return KeywordResult(
            valid=(valid := len(instance.value) >= self.value),
            error=f"The array has too few elements (minimum {self.value})" if not valid else None,
        )


class UniqueItemsKeyword(Keyword):
    __keyword__ = "uniqueItems"
    __schema__ = {"type": "boolean"}
    __types__ = JSONArray

    def evaluate(self, instance: JSONArray) -> KeywordResult:
        try:
            uniquified = set(instance.value)
        except TypeError:  # unhashable type
            uniquified = []
            for item in instance.value:
                if item not in uniquified:
                    uniquified += [item]

        return KeywordResult(
            valid=(valid := not self.value or len(instance.value) == len(uniquified)),
            error="The array's elements must all be unique'" if not valid else None,
        )
