import pathlib

from jschon.keywords.applicator import *
from jschon.keywords.validation import *
from jschon.schema import Metaschema, Vocabulary

Metaschema.register(
    uri="https://json-schema.org/draft/2019-09/schema",
    filepath=pathlib.Path(__file__).parent / 'catalogue' / 'jsonschema_201909' / 'schema',
)

Vocabulary.register(
    uri="https://json-schema.org/draft/2019-09/vocab/core",
    kwclasses=()
)

Vocabulary.register(
    uri="https://json-schema.org/draft/2019-09/vocab/applicator",
    kwclasses=(
        ItemsKeyword,
        AdditionalItemsKeyword,
        UnevaluatedItemsKeyword,
        ContainsKeyword,
        PropertiesKeyword,
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
    )
)

Vocabulary.register(
    uri="https://json-schema.org/draft/2019-09/vocab/meta-data",
    kwclasses=()
)

Vocabulary.register(
    uri="https://json-schema.org/draft/2019-09/vocab/format",
    kwclasses=()
)

Vocabulary.register(
    uri="https://json-schema.org/draft/2019-09/vocab/content",
    kwclasses=()
)
