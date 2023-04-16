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
        URI('https://json-schema.org/draft/2020-12/'),
        LocalSource(pathlib.Path(__file__).parent / 'json-schema-2020-12', suffix='.json'),
    )

    catalog.create_vocabulary(
        URI("https://json-schema.org/draft/2020-12/vocab/core"),
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
        URI("https://json-schema.org/draft/2020-12/vocab/applicator"),
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
        ContainsKeyword_2019_09,
        PropertiesKeyword,
        PatternPropertiesKeyword,
        AdditionalPropertiesKeyword,
        PropertyNamesKeyword,
    )

    catalog.create_vocabulary(
        URI("https://json-schema.org/draft/2020-12/vocab/unevaluated"),
        UnevaluatedItemsKeyword,
        UnevaluatedPropertiesKeyword_2019_09,
    )

    catalog.create_vocabulary(
        URI("https://json-schema.org/draft/2020-12/vocab/validation"),
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
        MaxContainsKeyword_2019_09,
        MinContainsKeyword_2019_09,
        MaxPropertiesKeyword,
        MinPropertiesKeyword,
        RequiredKeyword,
        DependentRequiredKeyword,
    )

    catalog.create_vocabulary(
        URI("https://json-schema.org/draft/2020-12/vocab/format-annotation"),
        FormatKeyword,
    )

    catalog.create_vocabulary(
        URI("https://json-schema.org/draft/2020-12/vocab/meta-data"),
        TitleKeyword,
        DescriptionKeyword,
        DefaultKeyword,
        DeprecatedKeyword,
        ReadOnlyKeyword,
        WriteOnlyKeyword,
        ExamplesKeyword,
    )

    catalog.create_vocabulary(
        URI("https://json-schema.org/draft/2020-12/vocab/content"),
        ContentMediaTypeKeyword,
        ContentEncodingKeyword,
        ContentSchemaKeyword,
    )
