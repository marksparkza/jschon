from jschon.json import JSON
from jschon.jsonschema import Keyword, Scope

__all__ = [
    'ContentMediaTypeKeyword',
    'ContentEncodingKeyword',
    'ContentSchemaKeyword',
]


class ContentMediaTypeKeyword(Keyword):
    __keyword__ = "contentMediaType"
    __schema__ = {"type": "string"}

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        scope.annotate(instance, "contentMediaType", self.json.value)


class ContentEncodingKeyword(Keyword):
    __keyword__ = "contentEncoding"
    __schema__ = {"type": "string"}

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        scope.annotate(instance, "contentEncoding", self.json.value)


class ContentSchemaKeyword(Keyword):
    __keyword__ = "contentSchema"
    __schema__ = {"$recursiveRef": "#"}
    __depends__ = "contentMediaType"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        scope.annotate(instance, "contentSchema", self.json.value)
