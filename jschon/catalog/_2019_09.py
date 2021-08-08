import pathlib

from jschon.uri import URI
from jschon.vocabulary.annotation import *
from jschon.vocabulary.applicator import *
from jschon.vocabulary.core import *
from jschon.vocabulary.format import *
from jschon.vocabulary.legacy import *
from jschon.vocabulary.validation import *


def initialize(catalog):
    catalog.add_directory(
        URI('https://json-schema.org/draft/2019-09/'),
        pathlib.Path(__file__).parent / 'json-schema-spec-2019-09',
    )

    catalog.create_vocabulary(
        URI("https://json-schema.org/draft/2019-09/vocab/core"),
        SchemaKeyword,
        VocabularyKeyword,
        IdKeyword,
        RefKeyword,
        AnchorKeyword,
        RecursiveRefKeyword_2019_09,
        RecursiveAnchorKeyword_2019_09,
        DefsKeyword,
        CommentKeyword,
    )

    catalog.create_vocabulary(
        URI("https://json-schema.org/draft/2019-09/vocab/applicator"),
        AllOfKeyword,
        AnyOfKeyword,
        OneOfKeyword,
        NotKeyword,
        IfKeyword,
        ThenKeyword,
        ElseKeyword,
        DependentSchemasKeyword,
        ItemsKeyword_2019_09,
        AdditionalItemsKeyword_2019_09,
        UnevaluatedItemsKeyword_2019_09,
        ContainsKeyword,
        PropertiesKeyword,
        PatternPropertiesKeyword,
        AdditionalPropertiesKeyword,
        UnevaluatedPropertiesKeyword,
        PropertyNamesKeyword,
    )

    catalog.create_vocabulary(
        URI("https://json-schema.org/draft/2019-09/vocab/validation"),
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

    catalog.create_vocabulary(
        URI("https://json-schema.org/draft/2019-09/vocab/format"),
        FormatKeyword,
    )

    catalog.create_vocabulary(
        URI("https://json-schema.org/draft/2019-09/vocab/meta-data"),
        TitleKeyword,
        DescriptionKeyword,
        DefaultKeyword,
        DeprecatedKeyword,
        ReadOnlyKeyword,
        WriteOnlyKeyword,
        ExamplesKeyword,
    )

    catalog.create_vocabulary(
        URI("https://json-schema.org/draft/2019-09/vocab/content"),
        ContentMediaTypeKeyword,
        ContentEncodingKeyword,
        ContentSchemaKeyword,
    )

    catalog.create_metaschema(
        URI("https://json-schema.org/draft/2019-09/schema"),
        URI("https://json-schema.org/draft/2019-09/vocab/core"),
        URI("https://json-schema.org/draft/2019-09/vocab/applicator"),
        URI("https://json-schema.org/draft/2019-09/vocab/validation"),
        URI("https://json-schema.org/draft/2019-09/vocab/format"),
        URI("https://json-schema.org/draft/2019-09/vocab/meta-data"),
        URI("https://json-schema.org/draft/2019-09/vocab/content"),
    )
