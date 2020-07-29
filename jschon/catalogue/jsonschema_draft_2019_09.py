import pathlib

import rfc3986

from jschon.catalogue import Catalogue
from jschon.formats import *
from jschon.jsonschema import *
from jschon.keywords import *


def initialize():
    JSONObjectSchema._bootstrap_kwclasses = (
        IdKeyword,
        DefsKeyword,
        SchemaKeyword,
        VocabularyKeyword,
    )

    Catalogue.add_local(
        base_uri=rfc3986.uri_reference('https://json-schema.org/draft/2019-09/'),
        base_dir=pathlib.Path(__file__).parent / 'json-schema.org' / 'draft' / '2019-09',
    )

    Vocabulary.register(
        uri="https://json-schema.org/draft/2019-09/vocab/core",
        kwclasses=(
            SchemaKeyword,
            VocabularyKeyword,
            IdKeyword,
            RefKeyword,
            RecursiveRefKeyword,
            DefsKeyword,
        )
    )

    Vocabulary.register(
        uri="https://json-schema.org/draft/2019-09/vocab/applicator",
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
        uri="https://json-schema.org/draft/2019-09/vocab/validation",
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
        uri="https://json-schema.org/draft/2019-09/vocab/meta-data",
        kwclasses=()
    )

    FormatVocabulary.register(
        uri="https://json-schema.org/draft/2019-09/vocab/format",
        kwclasses=(
            FormatKeyword,
        ),
        fmtclasses=(
            DateTimeFormat,
            DateFormat,
            TimeFormat,
            DurationFormat,
            EmailFormat,
            IDNEmailFormat,
            HostnameFormat,
            IDNHostnameFormat,
            IPv4Format,
            IPv6Format,
            URIFormat,
            URIReferenceFormat,
            IRIFormat,
            IRIReferenceFormat,
            UUIDFormat,
            URITemplateFormat,
            JSONPointerFormat,
            RelativeJSONPointerFormat,
            RegexFormat,
        ),
        assert_=True,
    )

    Vocabulary.register(
        uri="https://json-schema.org/draft/2019-09/vocab/content",
        kwclasses=()
    )
