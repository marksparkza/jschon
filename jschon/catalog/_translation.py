import pathlib

from jschon.catalog import Catalog, LocalSource
from jschon.translation import TranslationOutputFormatter
from jschon.uri import URI
from jschon.vocabulary.translation import *


def initialize(catalog: Catalog):
    catalog.add_uri_source(
        URI('https://jschon.dev/ext/translation/'),
        LocalSource(pathlib.Path(__file__).parent / 'json-translation-vocabulary', suffix='.json'),
    )

    catalog.create_vocabulary(
        URI('https://jschon.dev/ext/translation'),
        TranslationsKeyword,
        T9nSchemeKeyword,
        T9nTargetKeyword,
        T9nConditionKeyword,
        T9nConstKeyword,
        T9nSourceKeyword,
        T9nConcatKeyword,
        T9nSepKeyword,
        T9nFilterKeyword,
        T9nCastKeyword,
        T9nArrayKeyword,
        T9nObjectKeyword,
    )

    catalog.create_metaschema(
        URI('https://jschon.dev/ext/translation/schema'),
        URI("https://json-schema.org/draft/2020-12/vocab/core"),
        URI("https://json-schema.org/draft/2020-12/vocab/applicator"),
        URI("https://json-schema.org/draft/2020-12/vocab/unevaluated"),
        URI("https://json-schema.org/draft/2020-12/vocab/validation"),
        URI("https://json-schema.org/draft/2020-12/vocab/format-annotation"),
        URI("https://json-schema.org/draft/2020-12/vocab/meta-data"),
        URI("https://json-schema.org/draft/2020-12/vocab/content"),
        URI("https://jschon.dev/ext/translation"),
    )

    catalog.output_formatter = TranslationOutputFormatter()
