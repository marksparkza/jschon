import pathlib

from jschon.catalog import Catalog, LocalSource
from jschon.uri import URI
from jschon.vocabulary.annotation import *
from jschon.vocabulary.applicator import *
from jschon.vocabulary.core import *
from jschon.vocabulary.format import *
from jschon.vocabulary.validation import *


def initialize(catalog: Catalog):
    catalog.add_uri_source(
        URI('https://json-schema.org/draft/next/'),
        LocalSource(pathlib.Path(__file__).parent / 'json-schema-next', suffix='.json'),
    )

    catalog.create_vocabulary(
        URI("https://json-schema.org/draft/next/vocab/core"),
        SchemaKeyword,
        VocabularyKeyword,
        IdKeyword,
        RefKeyword,
        AnchorKeyword,
        DynamicRefKeyword,
        DynamicAnchorKeyword,
        DefsKeyword,
        CommentKeyword,
    )

    catalog.create_vocabulary(
        URI("https://json-schema.org/draft/next/vocab/applicator"),
        AllOfKeyword,
        AnyOfKeyword,
        OneOfKeyword,
        NotKeyword,
        IfKeyword,
        ThenKeyword,
        ElseKeyword,
        DependentSchemasKeyword,
        PrefixItemsKeyword,
        ItemsKeyword,
        ContainsKeyword_Next,
        MaxContainsKeyword_Next,
        MinContainsKeyword_Next,
        PropertiesKeyword,
        PatternPropertiesKeyword,
        AdditionalPropertiesKeyword,
        PropertyNamesKeyword,
    )

    catalog.create_vocabulary(
        URI("https://json-schema.org/draft/next/vocab/unevaluated"),
        UnevaluatedItemsKeyword,
        UnevaluatedPropertiesKeyword_Next,
    )

    catalog.create_vocabulary(
        URI("https://json-schema.org/draft/next/vocab/validation"),
        TypeKeyword,
        EnumKeyword,
        ConstKeyword,
        MultipleOfKeyword,
        MaximumKeyword,
        ExclusiveMaximumKeyword,
        MinimumKeyword,
        ExclusiveMinimumKeyword,
        MaxLengthKeyword,
        MinLengthKeyword,
        PatternKeyword,
        MaxItemsKeyword,
        MinItemsKeyword,
        UniqueItemsKeyword,
        MaxPropertiesKeyword,
        MinPropertiesKeyword,
        RequiredKeyword,
        DependentRequiredKeyword,
    )

    catalog.create_vocabulary(
        URI("https://json-schema.org/draft/next/vocab/format-annotation"),
        FormatKeyword,
    )

    catalog.create_vocabulary(
        URI("https://json-schema.org/draft/next/vocab/meta-data"),
        TitleKeyword,
        DescriptionKeyword,
        DefaultKeyword,
        DeprecatedKeyword,
        ReadOnlyKeyword,
        WriteOnlyKeyword,
        ExamplesKeyword,
    )

    catalog.create_vocabulary(
        URI("https://json-schema.org/draft/next/vocab/content"),
        ContentMediaTypeKeyword,
        ContentEncodingKeyword,
        ContentSchemaKeyword,
    )
