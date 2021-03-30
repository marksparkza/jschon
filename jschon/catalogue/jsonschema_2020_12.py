from jschon.catalogue import Catalogue, catalogue_dir
from jschon.uri import URI
from jschon.vocabulary.annotation import *
from jschon.vocabulary.applicator import *
from jschon.vocabulary.core import *
from jschon.vocabulary.format import *
from jschon.vocabulary.validation import *


def initialize():
    Catalogue.add_directory(
        base_uri=URI('https://json-schema.org/draft/2020-12/'),
        base_dir=catalogue_dir / 'json-schema-spec-2020-12',
    )

    Catalogue.create_vocabulary(
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

    Catalogue.create_vocabulary(
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

    Catalogue.create_vocabulary(
        URI("https://json-schema.org/draft/2020-12/vocab/unevaluated"),
        UnevaluatedItemsKeyword,
        UnevaluatedPropertiesKeyword,
    )

    Catalogue.create_vocabulary(
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

    Catalogue.create_vocabulary(
        URI("https://json-schema.org/draft/2020-12/vocab/format-annotation"),
        FormatKeyword,
    )

    Catalogue.create_vocabulary(
        URI("https://json-schema.org/draft/2020-12/vocab/meta-data"),
        TitleKeyword,
        DescriptionKeyword,
        DefaultKeyword,
        DeprecatedKeyword,
        ReadOnlyKeyword,
        WriteOnlyKeyword,
        ExamplesKeyword,
    )

    Catalogue.create_vocabulary(
        URI("https://json-schema.org/draft/2020-12/vocab/content"),
        ContentMediaTypeKeyword,
        ContentEncodingKeyword,
        ContentSchemaKeyword,
    )

    Catalogue.create_metaschema(
        URI("https://json-schema.org/draft/2020-12/schema"),
        URI("https://json-schema.org/draft/2020-12/vocab/core"),
        URI("https://json-schema.org/draft/2020-12/vocab/applicator"),
        URI("https://json-schema.org/draft/2020-12/vocab/unevaluated"),
        URI("https://json-schema.org/draft/2020-12/vocab/validation"),
        URI("https://json-schema.org/draft/2020-12/vocab/format-annotation"),
        URI("https://json-schema.org/draft/2020-12/vocab/meta-data"),
        URI("https://json-schema.org/draft/2020-12/vocab/content"),
    )
