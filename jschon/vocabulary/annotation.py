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
    'ContentMediaTypeKeyword',
    'ContentEncodingKeyword',
    'ContentSchemaKeyword',
]


class AnnotationKeyword(Keyword):

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        scope.annotate(instance, self.key, self.json.value)
        scope.noassert()


class TitleKeyword(AnnotationKeyword):
    key = "title"


class DescriptionKeyword(AnnotationKeyword):
    key = "description"


class DefaultKeyword(AnnotationKeyword):
    key = "default"


class DeprecatedKeyword(AnnotationKeyword):
    key = "deprecated"


class ReadOnlyKeyword(AnnotationKeyword):
    key = "readOnly"


class WriteOnlyKeyword(AnnotationKeyword):
    key = "writeOnly"


class ExamplesKeyword(AnnotationKeyword):
    key = "examples"


class ContentMediaTypeKeyword(AnnotationKeyword):
    key = "contentMediaType"
    types = "string"


class ContentEncodingKeyword(AnnotationKeyword):
    key = "contentEncoding"
    types = "string"


class ContentSchemaKeyword(AnnotationKeyword):
    key = "contentSchema"
    types = "string"
    depends = "contentMediaType"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        if scope.sibling("contentMediaType"):
            super().evaluate(instance, scope)
        else:
            scope.discard()
