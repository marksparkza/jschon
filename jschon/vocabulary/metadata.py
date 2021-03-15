from jschon.json import JSON
from jschon.jsonschema import Keyword, Scope

__all__ = [
    'TitleKeyword',
    'DescriptionKeyword',
    'DefaultKeyword',
    'DeprecatedKeyword',
    'ReadOnlyKeyword',
    'WriteOnlyKeyword',
    'ExamplesKeyword',
]


class TitleKeyword(Keyword):
    __keyword__ = "title"
    __schema__ = {"type": "string"}

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        scope.annotate(instance, "title", self.json.value)


class DescriptionKeyword(Keyword):
    __keyword__ = "description"
    __schema__ = {"type": "string"}

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        scope.annotate(instance, "description", self.json.value)


class DefaultKeyword(Keyword):
    __keyword__ = "default"
    __schema__ = True

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        scope.annotate(instance, "default", self.json.value)


class DeprecatedKeyword(Keyword):
    __keyword__ = "deprecated"
    __schema__ = {
        "type": "boolean",
        "default": False
    }

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        scope.annotate(instance, "deprecated", self.json.value)


class ReadOnlyKeyword(Keyword):
    __keyword__ = "readOnly"
    __schema__ = {
        "type": "boolean",
        "default": False
    }

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        scope.annotate(instance, "readOnly", self.json.value)


class WriteOnlyKeyword(Keyword):
    __keyword__ = "writeOnly"
    __schema__ = {
        "type": "boolean",
        "default": False
    }

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        scope.annotate(instance, "writeOnly", self.json.value)


class ExamplesKeyword(Keyword):
    __keyword__ = "examples"
    __schema__ = {
        "type": "array",
        "items": True
    }

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        scope.annotate(instance, "examples", self.json.value)
