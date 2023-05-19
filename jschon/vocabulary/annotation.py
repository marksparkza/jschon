from jschon.json import JSON
from jschon.jsonschema import Result
from jschon.vocabulary import Keyword

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


class _AnnotationKeyword(Keyword):

    def evaluate(self, instance: JSON, result: Result) -> None:
        result.annotate(self.json.value)
        result.noassert()


class TitleKeyword(_AnnotationKeyword):
    key = "title"


class DescriptionKeyword(_AnnotationKeyword):
    key = "description"


class DefaultKeyword(_AnnotationKeyword):
    key = "default"


class DeprecatedKeyword(_AnnotationKeyword):
    key = "deprecated"


class ReadOnlyKeyword(_AnnotationKeyword):
    key = "readOnly"


class WriteOnlyKeyword(_AnnotationKeyword):
    key = "writeOnly"


class ExamplesKeyword(_AnnotationKeyword):
    key = "examples"


class ContentMediaTypeKeyword(_AnnotationKeyword):
    key = "contentMediaType"
    instance_types = "string",


class ContentEncodingKeyword(_AnnotationKeyword):
    key = "contentEncoding"
    instance_types = "string",


class ContentSchemaKeyword(_AnnotationKeyword):
    key = "contentSchema"
    instance_types = "string",
    depends_on = "contentMediaType",

    def evaluate(self, instance: JSON, result: Result) -> None:
        if result.sibling(instance, "contentMediaType"):
            super().evaluate(instance, result)
        else:
            result.discard()
