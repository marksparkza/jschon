import submodules
from jschon.catalogue import Catalogue
from jschon.jsonschema import KeywordDef
from jschon.uri import URI
from jschon.vocabulary.applicator import *
from jschon.vocabulary.content import *
from jschon.vocabulary.core import *
from jschon.vocabulary.format import *
from jschon.vocabulary.metadata import *
from jschon.vocabulary.validation import *


def initialize():
    Catalogue.add_directory(
        base_uri=URI('https://json-schema.org/draft/2019-09/'),
        base_dir=submodules.rootdir / 'json-schema-spec-2019-09',
    )

    Catalogue.create_vocabulary(
        URI("https://json-schema.org/draft/2019-09/vocab/core"),
        KeywordDef(SchemaKeyword, "$schema"),
        KeywordDef(VocabularyKeyword, "$vocabulary"),
        KeywordDef(IdKeyword, "$id"),
        KeywordDef(RefKeyword, "$ref"),
        KeywordDef(AnchorKeyword, "$anchor"),
        KeywordDef(RecursiveRefKeyword, "$recursiveRef"),
        KeywordDef(RecursiveAnchorKeyword, "$recursiveAnchor"),
        KeywordDef(DefsKeyword, "$defs"),
        KeywordDef(CommentKeyword, "$comment"),
    )

    Catalogue.create_vocabulary(
        URI("https://json-schema.org/draft/2019-09/vocab/applicator"),
        KeywordDef(AllOfKeyword, "allOf"),
        KeywordDef(AnyOfKeyword, "anyOf"),
        KeywordDef(OneOfKeyword, "oneOf"),
        KeywordDef(NotKeyword, "not"),
        KeywordDef(IfKeyword, "if"),
        KeywordDef(ThenKeyword, "then", depends_on="if"),
        KeywordDef(ElseKeyword, "else", depends_on="if"),
        KeywordDef(DependentSchemasKeyword, "dependentSchemas", instance_types="object"),
        KeywordDef(ItemsKeyword, "items", instance_types="array"),
        KeywordDef(AdditionalItemsKeyword, "additionalItems", instance_types="array", depends_on="items"),
        KeywordDef(UnevaluatedItemsKeyword, "unevaluatedItems", instance_types="array",
                   depends_on=("items", "additionalItems", "if", "then", "else", "allOf", "anyOf", "oneOf", "not")),
        KeywordDef(ContainsKeyword, "contains", instance_types="array"),
        KeywordDef(PropertiesKeyword, "properties", instance_types="object"),
        KeywordDef(PatternPropertiesKeyword, "patternProperties", instance_types="object"),
        KeywordDef(AdditionalPropertiesKeyword, "additionalProperties", instance_types="object",
                   depends_on=("properties", "patternProperties")),
        KeywordDef(UnevaluatedPropertiesKeyword, "unevaluatedProperties", instance_types="object",
                   depends_on=("properties", "patternProperties", "additionalProperties", "if", "then", "else",
                               "dependentSchemas", "allOf", "anyOf", "oneOf", "not")),
        KeywordDef(PropertyNamesKeyword, "propertyNames", instance_types="object"),
    )

    Catalogue.create_vocabulary(
        URI("https://json-schema.org/draft/2019-09/vocab/validation"),
        KeywordDef(TypeKeyword, "type"),
        KeywordDef(EnumKeyword, "enum"),
        KeywordDef(ConstKeyword, "const"),
        KeywordDef(MultipleOfKeyword, "multipleOf", instance_types="number"),
        KeywordDef(MaximumKeyword, "maximum", instance_types="number"),
        KeywordDef(ExclusiveMaximumKeyword, "exclusiveMaximum", instance_types="number"),
        KeywordDef(MinimumKeyword, "minimum", instance_types="number"),
        KeywordDef(ExclusiveMinimumKeyword, "exclusiveMinimum", instance_types="number"),
        KeywordDef(MaxLengthKeyword, "maxLength", instance_types="string"),
        KeywordDef(MinLengthKeyword, "minLength", instance_types="string"),
        KeywordDef(PatternKeyword, "pattern", instance_types="string"),
        KeywordDef(MaxItemsKeyword, "maxItems", instance_types="array"),
        KeywordDef(MinItemsKeyword, "minItems", instance_types="array"),
        KeywordDef(UniqueItemsKeyword, "uniqueItems", instance_types="array"),
        KeywordDef(MaxContainsKeyword, "maxContains", instance_types="array", depends_on="contains"),
        KeywordDef(MinContainsKeyword, "minContains", instance_types="array", depends_on=("contains", "maxContains")),
        KeywordDef(MaxPropertiesKeyword, "maxProperties", instance_types="object"),
        KeywordDef(MinPropertiesKeyword, "minProperties", instance_types="object"),
        KeywordDef(RequiredKeyword, "required", instance_types="object"),
        KeywordDef(DependentRequiredKeyword, "dependentRequired", instance_types="object"),
    )

    Catalogue.create_vocabulary(
        URI("https://json-schema.org/draft/2019-09/vocab/format"),
        KeywordDef(FormatKeyword, "format"),
    )

    Catalogue.create_vocabulary(
        URI("https://json-schema.org/draft/2019-09/vocab/meta-data"),
        KeywordDef(TitleKeyword, "title"),
        KeywordDef(DescriptionKeyword, "description"),
        KeywordDef(DefaultKeyword, "default"),
        KeywordDef(DeprecatedKeyword, "deprecated"),
        KeywordDef(ReadOnlyKeyword, "readOnly"),
        KeywordDef(WriteOnlyKeyword, "writeOnly"),
        KeywordDef(ExamplesKeyword, "examples"),
    )

    Catalogue.create_vocabulary(
        URI("https://json-schema.org/draft/2019-09/vocab/content"),
        KeywordDef(ContentMediaTypeKeyword, "contentMediaType"),
        KeywordDef(ContentEncodingKeyword, "contentEncoding"),
        KeywordDef(ContentSchemaKeyword, "contentSchema", depends_on="contentMediaType"),
    )

    Catalogue.create_metaschema(
        URI("https://json-schema.org/draft/2019-09/schema"),
        URI("https://json-schema.org/draft/2019-09/vocab/core"),
        URI("https://json-schema.org/draft/2019-09/vocab/applicator"),
        URI("https://json-schema.org/draft/2019-09/vocab/validation"),
        URI("https://json-schema.org/draft/2019-09/vocab/format"),
        URI("https://json-schema.org/draft/2019-09/vocab/meta-data"),
        URI("https://json-schema.org/draft/2019-09/vocab/content"),
    )
