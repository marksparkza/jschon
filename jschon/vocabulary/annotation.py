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


class AnnotationKeyword(Keyword):

    def evaluate(self, instance: JSON, result: Result) -> None:
        result.annotate(self.json.data)
        result.noassert()


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
    instance_types = "string",


class ContentEncodingKeyword(AnnotationKeyword):
    key = "contentEncoding"
    instance_types = "string",


class ContentSchemaKeyword(AnnotationKeyword):
    key = "contentSchema"
    instance_types = "string",
    depends_on = "contentMediaType",

    def evaluate(self, instance: JSON, result: Result) -> None:
        if result.sibling(instance, "contentMediaType"):
            super().evaluate(instance, result)
        else:
            result.discard()
