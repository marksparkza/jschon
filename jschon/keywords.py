import re
from typing import *

import rfc3986
import rfc3986.exceptions
import rfc3986.validators

from jschon.jsonpointer import JSONPointer
from jschon.exceptions import *
from jschon.json import *
from jschon.jsonschema import *
from jschon.types import tuplify, arrayify

__all__ = [
    # core vocabulary
    'SchemaKeyword',
    'VocabularyKeyword',
    'IdKeyword',
    'RefKeyword',
    'RecursiveRefKeyword',
    'DefsKeyword',

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

    # meta-data vocabulary

    # format vocabulary
    'FormatKeyword',

    # content vocabulary

]


class SchemaKeyword(Keyword):
    __keyword__ = "$schema"
    __schema__ = {
        "type": "string",
        "format": "uri"
    }

    def __init__(
            self,
            superschema: JSONSchema,
            value: str,
    ) -> None:
        if superschema.superkeyword is not None:
            raise SchemaError('The "$schema" keyword must not appear in a subschema')

        super().__init__(superschema, value)

        validator = rfc3986.validators.Validator().require_presence_of('scheme')
        try:
            validator.validate(uri_ref := rfc3986.uri_reference(value))
        except rfc3986.exceptions.ValidationError as e:
            raise SchemaError(f"'{value}' is not a valid URI or does not contain a scheme") from e

        if uri_ref != uri_ref.normalize():
            raise SchemaError(f"'{value}' is not normalized")

        superschema.metaschema_uri = uri_ref


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
            superschema: JSONSchema,
            value: JSONObject[JSONBoolean],
    ) -> None:
        if superschema.superkeyword is not None:
            raise SchemaError('The "$vocabulary" keyword must not appear in a subschema')

        super().__init__(superschema, value)

        for vocab_uri, vocab_required in value.items():
            validator = rfc3986.validators.Validator().require_presence_of('scheme')
            try:
                validator.validate(uri_ref := rfc3986.uri_reference(vocab_uri))
            except rfc3986.exceptions.ValidationError as e:
                raise SchemaError(f"'{vocab_uri}' is not a valid URI or does not contain a scheme") from e

            if uri_ref != uri_ref.normalize():
                raise SchemaError(f"'{vocab_uri}' is not normalized")

            if not isinstance(vocab_required, bool):
                raise SchemaError('"$vocabulary" values must be booleans')

            try:
                vocabulary = Vocabulary(vocab_uri, vocab_required)
                self.superschema.kwclasses.update(vocabulary.kwclasses)
            except VocabularyError as e:
                if vocab_required:
                    raise SchemaError(f"The metaschema requires an unrecognized vocabulary '{vocab_uri}'") from e


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
            superschema: JSONSchema,
            value: str,
    ) -> None:
        super().__init__(superschema, value)
        if not (uri_ref := rfc3986.uri_reference(value)).is_absolute():
            if not superschema.location:
                raise SchemaError('The "$id" of the root schema, if present, must be an absolute URI')
            if (base_uri := superschema.base_uri) is not None:
                uri_ref = uri_ref.resolve_with(base_uri)
            else:
                raise SchemaError(f'No base URI against which to resolve the "$id" value "{value}"')

        superschema.base_uri = uri_ref


class RefKeyword(Keyword):
    __keyword__ = "$ref"
    __schema__ = {
        "type": "string",
        "format": "uri-reference"
    }

    def __init__(
            self,
            superschema: JSONSchema,
            value: str,
    ) -> None:
        super().__init__(superschema, value)
        self.refschema: JSONSchema

        uri, _, fragment = value.partition('#')
        uri_ref = rfc3986.uri_reference(uri)
        if (base_uri := self.superschema.base_uri) is not None:
            uri_ref = uri_ref.resolve_with(base_uri)
        if uri_ref.is_absolute():
            schema = JSONSchema.get(uri_ref)
        elif not uri:
            schema = self.superschema.rootschema
        else:
            raise SchemaError(f'Unable to determine schema resource referenced by "{value}"')

        ref = JSONPointer.parse_uri_fragment(f'#{fragment}')
        self.refschema = ref.evaluate(schema)

        if not isinstance(self.refschema, JSONSchema):
            raise SchemaError(f'The value referenced by "{value}" is not a JSON Schema')

    def evaluate(self, instance: JSON) -> KeywordResult:
        return KeywordResult(
            valid=(valid := (subresult := self.refschema.evaluate(instance)).valid),
            error="The instance is invalid against the referenced schema" if not valid else None,
            subresults=[subresult],
        )


class RecursiveRefKeyword(Keyword):
    __keyword__ = "$recursiveRef"
    __schema__ = {
        "type": "string",
        "format": "uri-reference"
    }

    def __init__(
            self,
            superschema: JSONSchema,
            value: str,
    ) -> None:
        super().__init__(superschema, value)
        if value != '#':
            raise SchemaError('The "$recursiveRef" keyword may only take the value "#"')

        self.refschema: JSONSchema = superschema.rootschema

    def evaluate(self, instance: JSON) -> KeywordResult:
        return KeywordResult(
            valid=(valid := (subresult := self.refschema.evaluate(instance)).valid),
            error="The instance is invalid against the referenced schema" if not valid else None,
            subresults=[subresult],
        )


class DefsKeyword(Keyword):
    __keyword__ = "$defs"
    __schema__ = {
        "type": "object",
        "additionalProperties": {"$recursiveRef": "#"},
        "default": {}
    }
    applicators = PropertyApplicator,


class AllOfKeyword(Keyword):
    __keyword__ = "allOf"
    __schema__ = {
        "type": "array",
        "minItems": 1,
        "items": {"$recursiveRef": "#"}
    }

    applicators = ArrayApplicator,

    def evaluate(self, instance: JSON) -> KeywordResult:
        self.json: JSONArray[JSONSchema]
        result = KeywordResult(
            valid=True,
            subresults=[],
        )
        for subschema in self.json:
            result.subresults += [subresult := subschema.evaluate(instance)]
            if not subresult.valid:
                result.valid = False
                result.error = "The instance must be valid against all subschemas"
                break

        return result


class AnyOfKeyword(Keyword):
    __keyword__ = "anyOf"
    __schema__ = {
        "type": "array",
        "minItems": 1,
        "items": {"$recursiveRef": "#"}
    }

    applicators = ArrayApplicator,

    def evaluate(self, instance: JSON) -> KeywordResult:
        self.json: JSONArray[JSONSchema]
        result = KeywordResult(
            valid=False,
            subresults=[],
        )
        for subschema in self.json:
            result.subresults += [subresult := subschema.evaluate(instance)]
            if subresult.valid:
                result.valid = True

        if not result.valid:
            result.error = "The instance must be valid against at least one subschema"

        return result


class OneOfKeyword(Keyword):
    __keyword__ = "oneOf"
    __schema__ = {
        "type": "array",
        "minItems": 1,
        "items": {"$recursiveRef": "#"}
    }

    applicators = ArrayApplicator,

    def evaluate(self, instance: JSON) -> KeywordResult:
        self.json: JSONArray[JSONSchema]
        result = KeywordResult(
            valid=False,
            subresults=[],
        )
        valid = 0
        for subschema in self.json:
            result.subresults += [subresult := subschema.evaluate(instance)]
            if subresult.valid:
                valid += 1

        if valid == 1:
            result.valid = True
        else:
            result.error = "The instance must be valid against exactly one subschema"

        return result


class NotKeyword(Keyword):
    __keyword__ = "not"
    __schema__ = {"$recursiveRef": "#"}

    applicators = Applicator,

    def evaluate(self, instance: JSON) -> KeywordResult:
        self.json: JSONSchema
        return KeywordResult(
            valid=(valid := not (subresult := self.json.evaluate(instance)).valid),
            error="The instance must not be valid against the given subschema" if not valid else None,
            subresults=[subresult],
        )


class IfKeyword(Keyword):
    __keyword__ = "if"
    __schema__ = {"$recursiveRef": "#"}

    applicators = Applicator,

    @property
    def assert_(self):
        return False

    def evaluate(self, instance: JSON) -> KeywordResult:
        self.json: JSONSchema
        return KeywordResult(
            valid=(subresult := self.json.evaluate(instance)).valid,
            subresults=[subresult],
        )


class ThenKeyword(Keyword):
    __keyword__ = "then"
    __schema__ = {"$recursiveRef": "#"}
    __depends__ = "if"

    applicators = Applicator,

    def evaluate(self, instance: JSON) -> Optional[KeywordResult]:
        self.json: JSONSchema
        if (if_ := self.superschema.keywords.get("if")) and if_.result.valid:
            return KeywordResult(
                valid=(subresult := self.json.evaluate(instance)).valid,
                subresults=[subresult],
            )


class ElseKeyword(Keyword):
    __keyword__ = "else"
    __schema__ = {"$recursiveRef": "#"}
    __depends__ = "if"

    applicators = Applicator,

    def evaluate(self, instance: JSON) -> Optional[KeywordResult]:
        self.json: JSONSchema
        if (if_ := self.superschema.keywords.get("if")) and not if_.result.valid:
            return KeywordResult(
                valid=(subresult := self.json.evaluate(instance)).valid,
                subresults=[subresult],
            )


class DependentSchemasKeyword(Keyword):
    __keyword__ = "dependentSchemas"
    __schema__ = {
        "type": "object",
        "additionalProperties": {"$recursiveRef": "#"}
    }
    __types__ = "object"

    applicators = PropertyApplicator,

    def evaluate(self, instance: JSONObject) -> KeywordResult:
        self.json: JSONObject[JSONSchema]
        result = KeywordResult(
            valid=True,
            annotation=[],
            subresults=[],
        )
        for name, subschema in self.json.items():
            if name in instance:
                result.subresults += [subresult := subschema.evaluate(instance)]
                if subresult.valid:
                    result.annotation += [name]
                else:
                    result.valid = False
                    result.annotation = None
                    result.error = f'The instance is invalid against the "{name}" subschema'
                    break

        return result


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

    def evaluate(self, instance: JSONArray) -> KeywordResult:
        result = KeywordResult(
            valid=True,
            subresults=[],
        )
        if len(instance) > 0:
            if isinstance(self.json, JSONBooleanSchema) and self.json.value is False:
                result.valid = False

            elif isinstance(self.json, JSONSchema):
                result.annotation = True
                for item in instance:
                    result.subresults += [subresult := self.json.evaluate(item)]
                    if not subresult.valid:
                        result.valid = False
                        result.annotation = None
                        break

            elif isinstance(self.json, JSONArray):
                self.json: JSONArray[JSONSchema]
                for index, item in enumerate(instance[:len(self.json)]):
                    result.annotation = index
                    result.subresults += [subresult := self.json[index].evaluate(item)]
                    if not subresult.valid:
                        result.valid = False
                        result.annotation = None
                        break

        if not result.valid:
            result.error = "One or more array elements is invalid"

        return result


class AdditionalItemsKeyword(Keyword):
    __keyword__ = "additionalItems"
    __schema__ = {"$recursiveRef": "#"}
    __types__ = "array"
    __depends__ = "items"

    applicators = Applicator,

    def evaluate(self, instance: JSONArray) -> Optional[KeywordResult]:
        self.json: JSONSchema
        if (items := self.superschema.keywords.get("items")) and type(items.result.annotation) is int:
            result = KeywordResult(
                valid=True,
                subresults=[],
            )
            for index, item in enumerate(instance[items.result.annotation + 1:]):
                result.annotation = True
                result.subresults += [subresult := self.json.evaluate(item)]
                if not subresult.valid:
                    result.valid = False
                    result.annotation = None
                    result.error = "One or more array elements is invalid"
                    break

            return result


class UnevaluatedItemsKeyword(Keyword):
    __keyword__ = "unevaluatedItems"
    __schema__ = {"$recursiveRef": "#"}
    __types__ = "array"
    __depends__ = "items", "additionalItems", "if", "then", "else", "allOf", "anyOf", "oneOf", "not"

    applicators = Applicator,

    def evaluate(self, instance: JSONArray) -> Optional[KeywordResult]:
        # TODO:
        #  check annotation results for items, additionalItems and unevaluatedItems
        #  from adjacent in-place applicator keywords
        self.json: JSONSchema
        items = self.superschema.keywords.get("items")
        additional_items = self.superschema.keywords.get("additionalItems")

        if items and type(items.result.annotation) is int and \
                (not additional_items or additional_items.result.annotation is None):
            result = KeywordResult(
                valid=True,
                subresults=[],
            )
            for index, item in enumerate(instance[items.result.annotation + 1:]):
                result.annotation = True
                result.subresults += [subresult := self.json.evaluate(item)]
                if not subresult.valid:
                    result.valid = False
                    result.annotation = None
                    result.error = "One or more array elements is invalid"
                    break

            return result


class ContainsKeyword(Keyword):
    __keyword__ = "contains"
    __schema__ = {"$recursiveRef": "#"}
    __types__ = "array"

    applicators = Applicator,

    def evaluate(self, instance: JSONArray) -> KeywordResult:
        self.json: JSONSchema
        result = KeywordResult(
            valid=False,
            annotation=0,
            subresults=[],
        )
        for item in instance:
            result.subresults += [subresult := self.json.evaluate(item)]
            if subresult.valid:
                result.valid = True
                result.annotation += 1

        if not result.valid:
            result.error = "The array does not contain a required element"

        return result


class PropertiesKeyword(Keyword):
    __keyword__ = "properties"
    __schema__ = {
        "type": "object",
        "additionalProperties": {"$recursiveRef": "#"},
        "default": {}
    }
    __types__ = "object"

    applicators = PropertyApplicator,

    def evaluate(self, instance: JSONObject) -> KeywordResult:
        self.json: JSONObject[JSONSchema]
        result = KeywordResult(
            valid=True,
            annotation=[],
            subresults=[],
        )
        for name, item in instance.items():
            if name in self.json:
                result.subresults += [subresult := self.json[name].evaluate(item)]
                if subresult.valid:
                    result.annotation += [name]
                else:
                    result.valid = False
                    result.annotation = None
                    result.error = "One or more object properties is invalid"
                    break

        return result


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

    def evaluate(self, instance: JSONObject) -> KeywordResult:
        self.json: JSONObject[JSONSchema]
        result = KeywordResult(
            valid=True,
            subresults=[],
        )
        matched_names = set()
        for name, item in instance.items():
            for regex, subschema in self.json.items():
                if re.search(regex, name) is not None:
                    result.subresults += [subresult := subschema.evaluate(item)]
                    if subresult.valid:
                        matched_names |= {name}
                    else:
                        result.valid = False
                        result.error = "One or more object properties is invalid"
                        break
            if not result.valid:
                break

        if result.valid:
            result.annotation = list(matched_names)

        return result


class AdditionalPropertiesKeyword(Keyword):
    __keyword__ = "additionalProperties"
    __schema__ = {"$recursiveRef": "#"}
    __types__ = "object"
    __depends__ = "properties", "patternProperties"

    applicators = Applicator,

    def evaluate(self, instance: JSONObject) -> KeywordResult:
        self.json: JSONSchema

        evaluated_names = set()
        if properties := self.superschema.keywords.get("properties"):
            evaluated_names |= set(properties.result.annotation or ())
        if pattern_properties := self.superschema.keywords.get("patternProperties"):
            evaluated_names |= set(pattern_properties.result.annotation or ())

        result = KeywordResult(
            valid=True,
            annotation=[],
            subresults=[],
        )
        for name, item in instance.items():
            if name not in evaluated_names:
                result.subresults += [subresult := self.json.evaluate(item)]
                if subresult.valid:
                    result.annotation += [name]
                else:
                    result.valid = False
                    result.annotation = None
                    result.error = "One or more object properties is invalid"
                    break

        return result


class UnevaluatedPropertiesKeyword(Keyword):
    __keyword__ = "unevaluatedProperties"
    __schema__ = {"$recursiveRef": "#"}
    __types__ = "object"
    __depends__ = "properties", "patternProperties", "additionalProperties", "if", "then", "else", \
                  "dependentSchemas", "allOf", "anyOf", "oneOf", "not"

    applicators = Applicator,

    def evaluate(self, instance: JSONObject) -> KeywordResult:
        # TODO:
        #  check annotation results for properties, patternProperties, additionalProperties
        #  and unevaluatedProperties from adjacent in-place applicator keywords
        self.json: JSONSchema

        evaluated_names = set()
        if properties := self.superschema.keywords.get("properties"):
            evaluated_names |= set(properties.result.annotation or ())
        if pattern_properties := self.superschema.keywords.get("patternProperties"):
            evaluated_names |= set(pattern_properties.result.annotation or ())
        if additional_properties := self.superschema.keywords.get("additionalProperties"):
            evaluated_names |= set(additional_properties.result.annotation or ())

        result = KeywordResult(
            valid=True,
            annotation=[],
            subresults=[],
        )
        for name, item in instance.items():
            if name not in evaluated_names:
                result.subresults += [subresult := self.json.evaluate(item)]
                if subresult.valid:
                    result.annotation += [name]
                else:
                    result.valid = False
                    result.annotation = None
                    result.error = "One or more object properties is invalid"
                    break

        return result


class PropertyNamesKeyword(Keyword):
    __keyword__ = "propertyNames"
    __schema__ = {"$recursiveRef": "#"}
    __types__ = "object"

    applicators = Applicator,

    def evaluate(self, instance: JSONObject) -> KeywordResult:
        self.json: JSONSchema
        return KeywordResult(
            valid=(valid := all(self.json.evaluate(JSON(name)).valid for name in instance)),
            error="One or more property names is invalid" if not valid else None,
        )


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
            superschema: JSONSchema,
            value: Union[str, Sequence[str]],
    ) -> None:
        super().__init__(superschema, arrayify(value))

    def evaluate(self, instance: JSON) -> KeywordResult:
        self.json: JSONArray[JSONString]
        return KeywordResult(
            valid=(valid := any(instance.istype(item.value) for item in self.json)),
            error=f"The value must be of type {self.json}" if not valid else None,
        )


class EnumKeyword(Keyword):
    __keyword__ = "enum"
    __schema__ = {"type": "array", "items": True}

    def evaluate(self, instance: JSON) -> KeywordResult:
        self.json: JSONArray
        return KeywordResult(
            valid=(valid := instance in self.json),
            error=f"The value must be one of {self.json}" if not valid else None,
        )


class ConstKeyword(Keyword):
    __keyword__ = "const"
    __schema__ = True

    def evaluate(self, instance: JSON) -> KeywordResult:
        return KeywordResult(
            valid=(valid := instance == self.json),
            error=f"The value must be equal to {self.json}" if not valid else None,
        )


class MultipleOfKeyword(Keyword):
    __keyword__ = "multipleOf"
    __schema__ = {"type": "number", "exclusiveMinimum": 0}
    __types__ = "number"

    def evaluate(self, instance: JSONNumber) -> KeywordResult:
        self.json: JSONNumber
        return KeywordResult(
            valid=(valid := instance % self.json == 0),
            error=f"The value must be a multiple of {self.json}" if not valid else None,
        )


class MaximumKeyword(Keyword):
    __keyword__ = "maximum"
    __schema__ = {"type": "number"}
    __types__ = "number"

    def evaluate(self, instance: JSONNumber) -> KeywordResult:
        self.json: JSONNumber
        return KeywordResult(
            valid=(valid := instance <= self.json),
            error=f"The value may not be greater than {self.json}" if not valid else None,
        )


class ExclusiveMaximumKeyword(Keyword):
    __keyword__ = "exclusiveMaximum"
    __schema__ = {"type": "number"}
    __types__ = "number"

    def evaluate(self, instance: JSONNumber) -> KeywordResult:
        self.json: JSONNumber
        return KeywordResult(
            valid=(valid := instance < self.json),
            error=f"The value must be less than {self.json}" if not valid else None,
        )


class MinimumKeyword(Keyword):
    __keyword__ = "minimum"
    __schema__ = {"type": "number"}
    __types__ = "number"

    def evaluate(self, instance: JSONNumber) -> KeywordResult:
        self.json: JSONNumber
        return KeywordResult(
            valid=(valid := instance >= self.json),
            error=f"The value may not be less than {self.json}" if not valid else None,
        )


class ExclusiveMinimumKeyword(Keyword):
    __keyword__ = "exclusiveMinimum"
    __schema__ = {"type": "number"}
    __types__ = "number"

    def evaluate(self, instance: JSONNumber) -> KeywordResult:
        self.json: JSONNumber
        return KeywordResult(
            valid=(valid := instance > self.json),
            error=f"The value must be greater than {self.json}" if not valid else None,
        )


class MaxLengthKeyword(Keyword):
    __keyword__ = "maxLength"
    __schema__ = {"type": "integer", "minimum": 0}
    __types__ = "string"

    def evaluate(self, instance: JSONString) -> KeywordResult:
        self.json: JSONInteger
        return KeywordResult(
            valid=(valid := len(instance) <= self.json),
            error=f"The text is too long (maximum {self.json} characters)" if not valid else None,
        )


class MinLengthKeyword(Keyword):
    __keyword__ = "minLength"
    __schema__ = {"type": "integer", "minimum": 0, "default": 0}
    __types__ = "string"

    def evaluate(self, instance: JSONString) -> KeywordResult:
        self.json: JSONInteger
        return KeywordResult(
            valid=(valid := len(instance) >= self.json),
            error=f"The text is too short (minimum {self.json} characters)" if not valid else None,
        )


class PatternKeyword(Keyword):
    __keyword__ = "pattern"
    __schema__ = {"type": "string", "format": "regex"}
    __types__ = "string"

    def __init__(
            self,
            superschema: JSONSchema,
            value: str,
    ) -> None:
        super().__init__(superschema, value)
        self.regex = re.compile(value)

    def evaluate(self, instance: JSONString) -> KeywordResult:
        return KeywordResult(
            valid=(valid := self.regex.search(instance.value) is not None),
            error=f"The text must match the regular expression {self.json}" if not valid else None,
        )


class MaxItemsKeyword(Keyword):
    __keyword__ = "maxItems"
    __schema__ = {"type": "integer", "minimum": 0}
    __types__ = "array"

    def evaluate(self, instance: JSONArray) -> KeywordResult:
        self.json: JSONInteger
        return KeywordResult(
            valid=(valid := len(instance) <= self.json),
            error=f"The array has too many elements (maximum {self.json})" if not valid else None,
        )


class MinItemsKeyword(Keyword):
    __keyword__ = "minItems"
    __schema__ = {"type": "integer", "minimum": 0, "default": 0}
    __types__ = "array"

    def evaluate(self, instance: JSONArray) -> KeywordResult:
        self.json: JSONInteger
        return KeywordResult(
            valid=(valid := len(instance) >= self.json),
            error=f"The array has too few elements (minimum {self.json})" if not valid else None,
        )


class UniqueItemsKeyword(Keyword):
    __keyword__ = "uniqueItems"
    __schema__ = {"type": "boolean", "default": False}
    __types__ = "array"

    def evaluate(self, instance: JSONArray) -> KeywordResult:
        self.json: JSONBoolean
        if not self.json.value:
            return KeywordResult(valid=True)

        uniquified = []
        for item in instance:
            if item not in uniquified:
                uniquified += [item]

        return KeywordResult(
            valid=(valid := len(instance) == len(uniquified)),
            error="The array's elements must all be unique" if not valid else None,
        )


class MaxContainsKeyword(Keyword):
    __keyword__ = "maxContains"
    __schema__ = {"type": "integer", "minimum": 0}
    __types__ = "array"
    __depends__ = "contains"

    def evaluate(self, instance: JSONArray) -> Optional[KeywordResult]:
        self.json: JSONInteger
        if contains := self.superschema.keywords.get("contains"):
            return KeywordResult(
                valid=(valid := contains.result.annotation <= self.json),
                error=f'The array has too many elements matching the "contains" subschema '
                      f'(maximum {self.json})' if not valid else None,
            )


class MinContainsKeyword(Keyword):
    __keyword__ = "minContains"
    __schema__ = {"type": "integer", "minimum": 0, "default": 1}
    __types__ = "array"
    __depends__ = "contains", "maxContains"

    def evaluate(self, instance: JSONArray) -> Optional[KeywordResult]:
        self.json: JSONInteger
        if contains := self.superschema.keywords.get("contains"):
            valid = contains.result.annotation >= self.json

            if valid and not contains.result.valid:
                max_contains = self.superschema.keywords.get("maxContains")
                if not max_contains or max_contains.result.valid:
                    contains.result.valid = True

            return KeywordResult(
                valid=valid,
                error=f'The array has too few elements matching the "contains" subschema '
                      f'(minimum {self.json})' if not valid else None,
            )


class MaxPropertiesKeyword(Keyword):
    __keyword__ = "maxProperties"
    __schema__ = {"type": "integer", "minimum": 0}
    __types__ = "object"

    def evaluate(self, instance: JSONObject) -> KeywordResult:
        self.json: JSONInteger
        return KeywordResult(
            valid=(valid := len(instance) <= self.json),
            error=f"The object has too many properties (maximum {self.json})" if not valid else None,
        )


class MinPropertiesKeyword(Keyword):
    __keyword__ = "minProperties"
    __schema__ = {"type": "integer", "minimum": 0, "default": 0}
    __types__ = "object"

    def evaluate(self, instance: JSONObject) -> KeywordResult:
        self.json: JSONInteger
        return KeywordResult(
            valid=(valid := len(instance) >= self.json),
            error=f"The object has too few properties (minimum {self.json})" if not valid else None,
        )


class RequiredKeyword(Keyword):
    __keyword__ = "required"
    __schema__ = {
        "type": "array",
        "items": {"type": "string"},
        "uniqueItems": True,
        "default": []
    }
    __types__ = "object"

    def evaluate(self, instance: JSONObject) -> KeywordResult:
        self.json: JSONArray[JSONString]

        missing = [name for name in self.json if name.value not in instance]
        return KeywordResult(
            valid=(valid := len(missing) == 0),
            error=f"The object is missing required properties {missing}" if not valid else None,
        )


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

    def evaluate(self, instance: JSONObject) -> KeywordResult:
        self.json: JSONObject[JSONArray[JSONString]]

        missing = {}
        for name, dependents in self.json.items():
            if name in instance:
                missing_deps = [dep for dep in dependents if dep.value not in instance]
                if missing_deps:
                    missing[name] = missing_deps

        return KeywordResult(
            valid=(valid := len(missing) == 0),
            error=f"The object is missing dependent properties {missing}" if not valid else None,
        )


class FormatKeyword(Keyword):
    __keyword__ = "format"
    __schema__ = {"type": "string"}

    def __init__(
            self,
            superschema: JSONSchema,
            value: str,
    ) -> None:
        super().__init__(superschema, value)
        vocabulary = FormatVocabulary.get(self.vocabulary_uri)
        self.format_: Optional[Format] = vocabulary.formats.get(self.json.value)

    @property
    def assert_(self) -> bool:
        return self.format_.assert_ if self.format_ else False

    def evaluate(self, instance: JSON) -> KeywordResult:
        result = KeywordResult(
            valid=True,
            annotation=self.json,
        )
        if self.format_ and isinstance(instance, tuple(JSON.classfor(t) for t in tuplify(self.format_.__types__))):
            fmtresult = self.format_.evaluate(instance)
            if not fmtresult.valid:
                result.valid = False
                result.error = f'The text does not conform to the {self.json} format: {fmtresult.error}'

        return result
