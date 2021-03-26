import submodules
from jschon.catalogue import Catalogue
from jschon.jsonschema import KeywordDef
from jschon.uri import URI
from jschon.vocabulary.annotation import *
from jschon.vocabulary.applicator import *
from jschon.vocabulary.core import *
from jschon.vocabulary.format import *
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
        KeywordDef(DynamicRefKeyword, "$recursiveRef", keymap={"$dynamicAnchor": "$recursiveAnchor"}),
        KeywordDef(DynamicAnchorKeyword, "$recursiveAnchor"),
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
        KeywordDef(ThenKeyword, "then", depends="if"),
        KeywordDef(ElseKeyword, "else", depends="if"),
        KeywordDef(DependentSchemasKeyword, "dependentSchemas", types="object"),
        KeywordDef(LegacyItemsKeyword, "items", types="array"),
        KeywordDef(LegacyAdditionalItemsKeyword, "additionalItems", types="array", depends="items"),
        KeywordDef(UnevaluatedItemsKeyword, "unevaluatedItems", types="array",
                   depends=("items", "additionalItems", "if", "then", "else", "allOf", "anyOf", "oneOf", "not")),
        KeywordDef(ContainsKeyword, "contains", types="array"),
        KeywordDef(PropertiesKeyword, "properties", types="object"),
        KeywordDef(PatternPropertiesKeyword, "patternProperties", types="object"),
        KeywordDef(AdditionalPropertiesKeyword, "additionalProperties", types="object",
                   depends=("properties", "patternProperties")),
        KeywordDef(UnevaluatedPropertiesKeyword, "unevaluatedProperties", types="object",
                   depends=("properties", "patternProperties", "additionalProperties", "if", "then", "else",
                            "dependentSchemas", "allOf", "anyOf", "oneOf", "not")),
        KeywordDef(PropertyNamesKeyword, "propertyNames", types="object"),
    )

    Catalogue.create_vocabulary(
        URI("https://json-schema.org/draft/2019-09/vocab/validation"),
        KeywordDef(TypeKeyword, "type"),
        KeywordDef(EnumKeyword, "enum"),
        KeywordDef(ConstKeyword, "const"),
        KeywordDef(MultipleOfKeyword, "multipleOf", types="number"),
        KeywordDef(MaximumKeyword, "maximum", types="number"),
        KeywordDef(ExclusiveMaximumKeyword, "exclusiveMaximum", types="number"),
        KeywordDef(MinimumKeyword, "minimum", types="number"),
        KeywordDef(ExclusiveMinimumKeyword, "exclusiveMinimum", types="number"),
        KeywordDef(MaxLengthKeyword, "maxLength", types="string"),
        KeywordDef(MinLengthKeyword, "minLength", types="string"),
        KeywordDef(PatternKeyword, "pattern", types="string"),
        KeywordDef(MaxItemsKeyword, "maxItems", types="array"),
        KeywordDef(MinItemsKeyword, "minItems", types="array"),
        KeywordDef(UniqueItemsKeyword, "uniqueItems", types="array"),
        KeywordDef(MaxContainsKeyword, "maxContains", types="array", depends="contains"),
        KeywordDef(MinContainsKeyword, "minContains", types="array", depends=("contains", "maxContains")),
        KeywordDef(MaxPropertiesKeyword, "maxProperties", types="object"),
        KeywordDef(MinPropertiesKeyword, "minProperties", types="object"),
        KeywordDef(RequiredKeyword, "required", types="object"),
        KeywordDef(DependentRequiredKeyword, "dependentRequired", types="object"),
    )

    Catalogue.create_vocabulary(
        URI("https://json-schema.org/draft/2019-09/vocab/format"),
        KeywordDef(FormatKeyword, "format"),
    )

    Catalogue.create_vocabulary(
        URI("https://json-schema.org/draft/2019-09/vocab/meta-data"),
        KeywordDef(AnnotationKeyword, "title"),
        KeywordDef(AnnotationKeyword, "description"),
        KeywordDef(AnnotationKeyword, "default"),
        KeywordDef(AnnotationKeyword, "deprecated"),
        KeywordDef(AnnotationKeyword, "readOnly"),
        KeywordDef(AnnotationKeyword, "writeOnly"),
        KeywordDef(AnnotationKeyword, "examples"),
    )

    Catalogue.create_vocabulary(
        URI("https://json-schema.org/draft/2019-09/vocab/content"),
        KeywordDef(AnnotationKeyword, "contentMediaType"),
        KeywordDef(AnnotationKeyword, "contentEncoding"),
        KeywordDef(AnnotationKeyword, "contentSchema", depends="contentMediaType"),
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
