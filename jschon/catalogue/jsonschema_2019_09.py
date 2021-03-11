import submodules
from jschon.catalogue import Catalogue
from jschon.jsonschema import *
from jschon.keywords import *
from jschon.uri import URI


def initialize():
    JSONSchema.bootstrap(
        IdKeyword,
        SchemaKeyword,
        VocabularyKeyword,
    )

    Catalogue.add_local(
        base_uri=URI('https://json-schema.org/draft/2019-09/'),
        base_dir=submodules.rootdir / 'json-schema-spec-2019-09',
    )

    Vocabulary.register(
        uri=URI("https://json-schema.org/draft/2019-09/vocab/core"),
        kwclasses=(
            SchemaKeyword,
            VocabularyKeyword,
            IdKeyword,
            RefKeyword,
            AnchorKeyword,
            RecursiveRefKeyword,
            RecursiveAnchorKeyword,
            DefsKeyword,
            CommentKeyword,
        )
    )

    Vocabulary.register(
        uri=URI("https://json-schema.org/draft/2019-09/vocab/applicator"),
        kwclasses=(
            AllOfKeyword,
            AnyOfKeyword,
            OneOfKeyword,
            NotKeyword,
            IfKeyword,
            ThenKeyword,
            ElseKeyword,
            DependentSchemasKeyword,
            ItemsKeyword,
            AdditionalItemsKeyword,
            UnevaluatedItemsKeyword,
            ContainsKeyword,
            PropertiesKeyword,
            PatternPropertiesKeyword,
            AdditionalPropertiesKeyword,
            UnevaluatedPropertiesKeyword,
            PropertyNamesKeyword,
        )
    )

    Vocabulary.register(
        uri=URI("https://json-schema.org/draft/2019-09/vocab/validation"),
        kwclasses=(
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
    )

    Vocabulary.register(
        uri=URI("https://json-schema.org/draft/2019-09/vocab/format"),
        kwclasses=(
            FormatKeyword,
        )
    )

    Vocabulary.register(
        uri=URI("https://json-schema.org/draft/2019-09/vocab/meta-data"),
        kwclasses=(
            TitleKeyword,
            DescriptionKeyword,
            DefaultKeyword,
            DeprecatedKeyword,
            ReadOnlyKeyword,
            WriteOnlyKeyword,
            ExamplesKeyword,
        )
    )

    Vocabulary.register(
        uri=URI("https://json-schema.org/draft/2019-09/vocab/content"),
        kwclasses=(
            ContentMediaTypeKeyword,
            ContentEncodingKeyword,
            ContentSchemaKeyword,
        )
    )

    # cache and self-validate the metaschema and its vocabularies
    metaschema_uri = URI("https://json-schema.org/draft/2019-09/schema")
    metaschema = JSONSchema.load(metaschema_uri, metaschema_uri=metaschema_uri)
    metaschema.validate()
