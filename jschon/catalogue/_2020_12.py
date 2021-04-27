import pathlib

from jschon.uri import URI
from jschon.vocabulary.annotation import *
from jschon.vocabulary.applicator import *
from jschon.vocabulary.core import *
from jschon.vocabulary.format import *
from jschon.vocabulary.validation import *


def initialize(catalogue):
    catalogue.add_directory(
        URI('https://json-schema.org/draft/2020-12/'),
        pathlib.Path(__file__).parent / 'json-schema-spec-2020-12',
    )

    catalogue.create_vocabulary(
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

    catalogue.create_vocabulary(
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
        ContainsKeyword,
        PropertiesKeyword,
        PatternPropertiesKeyword,
        AdditionalPropertiesKeyword,
        PropertyNamesKeyword,
    )

    catalogue.create_vocabulary(
        URI("https://json-schema.org/draft/2020-12/vocab/unevaluated"),
        UnevaluatedItemsKeyword,
        UnevaluatedPropertiesKeyword,
    )

    catalogue.create_vocabulary(
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
        MaxContainsKeyword,
        MinContainsKeyword,
        MaxPropertiesKeyword,
        MinPropertiesKeyword,
        RequiredKeyword,
        DependentRequiredKeyword,
    )

    catalogue.create_vocabulary(
        URI("https://json-schema.org/draft/2020-12/vocab/format-annotation"),
        FormatKeyword,
    )

    catalogue.create_vocabulary(
        URI("https://json-schema.org/draft/2020-12/vocab/meta-data"),
        TitleKeyword,
        DescriptionKeyword,
        DefaultKeyword,
        DeprecatedKeyword,
        ReadOnlyKeyword,
        WriteOnlyKeyword,
        ExamplesKeyword,
    )

    catalogue.create_vocabulary(
        URI("https://json-schema.org/draft/2020-12/vocab/content"),
        ContentMediaTypeKeyword,
        ContentEncodingKeyword,
        ContentSchemaKeyword,
    )

    catalogue.create_metaschema(
        URI("https://json-schema.org/draft/2020-12/schema"),
        URI("https://json-schema.org/draft/2020-12/vocab/core"),
        URI("https://json-schema.org/draft/2020-12/vocab/applicator"),
        URI("https://json-schema.org/draft/2020-12/vocab/unevaluated"),
        URI("https://json-schema.org/draft/2020-12/vocab/validation"),
        URI("https://json-schema.org/draft/2020-12/vocab/format-annotation"),
        URI("https://json-schema.org/draft/2020-12/vocab/meta-data"),
        URI("https://json-schema.org/draft/2020-12/vocab/content"),
    )
