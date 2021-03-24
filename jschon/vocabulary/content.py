from jschon.json import JSON
from jschon.jsonschema import Keyword, Scope

__all__ = [
    'ContentMediaTypeKeyword',
    'ContentEncodingKeyword',
    'ContentSchemaKeyword',
]


class ContentMediaTypeKeyword(Keyword):

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        scope.annotate(instance, "contentMediaType", self.json.value)


class ContentEncodingKeyword(Keyword):

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        scope.annotate(instance, "contentEncoding", self.json.value)


class ContentSchemaKeyword(Keyword):

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        scope.annotate(instance, "contentSchema", self.json.value)
