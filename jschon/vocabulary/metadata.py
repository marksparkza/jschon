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

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        scope.annotate(instance, "title", self.json.value)


class DescriptionKeyword(Keyword):

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        scope.annotate(instance, "description", self.json.value)


class DefaultKeyword(Keyword):

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        scope.annotate(instance, "default", self.json.value)


class DeprecatedKeyword(Keyword):

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        scope.annotate(instance, "deprecated", self.json.value)


class ReadOnlyKeyword(Keyword):

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        scope.annotate(instance, "readOnly", self.json.value)


class WriteOnlyKeyword(Keyword):

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        scope.annotate(instance, "writeOnly", self.json.value)


class ExamplesKeyword(Keyword):

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        scope.annotate(instance, "examples", self.json.value)
