import decimal
import re

from jschon.json import JSON
from jschon.jsonschema import Scope, JSONSchema
from jschon.utils import tuplify
from jschon.vocabulary import Keyword

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
    'MaxContainsKeyword',
    'MinContainsKeyword',
    'MaxPropertiesKeyword',
    'MinPropertiesKeyword',
    'RequiredKeyword',
    'DependentRequiredKeyword',
]


class TypeKeyword(Keyword):
    key = "type"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        types = tuplify(self.json.value)
        if instance.type in types:
            valid = True
        elif instance.type == "number" and "integer" in types:
            valid = instance.value == int(instance.value)
        else:
            valid = False

        if not valid:
            scope.fail(f"The instance must be of type {self.json}")


class EnumKeyword(Keyword):
    key = "enum"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        if instance not in self.json:
            scope.fail(f"The value must be one of {self.json}")


class ConstKeyword(Keyword):
    key = "const"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        if instance != self.json:
            scope.fail(f"The value must be equal to {self.json}")


class MultipleOfKeyword(Keyword):
    key = "multipleOf"
    types = "number"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        try:
            if instance.value % self.json.value != 0:
                scope.fail(f"The value must be a multiple of {self.json}")
        except decimal.InvalidOperation:
            scope.fail(f"Invalid operation: {instance} % {self.json}")


class MaximumKeyword(Keyword):
    key = "maximum"
    types = "number"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        if instance > self.json:
            scope.fail(f"The value may not be greater than {self.json}")


class ExclusiveMaximumKeyword(Keyword):
    key = "exclusiveMaximum"
    types = "number"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        if instance >= self.json:
            scope.fail(f"The value must be less than {self.json}")


class MinimumKeyword(Keyword):
    key = "minimum"
    types = "number"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        if instance < self.json:
            scope.fail(f"The value may not be less than {self.json}")


class ExclusiveMinimumKeyword(Keyword):
    key = "exclusiveMinimum"
    types = "number"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        if instance <= self.json:
            scope.fail(f"The value must be greater than {self.json}")


class MaxLengthKeyword(Keyword):
    key = "maxLength"
    types = "string"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        if len(instance) > self.json:
            scope.fail(f"The text is too long (maximum {self.json} characters)")


class MinLengthKeyword(Keyword):
    key = "minLength"
    types = "string"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        if len(instance) < self.json:
            scope.fail(f"The text is too short (minimum {self.json} characters)")


class PatternKeyword(Keyword):
    key = "pattern"
    types = "string"

    def __init__(self, parentschema: JSONSchema, value: str):
        super().__init__(parentschema, value)
        self.regex = re.compile(value)

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        if self.regex.search(instance.value) is None:
            scope.fail(f"The text must match the regular expression {self.json}")


class MaxItemsKeyword(Keyword):
    key = "maxItems"
    types = "array"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        if len(instance) > self.json:
            scope.fail(f"The array has too many elements (maximum {self.json})")


class MinItemsKeyword(Keyword):
    key = "minItems"
    types = "array"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        if len(instance) < self.json:
            scope.fail(f"The array has too few elements (minimum {self.json})")


class UniqueItemsKeyword(Keyword):
    key = "uniqueItems"
    types = "array"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        if not self.json.value:
            return

        uniquified = []
        for item in instance:
            if item not in uniquified:
                uniquified += [item]

        if len(instance) > len(uniquified):
            scope.fail("The array's elements must all be unique")


class MaxContainsKeyword(Keyword):
    key = "maxContains"
    types = "array"
    depends = "contains"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        if contains := scope.sibling(instance, "contains"):
            if contains.annotation is not None and len(contains.annotation) > self.json:
                scope.fail('The array has too many elements matching the '
                           f'"contains" subschema (maximum {self.json})')


class MinContainsKeyword(Keyword):
    key = "minContains"
    types = "array"
    depends = "contains", "maxContains"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        if contains := scope.sibling(instance, "contains"):
            contains_count = len(contains.annotation) \
                if contains.annotation is not None \
                else 0

            valid = contains_count >= self.json

            if valid and not contains.valid:
                max_contains = scope.sibling(instance, "maxContains")
                if not max_contains or max_contains.valid:
                    contains.pass_()

            if not valid:
                scope.fail('The array has too few elements matching the '
                           f'"contains" subschema (minimum {self.json})')


class MaxPropertiesKeyword(Keyword):
    key = "maxProperties"
    types = "object"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        if len(instance) > self.json:
            scope.fail(f"The object has too many properties (maximum {self.json})")


class MinPropertiesKeyword(Keyword):
    key = "minProperties"
    types = "object"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        if len(instance) < self.json:
            scope.fail(f"The object has too few properties (minimum {self.json})")


class RequiredKeyword(Keyword):
    key = "required"
    types = "object"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        missing = [name for name in self.json if name.value not in instance]
        if missing:
            scope.fail(f"The object is missing required properties {missing}")


class DependentRequiredKeyword(Keyword):
    key = "dependentRequired"
    types = "object"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        missing = {}
        for name, dependents in self.json.items():
            if name in instance:
                missing_deps = [dep for dep in dependents if dep.value not in instance]
                if missing_deps:
                    missing[name] = missing_deps

        if missing:
            scope.fail(f"The object is missing dependent properties {missing}")
