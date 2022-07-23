import re
from decimal import Decimal, InvalidOperation

from jschon.json import JSON
from jschon.jsonschema import JSONSchema, Result
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

    def evaluate(self, instance: JSON, result: Result) -> None:
        types = tuplify(self.json.data)
        if instance.type in types:
            valid = True
        elif instance.type == "number" and "integer" in types:
            valid = instance.data == int(instance.data)
        else:
            valid = False

        if not valid:
            result.fail(f"The instance must be of type {self.json}")


class EnumKeyword(Keyword):
    key = "enum"

    def evaluate(self, instance: JSON, result: Result) -> None:
        if instance not in self.json:
            result.fail("The instance value must be equal to one of the elements "
                        "in the defined enumeration")


class ConstKeyword(Keyword):
    key = "const"

    def evaluate(self, instance: JSON, result: Result) -> None:
        if instance != self.json:
            result.fail(f"The instance value must be equal to the defined constant")


class MultipleOfKeyword(Keyword):
    key = "multipleOf"
    instance_types = "number",

    def evaluate(self, instance: JSON, result: Result) -> None:
        try:
            if Decimal(f'{instance.data}') % Decimal(f'{self.json.data}') != 0:
                result.fail(f"The value must be a multiple of {self.json}")
        except InvalidOperation:
            result.fail(f"Invalid operation: {instance} % {self.json}")


class MaximumKeyword(Keyword):
    key = "maximum"
    instance_types = "number",

    def evaluate(self, instance: JSON, result: Result) -> None:
        if instance > self.json:
            result.fail(f"The value may not be greater than {self.json}")


class ExclusiveMaximumKeyword(Keyword):
    key = "exclusiveMaximum"
    instance_types = "number",

    def evaluate(self, instance: JSON, result: Result) -> None:
        if instance >= self.json:
            result.fail(f"The value must be less than {self.json}")


class MinimumKeyword(Keyword):
    key = "minimum"
    instance_types = "number",

    def evaluate(self, instance: JSON, result: Result) -> None:
        if instance < self.json:
            result.fail(f"The value may not be less than {self.json}")


class ExclusiveMinimumKeyword(Keyword):
    key = "exclusiveMinimum"
    instance_types = "number",

    def evaluate(self, instance: JSON, result: Result) -> None:
        if instance <= self.json:
            result.fail(f"The value must be greater than {self.json}")


class MaxLengthKeyword(Keyword):
    key = "maxLength"
    instance_types = "string",

    def evaluate(self, instance: JSON, result: Result) -> None:
        if len(instance) > self.json:
            result.fail(f"The text is too long (maximum {self.json} characters)")


class MinLengthKeyword(Keyword):
    key = "minLength"
    instance_types = "string",

    def evaluate(self, instance: JSON, result: Result) -> None:
        if len(instance) < self.json:
            result.fail(f"The text is too short (minimum {self.json} characters)")


class PatternKeyword(Keyword):
    key = "pattern"
    instance_types = "string",

    def __init__(self, parentschema: JSONSchema, value: str):
        super().__init__(parentschema, value)
        self.regex = re.compile(value)

    def evaluate(self, instance: JSON, result: Result) -> None:
        if self.regex.search(instance.data) is None:
            result.fail(f"The text must match the regular expression {self.json}")


class MaxItemsKeyword(Keyword):
    key = "maxItems"
    instance_types = "array",

    def evaluate(self, instance: JSON, result: Result) -> None:
        if len(instance) > self.json:
            result.fail(f"The array has too many elements (maximum {self.json})")


class MinItemsKeyword(Keyword):
    key = "minItems"
    instance_types = "array",

    def evaluate(self, instance: JSON, result: Result) -> None:
        if len(instance) < self.json:
            result.fail(f"The array has too few elements (minimum {self.json})")


class UniqueItemsKeyword(Keyword):
    key = "uniqueItems"
    instance_types = "array",

    def evaluate(self, instance: JSON, result: Result) -> None:
        if not self.json.data:
            return

        uniquified = []
        for item in instance:
            if item not in uniquified:
                uniquified += [item]

        if len(instance) > len(uniquified):
            result.fail("The array's elements must all be unique")


class MaxContainsKeyword(Keyword):
    key = "maxContains"
    instance_types = "array",
    depends_on = "contains",

    def evaluate(self, instance: JSON, result: Result) -> None:
        if contains := result.sibling(instance, "contains"):
            if contains.annotation is not None and len(contains.annotation) > self.json:
                result.fail('The array has too many elements matching the '
                            f'"contains" subschema (maximum {self.json})')


class MinContainsKeyword(Keyword):
    key = "minContains"
    instance_types = "array",
    depends_on = "contains", "maxContains",

    def evaluate(self, instance: JSON, result: Result) -> None:
        if contains := result.sibling(instance, "contains"):
            contains_count = len(contains.annotation) \
                if contains.annotation is not None \
                else 0

            valid = contains_count >= self.json

            if valid and not contains.valid:
                max_contains = result.sibling(instance, "maxContains")
                if not max_contains or max_contains.valid:
                    contains.pass_()

            if not valid:
                result.fail('The array has too few elements matching the '
                            f'"contains" subschema (minimum {self.json})')


class MaxPropertiesKeyword(Keyword):
    key = "maxProperties"
    instance_types = "object",

    def evaluate(self, instance: JSON, result: Result) -> None:
        if len(instance) > self.json:
            result.fail(f"The object has too many properties (maximum {self.json})")


class MinPropertiesKeyword(Keyword):
    key = "minProperties"
    instance_types = "object",

    def evaluate(self, instance: JSON, result: Result) -> None:
        if len(instance) < self.json:
            result.fail(f"The object has too few properties (minimum {self.json})")


class RequiredKeyword(Keyword):
    key = "required"
    instance_types = "object",

    def evaluate(self, instance: JSON, result: Result) -> None:
        missing = [name.value for name in self.json if name.data not in instance]
        if missing:
            result.fail(f"The object is missing required properties {missing}")


class DependentRequiredKeyword(Keyword):
    key = "dependentRequired"
    instance_types = "object",

    def evaluate(self, instance: JSON, result: Result) -> None:
        missing = {}
        for name, dependents in self.json.items():
            if name in instance:
                missing_deps = [dep for dep in dependents if dep.data not in instance]
                if missing_deps:
                    missing[name] = missing_deps

        if missing:
            result.fail(f"The object is missing dependent properties {missing}")
