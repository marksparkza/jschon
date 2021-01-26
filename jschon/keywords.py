import re
from typing import *

from jschon.exceptions import JSONSchemaError, VocabularyError, URIError
from jschon.json import *
from jschon.jsonschema import *
from jschon.types import tuplify, arrayify
from jschon.uri import URI

__all__ = [
    # core vocabulary
    'SchemaKeyword',
    'VocabularyKeyword',
    'IdKeyword',
    'RefKeyword',
    'AnchorKeyword',
    'RecursiveRefKeyword',
    'RecursiveAnchorKeyword',
    'DefsKeyword',
    'CommentKeyword',

    # applicator vocabulary
    'AllOfKeyword',
    'AnyOfKeyword',
    'OneOfKeyword',
    'NotKeyword',
    'IfKeyword',
    'ThenKeyword',
    'ElseKeyword',
    'DependentSchemasKeyword',
    'ItemsKeyword',
    'AdditionalItemsKeyword',
    'UnevaluatedItemsKeyword',
    'ContainsKeyword',
    'PropertiesKeyword',
    'PatternPropertiesKeyword',
    'AdditionalPropertiesKeyword',
    'UnevaluatedPropertiesKeyword',
    'PropertyNamesKeyword',

    # validation vocabulary
    'TypeKeyword',
    'EnumKeyword',
    'ConstKeyword',
    'MultipleOfKeyword',
    'MaximumKeyword',
    'ExclusiveMaximumKeyword',
    'MinimumKeyword',
    'ExclusiveMinimumKeyword',
    'MaxLengthKeyword',
    'MinLengthKeyword',
    'PatternKeyword',
    'MaxItemsKeyword',
    'MinItemsKeyword',
    'UniqueItemsKeyword',
    'MaxContainsKeyword',
    'MinContainsKeyword',
    'MaxPropertiesKeyword',
    'MinPropertiesKeyword',
    'RequiredKeyword',
    'DependentRequiredKeyword',

    # format vocabulary
    'FormatKeyword',

    # meta-data vocabulary
    'TitleKeyword',
    'DescriptionKeyword',
    'DefaultKeyword',
    'DeprecatedKeyword',
    'ReadOnlyKeyword',
    'WriteOnlyKeyword',
    'ExamplesKeyword',

    # content vocabulary
    'ContentMediaTypeKeyword',
    'ContentEncodingKeyword',
    'ContentSchemaKeyword',
]


class SchemaKeyword(Keyword):
    __keyword__ = "$schema"
    __schema__ = {
        "type": "string",
        "format": "uri"
    }

    def __init__(
            self,
            value: str,
            **kwargs: Any,
    ) -> None:
        super().__init__(value, **kwargs)
        if self.superschema.superkeyword is not None:
            raise JSONSchemaError('The "$schema" keyword must not appear in a subschema')

        try:
            (uri := URI(value)).validate(require_scheme=True, require_normalized=True)
        except URIError as e:
            raise JSONSchemaError from e

        self.superschema.metaschema_uri = uri


class VocabularyKeyword(Keyword):
    __keyword__ = "$vocabulary"
    __schema__ = {
        "type": "object",
        "propertyNames": {
            "type": "string",
            "format": "uri"
        },
        "additionalProperties": {
            "type": "boolean"
        }
    }

    def __init__(
            self,
            value: JSONObject[JSONBoolean],
            **kwargs: Any,
    ) -> None:
        super().__init__(value, **kwargs)
        if self.superschema.superkeyword is not None:
            raise JSONSchemaError('The "$vocabulary" keyword must not appear in a subschema')

        for vocab_uri, vocab_required in value.items():
            try:
                (vocab_uri := URI(vocab_uri)).validate(require_scheme=True, require_normalized=True)
            except URIError as e:
                raise JSONSchemaError from e

            if not isinstance(vocab_required, bool):
                raise JSONSchemaError('"$vocabulary" values must be booleans')

            try:
                vocabulary = Vocabulary(vocab_uri, vocab_required)
                self.superschema.kwclasses.update(vocabulary.kwclasses)
            except VocabularyError as e:
                if vocab_required:
                    raise JSONSchemaError(f"The metaschema requires an unrecognized vocabulary '{vocab_uri}'") from e


class IdKeyword(Keyword):
    __keyword__ = "$id"
    __schema__ = {
        "type": "string",
        "format": "uri-reference",
        "$comment": "Non-empty fragments not allowed.",
        "pattern": "^[^#]*#?$"
    }

    def __init__(
            self,
            value: str,
            **kwargs: Any,
    ) -> None:
        super().__init__(value, **kwargs)
        (uri := URI(value)).validate(require_normalized=True, allow_fragment=False)
        if not uri.is_absolute():
            if not self.superschema.path:
                raise JSONSchemaError('The "$id" of the root schema, if present, must be an absolute URI')
            if (base_uri := self.superschema.base_uri) is not None:
                uri = uri.resolve(base_uri)
            else:
                raise JSONSchemaError(f'No base URI against which to resolve the "$id" value "{value}"')

        self.superschema.uri = uri


class RefKeyword(Keyword):
    __keyword__ = "$ref"
    __schema__ = {
        "type": "string",
        "format": "uri-reference"
    }

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        uri = URI(self.json.value)
        if not uri.can_absolute():
            if (base_uri := self.superschema.base_uri) is not None:
                uri = uri.resolve(base_uri)
            else:
                raise JSONSchemaError(f'No base URI against which to resolve the "$ref" value "{uri}"')

        refschema = JSONSchema.get(uri, self.superschema.metaschema_uri)
        refschema.evaluate(instance, scope)


class AnchorKeyword(Keyword):
    __keyword__ = "$anchor"
    __schema__ = {
        "type": "string",
        "pattern": "^[A-Za-z][-A-Za-z0-9.:_]*$"
    }

    def __init__(
            self,
            value: str,
            **kwargs: Any,
    ) -> None:
        super().__init__(value, **kwargs)
        if (base_uri := self.superschema.base_uri) is not None:
            uri = URI(f'{base_uri}#{value}')
        else:
            raise JSONSchemaError(f'No base URI for anchor "{value}"')

        JSONSchema.set(uri, self.superschema)


class RecursiveRefKeyword(Keyword):
    __keyword__ = "$recursiveRef"
    __schema__ = {
        "type": "string",
        "format": "uri-reference"
    }

    def __init__(
            self,
            value: str,
            **kwargs: Any,
    ) -> None:
        super().__init__(value, **kwargs)
        if value != '#':
            raise JSONSchemaError('The "$recursiveRef" keyword may only take the value "#"')

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        if (base_uri := self.superschema.base_uri) is not None:
            refschema = JSONSchema.get(base_uri, self.superschema.metaschema_uri)
        else:
            raise JSONSchemaError(f'No base URI against which to resolve "$recursiveRef"')

        if (recursive_anchor := refschema.keywords.get("$recursiveAnchor")) and \
                recursive_anchor.json.value is True:
            base_scope = scope.root
            for key in scope.path:
                if isinstance(base_schema := base_scope.schema, JSONSchema):
                    if base_schema == refschema:
                        break
                    if (base_anchor := base_schema.keywords.get("$recursiveAnchor")) and \
                            base_anchor.json.value is True:
                        refschema = base_schema
                        break
                base_scope = base_scope.children[key]

        refschema.evaluate(instance, scope)


class RecursiveAnchorKeyword(Keyword):
    __keyword__ = "$recursiveAnchor"
    __schema__ = {
        "type": "boolean",
        "default": False
    }


class DefsKeyword(Keyword):
    __keyword__ = "$defs"
    __schema__ = {
        "type": "object",
        "additionalProperties": {"$recursiveRef": "#"},
        "default": {}
    }
    applicators = PropertyApplicator,


class CommentKeyword(Keyword):
    __keyword__ = "$comment"
    __schema__ = {"type": "string"}


class AllOfKeyword(Keyword):
    __keyword__ = "allOf"
    __schema__ = {
        "type": "array",
        "minItems": 1,
        "items": {"$recursiveRef": "#"}
    }

    applicators = ArrayApplicator,

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        self.json: JSONArray[JSONSchema]

        err_indices = []
        for index, subschema in enumerate(self.json):
            with scope(self.superschema, str(index)) as subscope:
                subschema.evaluate(instance, subscope)
                if not subscope.valid:
                    err_indices += [index]

        if err_indices:
            scope.fail(instance, f'The instance is invalid against "allOf" subschemas {err_indices}')


class AnyOfKeyword(Keyword):
    __keyword__ = "anyOf"
    __schema__ = {
        "type": "array",
        "minItems": 1,
        "items": {"$recursiveRef": "#"}
    }

    applicators = ArrayApplicator,

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        self.json: JSONArray[JSONSchema]

        valid = False
        for index, subschema in enumerate(self.json):
            with scope(self.superschema, str(index)) as subscope:
                subschema.evaluate(instance, subscope)
                if subscope.valid:
                    valid = True

        if not valid:
            scope.fail(instance, f'The instance must be valid against at least one "anyOf" subschema')


class OneOfKeyword(Keyword):
    __keyword__ = "oneOf"
    __schema__ = {
        "type": "array",
        "minItems": 1,
        "items": {"$recursiveRef": "#"}
    }

    applicators = ArrayApplicator,

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        self.json: JSONArray[JSONSchema]

        valid_indices = []
        err_indices = []
        for index, subschema in enumerate(self.json):
            with scope(self.superschema, str(index)) as subscope:
                subschema.evaluate(instance, subscope)
                if subscope.valid:
                    valid_indices += [index]
                else:
                    err_indices += [index]

        if len(valid_indices) != 1:
            scope.fail(instance, 'The instance must be valid against exactly one "oneOf" subschema;'
                                 f'it is valid against {valid_indices} and invalid against {err_indices}')


class NotKeyword(Keyword):
    __keyword__ = "not"
    __schema__ = {"$recursiveRef": "#"}

    applicators = Applicator,

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        self.json: JSONSchema
        self.json.evaluate(instance, scope)

        if scope.valid:
            scope.fail(instance, 'The instance must not be valid against the "not" subschema')
        else:
            scope.errors.clear()


class IfKeyword(Keyword):
    __keyword__ = "if"
    __schema__ = {"$recursiveRef": "#"}

    applicators = Applicator,

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        self.json: JSONSchema
        self.json.evaluate(instance, scope)
        scope.assert_ = False
        scope.keep = True


class ThenKeyword(Keyword):
    __keyword__ = "then"
    __schema__ = {"$recursiveRef": "#"}
    __depends__ = "if"

    applicators = Applicator,

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        self.json: JSONSchema
        if (if_ := scope.sibling("if")) and if_.valid:
            self.json.evaluate(instance, scope)


class ElseKeyword(Keyword):
    __keyword__ = "else"
    __schema__ = {"$recursiveRef": "#"}
    __depends__ = "if"

    applicators = Applicator,

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        self.json: JSONSchema
        if (if_ := scope.sibling("if")) and not if_.valid:
            self.json.evaluate(instance, scope)


class DependentSchemasKeyword(Keyword):
    __keyword__ = "dependentSchemas"
    __schema__ = {
        "type": "object",
        "additionalProperties": {"$recursiveRef": "#"}
    }
    __types__ = "object"

    applicators = PropertyApplicator,

    def evaluate(self, instance: JSONObject, scope: Scope) -> None:
        self.json: JSONObject[JSONSchema]

        annotation = []
        err_names = []
        for name, subschema in self.json.items():
            if name in instance:
                with scope(self.superschema, name) as subscope:
                    subschema.evaluate(instance, subscope)
                    if subscope.valid:
                        annotation += [name]
                    else:
                        err_names += [name]

        if err_names:
            scope.fail(instance, f'Properties {err_names} are invalid against '
                                 'the corresponding "dependentSchemas" subschemas')
        else:
            scope.annotate(instance, "dependentSchemas", annotation)


class ItemsKeyword(Keyword):
    __keyword__ = "items"
    __schema__ = {
        "anyOf": [
            {"$recursiveRef": "#"},
            {
                "type": "array",
                "minItems": 1,
                "items": {"$recursiveRef": "#"}
            }
        ]
    }
    __types__ = "array"

    applicators = Applicator, ArrayApplicator

    def evaluate(self, instance: JSONArray, scope: Scope) -> None:
        if len(instance) == 0:
            return

        elif isinstance(self.json, JSONBooleanSchema):
            self.json.evaluate(instance, scope)

        elif isinstance(self.json, JSONSchema):
            for index, item in enumerate(instance):
                self.json.evaluate(item, scope)

            if scope.valid:
                scope.annotate(instance, "items", True)

        elif isinstance(self.json, JSONArray):
            self.json: JSONArray[JSONSchema]
            eval_index = None
            err_indices = []
            for index, item in enumerate(instance[:len(self.json)]):
                eval_index = index
                with scope(self.superschema, str(index)) as subscope:
                    self.json[index].evaluate(item, subscope)
                    if not subscope.valid:
                        err_indices += [index]

            if err_indices:
                scope.fail(instance, f"Array elements {err_indices} are invalid")
            else:
                scope.annotate(instance, "items", eval_index)


class AdditionalItemsKeyword(Keyword):
    __keyword__ = "additionalItems"
    __schema__ = {"$recursiveRef": "#"}
    __types__ = "array"
    __depends__ = "items"

    applicators = Applicator,

    def evaluate(self, instance: JSONArray, scope: Scope) -> None:
        self.json: JSONSchema

        if (items := scope.sibling("items")) and (items_annotation := items.annotations.get("items")) and \
                isinstance(items_annotation.value, int):
            annotation = None
            for index, item in enumerate(instance[items_annotation.value + 1:]):
                annotation = True
                self.json.evaluate(item, scope)

            if scope.valid:
                scope.annotate(instance, "additionalItems", annotation)


class UnevaluatedItemsKeyword(Keyword):
    __keyword__ = "unevaluatedItems"
    __schema__ = {"$recursiveRef": "#"}
    __types__ = "array"
    __depends__ = "items", "additionalItems", "if", "then", "else", "allOf", "anyOf", "oneOf", "not"

    applicators = Applicator,

    def evaluate(self, instance: JSONArray, scope: Scope) -> None:
        self.json: JSONSchema

        last_evaluated_item = -1
        for items_annotation in scope.parent.collect_annotations(instance, "items"):
            if items_annotation.value is True:
                return
            if isinstance(items_annotation.value, int) and items_annotation.value > last_evaluated_item:
                last_evaluated_item = items_annotation.value

        for additional_items_annotation in scope.parent.collect_annotations(instance, "additionalItems"):
            if additional_items_annotation.value is True:
                return

        for unevaluated_items_annotation in scope.parent.collect_annotations(instance, "unevaluatedItems"):
            if unevaluated_items_annotation.value is True:
                return

        annotation = None
        for index, item in enumerate(instance[last_evaluated_item + 1:]):
            annotation = True
            self.json.evaluate(item, scope)

        if scope.valid:
            scope.annotate(instance, "unevaluatedItems", annotation)


class ContainsKeyword(Keyword):
    __keyword__ = "contains"
    __schema__ = {"$recursiveRef": "#"}
    __types__ = "array"

    applicators = Applicator,

    def evaluate(self, instance: JSONArray, scope: Scope) -> None:
        self.json: JSONSchema

        annotation = 0
        for index, item in enumerate(instance):
            if self.json.evaluate(item, scope, assert_=False):
                annotation += 1

        if annotation > 0:
            scope.annotate(instance, "contains", annotation)
        else:
            scope.fail(instance, 'The array does not contain an element that is valid '
                                 'against the "contains" subschema')


class PropertiesKeyword(Keyword):
    __keyword__ = "properties"
    __schema__ = {
        "type": "object",
        "additionalProperties": {"$recursiveRef": "#"},
        "default": {}
    }
    __types__ = "object"

    applicators = PropertyApplicator,

    def evaluate(self, instance: JSONObject, scope: Scope) -> None:
        self.json: JSONObject[JSONSchema]

        annotation = []
        err_names = []
        for name, item in instance.items():
            if name in self.json:
                with scope(self.superschema, name) as subscope:
                    self.json[name].evaluate(item, subscope)
                    if subscope.valid:
                        annotation += [name]
                    else:
                        err_names += [name]

        if err_names:
            scope.fail(instance, f"Properties {err_names} are invalid")
        else:
            scope.annotate(instance, "properties", annotation)


class PatternPropertiesKeyword(Keyword):
    __keyword__ = "patternProperties"
    __schema__ = {
        "type": "object",
        "additionalProperties": {"$recursiveRef": "#"},
        "propertyNames": {"format": "regex"},
        "default": {}
    }
    __types__ = "object"

    applicators = PropertyApplicator,

    def evaluate(self, instance: JSONObject, scope: Scope) -> None:
        self.json: JSONObject[JSONSchema]

        matched_names = set()
        err_names = []
        for name, item in instance.items():
            for regex, subschema in self.json.items():
                if re.search(regex, name) is not None:
                    with scope(self.superschema, regex) as subscope:
                        subschema.evaluate(item, subscope)
                        if subscope.valid:
                            matched_names |= {name}
                        else:
                            err_names += [name]

        if err_names:
            scope.fail(instance, f"Properties {err_names} are invalid")
        else:
            scope.annotate(instance, "patternProperties", list(matched_names))


class AdditionalPropertiesKeyword(Keyword):
    __keyword__ = "additionalProperties"
    __schema__ = {"$recursiveRef": "#"}
    __types__ = "object"
    __depends__ = "properties", "patternProperties"

    applicators = Applicator,

    def evaluate(self, instance: JSONObject, scope: Scope) -> None:
        self.json: JSONSchema

        evaluated_names = set()
        if (properties := scope.sibling("properties")) and \
                (properties_annotation := properties.annotations.get("properties")):
            evaluated_names |= set(properties_annotation.value)

        if (pattern_properties := scope.sibling("patternProperties")) and \
                (pattern_properties_annotation := pattern_properties.annotations.get("patternProperties")):
            evaluated_names |= set(pattern_properties_annotation.value)

        annotation = []
        for name, item in instance.items():
            if name not in evaluated_names:
                if self.json.evaluate(item, scope):
                    annotation += [name]

        if scope.valid:
            scope.annotate(instance, "additionalProperties", annotation)


class UnevaluatedPropertiesKeyword(Keyword):
    __keyword__ = "unevaluatedProperties"
    __schema__ = {"$recursiveRef": "#"}
    __types__ = "object"
    __depends__ = "properties", "patternProperties", "additionalProperties", \
                  "if", "then", "else", "dependentSchemas", \
                  "allOf", "anyOf", "oneOf", "not"

    applicators = Applicator,

    def evaluate(self, instance: JSONObject, scope: Scope) -> None:
        self.json: JSONSchema

        evaluated_names = set()
        for properties_annotation in scope.parent.collect_annotations(instance, "properties"):
            evaluated_names |= set(properties_annotation.value)
        for pattern_properties_annotation in scope.parent.collect_annotations(instance, "patternProperties"):
            evaluated_names |= set(pattern_properties_annotation.value)
        for additional_properties_annotation in scope.parent.collect_annotations(instance, "additionalProperties"):
            evaluated_names |= set(additional_properties_annotation.value)
        for unevaluated_properties_annotation in scope.parent.collect_annotations(instance, "unevaluatedProperties"):
            evaluated_names |= set(unevaluated_properties_annotation.value)

        annotation = []
        for name, item in instance.items():
            if name not in evaluated_names:
                if self.json.evaluate(item, scope):
                    annotation += [name]

        if scope.valid:
            scope.annotate(instance, "unevaluatedProperties", annotation)


class PropertyNamesKeyword(Keyword):
    __keyword__ = "propertyNames"
    __schema__ = {"$recursiveRef": "#"}
    __types__ = "object"

    applicators = Applicator,

    def evaluate(self, instance: JSONObject, scope: Scope) -> None:
        self.json: JSONSchema

        err_names = []
        for name in instance:
            if not self.json.evaluate(JSON(name, path=instance.path), scope, assert_=False):
                err_names += [name]

        if err_names:
            scope.fail(instance, f"Property names {err_names} are invalid")


class TypeKeyword(Keyword):
    __keyword__ = "type"
    __schema__ = {
        "anyOf": [
            {"enum": ["null", "boolean", "number", "integer", "string", "array", "object"]},
            {
                "type": "array",
                "items": {"enum": ["null", "boolean", "number", "integer", "string", "array", "object"]},
                "minItems": 1,
                "uniqueItems": True
            }
        ]
    }

    def __init__(
            self,
            value: Union[str, Sequence[str]],
            **kwargs: Any,
    ) -> None:
        super().__init__(arrayify(value), **kwargs)

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        self.json: JSONArray[JSONString]
        if not any(instance.istype(item.value) for item in self.json):
            scope.fail(instance, f"The value must be of type {self.json}")


class EnumKeyword(Keyword):
    __keyword__ = "enum"
    __schema__ = {"type": "array", "items": True}

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        self.json: JSONArray
        if instance not in self.json:
            scope.fail(instance, f"The value must be one of {self.json}")


class ConstKeyword(Keyword):
    __keyword__ = "const"
    __schema__ = True

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        if instance != self.json:
            scope.fail(instance, f"The value must be equal to {self.json}")


class MultipleOfKeyword(Keyword):
    __keyword__ = "multipleOf"
    __schema__ = {"type": "number", "exclusiveMinimum": 0}
    __types__ = "number"

    def evaluate(self, instance: JSONNumber, scope: Scope) -> None:
        self.json: JSONNumber
        if instance % self.json != 0:
            scope.fail(instance, f"The value must be a multiple of {self.json}")


class MaximumKeyword(Keyword):
    __keyword__ = "maximum"
    __schema__ = {"type": "number"}
    __types__ = "number"

    def evaluate(self, instance: JSONNumber, scope: Scope) -> None:
        self.json: JSONNumber
        if instance > self.json:
            scope.fail(instance, f"The value may not be greater than {self.json}")


class ExclusiveMaximumKeyword(Keyword):
    __keyword__ = "exclusiveMaximum"
    __schema__ = {"type": "number"}
    __types__ = "number"

    def evaluate(self, instance: JSONNumber, scope: Scope) -> None:
        self.json: JSONNumber
        if instance >= self.json:
            scope.fail(instance, f"The value must be less than {self.json}")


class MinimumKeyword(Keyword):
    __keyword__ = "minimum"
    __schema__ = {"type": "number"}
    __types__ = "number"

    def evaluate(self, instance: JSONNumber, scope: Scope) -> None:
        self.json: JSONNumber
        if instance < self.json:
            scope.fail(instance, f"The value may not be less than {self.json}")


class ExclusiveMinimumKeyword(Keyword):
    __keyword__ = "exclusiveMinimum"
    __schema__ = {"type": "number"}
    __types__ = "number"

    def evaluate(self, instance: JSONNumber, scope: Scope) -> None:
        self.json: JSONNumber
        if instance <= self.json:
            scope.fail(instance, f"The value must be greater than {self.json}")


class MaxLengthKeyword(Keyword):
    __keyword__ = "maxLength"
    __schema__ = {"type": "integer", "minimum": 0}
    __types__ = "string"

    def evaluate(self, instance: JSONString, scope: Scope) -> None:
        self.json: JSONInteger
        if len(instance) > self.json:
            scope.fail(instance, f"The text is too long (maximum {self.json} characters)")


class MinLengthKeyword(Keyword):
    __keyword__ = "minLength"
    __schema__ = {"type": "integer", "minimum": 0, "default": 0}
    __types__ = "string"

    def evaluate(self, instance: JSONString, scope: Scope) -> None:
        self.json: JSONInteger
        if len(instance) < self.json:
            scope.fail(instance, f"The text is too short (minimum {self.json} characters)")


class PatternKeyword(Keyword):
    __keyword__ = "pattern"
    __schema__ = {"type": "string", "format": "regex"}
    __types__ = "string"

    def __init__(
            self,
            value: str,
            **kwargs: Any,
    ) -> None:
        super().__init__(value, **kwargs)
        self.regex = re.compile(value)

    def evaluate(self, instance: JSONString, scope: Scope) -> None:
        if self.regex.search(instance.value) is None:
            scope.fail(instance, f"The text must match the regular expression {self.json}")


class MaxItemsKeyword(Keyword):
    __keyword__ = "maxItems"
    __schema__ = {"type": "integer", "minimum": 0}
    __types__ = "array"

    def evaluate(self, instance: JSONArray, scope: Scope) -> None:
        self.json: JSONInteger
        if len(instance) > self.json:
            scope.fail(instance, f"The array has too many elements (maximum {self.json})")


class MinItemsKeyword(Keyword):
    __keyword__ = "minItems"
    __schema__ = {"type": "integer", "minimum": 0, "default": 0}
    __types__ = "array"

    def evaluate(self, instance: JSONArray, scope: Scope) -> None:
        self.json: JSONInteger
        if len(instance) < self.json:
            scope.fail(instance, f"The array has too few elements (minimum {self.json})")


class UniqueItemsKeyword(Keyword):
    __keyword__ = "uniqueItems"
    __schema__ = {"type": "boolean", "default": False}
    __types__ = "array"

    def evaluate(self, instance: JSONArray, scope: Scope) -> None:
        self.json: JSONBoolean
        if not self.json.value:
            return

        uniquified = []
        for item in instance:
            if item not in uniquified:
                uniquified += [item]

        if len(instance) > len(uniquified):
            scope.fail(instance, "The array's elements must all be unique")


class MaxContainsKeyword(Keyword):
    __keyword__ = "maxContains"
    __schema__ = {"type": "integer", "minimum": 0}
    __types__ = "array"
    __depends__ = "contains"

    def evaluate(self, instance: JSONArray, scope: Scope) -> None:
        self.json: JSONInteger
        if contains := scope.sibling("contains"):
            if (contains_annotation := contains.annotations.get("contains")) and \
                    contains_annotation.value > self.json:
                scope.fail(instance,
                           'The array has too many elements matching the '
                           f'"contains" subschema (maximum {self.json})')


class MinContainsKeyword(Keyword):
    __keyword__ = "minContains"
    __schema__ = {"type": "integer", "minimum": 0, "default": 1}
    __types__ = "array"
    __depends__ = "contains", "maxContains"

    def evaluate(self, instance: JSONArray, scope: Scope) -> None:
        self.json: JSONInteger
        if contains := scope.sibling("contains"):
            contains_count = contains_annotation.value \
                if (contains_annotation := contains.annotations.get("contains")) \
                else 0

            valid = contains_count >= self.json

            if valid and not contains.valid:
                max_contains = scope.sibling("maxContains")
                if not max_contains or max_contains.valid:
                    contains.errors.clear()

            if not valid:
                scope.fail(instance,
                           'The array has too few elements matching the '
                           f'"contains" subschema (minimum {self.json})')


class MaxPropertiesKeyword(Keyword):
    __keyword__ = "maxProperties"
    __schema__ = {"type": "integer", "minimum": 0}
    __types__ = "object"

    def evaluate(self, instance: JSONObject, scope: Scope) -> None:
        self.json: JSONInteger
        if len(instance) > self.json:
            scope.fail(instance, f"The object has too many properties (maximum {self.json})")


class MinPropertiesKeyword(Keyword):
    __keyword__ = "minProperties"
    __schema__ = {"type": "integer", "minimum": 0, "default": 0}
    __types__ = "object"

    def evaluate(self, instance: JSONObject, scope: Scope) -> None:
        self.json: JSONInteger
        if len(instance) < self.json:
            scope.fail(instance, f"The object has too few properties (minimum {self.json})")


class RequiredKeyword(Keyword):
    __keyword__ = "required"
    __schema__ = {
        "type": "array",
        "items": {"type": "string"},
        "uniqueItems": True,
        "default": []
    }
    __types__ = "object"

    def evaluate(self, instance: JSONObject, scope: Scope) -> None:
        self.json: JSONArray[JSONString]

        missing = [name for name in self.json if name.value not in instance]
        if missing:
            scope.fail(instance, f"The object is missing required properties {missing}")


class DependentRequiredKeyword(Keyword):
    __keyword__ = "dependentRequired"
    __schema__ = {
        "type": "object",
        "additionalProperties": {
            "type": "array",
            "items": {"type": "string"},
            "uniqueItems": True,
            "default": []
        }
    }
    __types__ = "object"

    def evaluate(self, instance: JSONObject, scope: Scope) -> None:
        self.json: JSONObject[JSONArray[JSONString]]

        missing = {}
        for name, dependents in self.json.items():
            if name in instance:
                missing_deps = [dep for dep in dependents if dep.value not in instance]
                if missing_deps:
                    missing[name] = missing_deps

        if missing:
            scope.fail(instance, f"The object is missing dependent properties {missing}")


class FormatKeyword(Keyword):
    __keyword__ = "format"
    __schema__ = {"type": "string"}

    def __init__(
            self,
            value: str,
            **kwargs: Any,
    ) -> None:
        super().__init__(value, **kwargs)
        vocabulary = FormatVocabulary.get(self.vocabulary_uri)
        self.format_: Optional[Format] = vocabulary.formats.get(self.json.value)
        self.assert_ = self.format_.assert_ if self.format_ else False

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        if self.format_ and isinstance(instance, tuple(JSON.classfor(t) for t in tuplify(self.format_.__types__))):
            fmtresult = self.format_.evaluate(instance)
            if not fmtresult.valid:
                scope.fail(instance, f'The text does not conform to the {self.json} format: {fmtresult.error}')

        if scope.valid:
            scope.annotate(instance, "format", self.json.value)


class TitleKeyword(Keyword):
    __keyword__ = "title"
    __schema__ = {"type": "string"}

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        scope.annotate(instance, "title", self.json.value)


class DescriptionKeyword(Keyword):
    __keyword__ = "description"
    __schema__ = {"type": "string"}

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        scope.annotate(instance, "description", self.json.value)


class DefaultKeyword(Keyword):
    __keyword__ = "default"
    __schema__ = True

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        scope.annotate(instance, "default", self.json.value)


class DeprecatedKeyword(Keyword):
    __keyword__ = "deprecated"
    __schema__ = {
        "type": "boolean",
        "default": False
    }

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        scope.annotate(instance, "deprecated", self.json.value)


class ReadOnlyKeyword(Keyword):
    __keyword__ = "readOnly"
    __schema__ = {
        "type": "boolean",
        "default": False
    }

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        scope.annotate(instance, "readOnly", self.json.value)


class WriteOnlyKeyword(Keyword):
    __keyword__ = "writeOnly"
    __schema__ = {
        "type": "boolean",
        "default": False
    }

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        scope.annotate(instance, "writeOnly", self.json.value)


class ExamplesKeyword(Keyword):
    __keyword__ = "examples"
    __schema__ = {
        "type": "array",
        "items": True
    }

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        scope.annotate(instance, "examples", self.json.value)


class ContentMediaTypeKeyword(Keyword):
    __keyword__ = "contentMediaType"
    __schema__ = {"type": "string"}

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        scope.annotate(instance, "contentMediaType", self.json.value)


class ContentEncodingKeyword(Keyword):
    __keyword__ = "contentEncoding"
    __schema__ = {"type": "string"}

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        scope.annotate(instance, "contentEncoding", self.json.value)


class ContentSchemaKeyword(Keyword):
    __keyword__ = "contentSchema"
    __schema__ = {"$recursiveRef": "#"}
    __depends__ = "contentMediaType"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        scope.annotate(instance, "contentSchema", self.json.value)
