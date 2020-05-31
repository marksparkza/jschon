import re
import typing as _t

from jschon.json import JSON, JSONArray, JSONObject
from jschon.keywords import ApplicatorKeyword, PropertyApplicatorKeyword
from jschon.schema import Schema, KeywordResult, Keyword

__all__ = [
    'RefKeyword',
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
]


class RefKeyword(Keyword):
    __keyword__ = "$ref"
    __schema__ = {
        "type": "string",
        "format": "uri-reference"
    }

    def __init__(
            self,
            superschema: Schema,
            value: str,
    ) -> None:
        super().__init__(superschema, value)

    def evaluate(self, instance: JSON) -> KeywordResult:
        return KeywordResult(
            valid=True,
        )


class AllOfKeyword(ApplicatorKeyword):
    __keyword__ = "allOf"
    __schema__ = {
        "type": "array",
        "minItems": 1,
        "items": {"$recursiveRef": "#"}
    }

    def evaluate(self, instance: JSON) -> KeywordResult:
        result = KeywordResult(
            valid=True,
            subresults=[],
        )
        for subschema in self.subschemas:
            result.subresults += [subresult := subschema.evaluate(instance)]
            if not subresult.valid:
                result.valid = False
                result.error = "The instance must be valid against all subschemas"
                break

        return result


class AnyOfKeyword(ApplicatorKeyword):
    __keyword__ = "anyOf"
    __schema__ = {
        "type": "array",
        "minItems": 1,
        "items": {"$recursiveRef": "#"}
    }

    def evaluate(self, instance: JSON) -> KeywordResult:
        result = KeywordResult(
            valid=False,
            subresults=[],
        )
        for subschema in self.subschemas:
            result.subresults += [subresult := subschema.evaluate(instance)]
            if subresult.valid:
                result.valid = True

        if not result.valid:
            result.error = "The instance must be valid against at least one subschema"

        return result


class OneOfKeyword(ApplicatorKeyword):
    __keyword__ = "oneOf"
    __schema__ = {
        "type": "array",
        "minItems": 1,
        "items": {"$recursiveRef": "#"}
    }

    def evaluate(self, instance: JSON) -> KeywordResult:
        result = KeywordResult(
            valid=False,
            subresults=[],
        )
        valid = 0
        for subschema in self.subschemas:
            result.subresults += [subresult := subschema.evaluate(instance)]
            if subresult.valid:
                valid += 1

        if valid == 1:
            result.valid = True
        else:
            result.error = "The instance must be valid against exactly one subschema"

        return result


class NotKeyword(ApplicatorKeyword):
    __keyword__ = "not"
    __schema__ = {"$recursiveRef": "#"}

    def evaluate(self, instance: JSON) -> KeywordResult:
        return KeywordResult(
            valid=(valid := not (subresult := self.subschema.evaluate(instance)).valid),
            error="The instance must not be valid against the given subschema" if not valid else None,
            subresults=[subresult],
        )


class IfKeyword(ApplicatorKeyword):
    __keyword__ = "if"
    __schema__ = {"$recursiveRef": "#"}

    def evaluate(self, instance: JSON) -> KeywordResult:
        return KeywordResult(
            assert_=False,
            valid=(subresult := self.subschema.evaluate(instance)).valid,
            subresults=[subresult],
        )


class ThenKeyword(ApplicatorKeyword):
    __keyword__ = "then"
    __schema__ = {"$recursiveRef": "#"}
    __depends__ = "if"

    def evaluate(self, instance: JSON) -> _t.Optional[KeywordResult]:
        if (if_ := self.superschema.keywords.get("if")) and if_.result.valid:
            return KeywordResult(
                valid=(subresult := self.subschema.evaluate(instance)).valid,
                subresults=[subresult],
            )


class ElseKeyword(ApplicatorKeyword):
    __keyword__ = "else"
    __schema__ = {"$recursiveRef": "#"}
    __depends__ = "if"

    def evaluate(self, instance: JSON) -> _t.Optional[KeywordResult]:
        if (if_ := self.superschema.keywords.get("if")) and not if_.result.valid:
            return KeywordResult(
                valid=(subresult := self.subschema.evaluate(instance)).valid,
                subresults=[subresult],
            )


class DependentSchemasKeyword(PropertyApplicatorKeyword):
    __keyword__ = "dependentSchemas"
    __schema__ = {
        "type": "object",
        "additionalProperties": {"$recursiveRef": "#"}
    }
    __types__ = "object"

    def evaluate(self, instance: JSONObject) -> KeywordResult:
        result = KeywordResult(
            valid=True,
            annotation=[],
            subresults=[],
        )
        for name, subschema in self.subschemas.items():
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


class ItemsKeyword(ApplicatorKeyword):
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

    def evaluate(self, instance: JSONArray) -> KeywordResult:
        result = KeywordResult(
            valid=True,
            subresults=[],
        )
        if len(instance) > 0:
            if self.value is False:
                result.valid = False

            elif self.subschema is not None:
                result.annotation = True
                for item in instance:
                    result.subresults += [subresult := self.subschema.evaluate(item)]
                    if not subresult.valid:
                        result.valid = False
                        result.annotation = None
                        break

            elif self.subschemas is not None:
                for index, item in enumerate(instance[:len(self.subschemas)]):
                    result.annotation = index
                    result.subresults += [subresult := self.subschemas[index].evaluate(item)]
                    if not subresult.valid:
                        result.valid = False
                        result.annotation = None
                        break

        if not result.valid:
            result.error = "One or more array elements is invalid"

        return result


class AdditionalItemsKeyword(ApplicatorKeyword):
    __keyword__ = "additionalItems"
    __schema__ = {"$recursiveRef": "#"}
    __types__ = "array"
    __depends__ = "items"

    def evaluate(self, instance: JSONArray) -> _t.Optional[KeywordResult]:
        if (items := self.superschema.keywords.get("items")) and type(items.result.annotation) is int:
            result = KeywordResult(
                valid=True,
                subresults=[],
            )
            for index, item in enumerate(instance[items.result.annotation + 1:]):
                result.annotation = True
                result.subresults += [subresult := self.subschema.evaluate(item)]
                if not subresult.valid:
                    result.valid = False
                    result.annotation = None
                    result.error = "One or more array elements is invalid"
                    break

            return result


class UnevaluatedItemsKeyword(ApplicatorKeyword):
    __keyword__ = "unevaluatedItems"
    __schema__ = {"$recursiveRef": "#"}
    __types__ = "array"
    __depends__ = "items", "additionalItems", "if", "then", "else", "allOf", "anyOf", "oneOf", "not"

    def evaluate(self, instance: JSONArray) -> _t.Optional[KeywordResult]:
        # TODO:
        #  check annotation results for items, additionalItems and unevaluatedItems
        #  from adjacent in-place applicator keywords

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
                result.subresults += [subresult := self.subschema.evaluate(item)]
                if not subresult.valid:
                    result.valid = False
                    result.annotation = None
                    result.error = "One or more array elements is invalid"
                    break

            return result


class ContainsKeyword(ApplicatorKeyword):
    __keyword__ = "contains"
    __schema__ = {"$recursiveRef": "#"}
    __types__ = "array"

    def evaluate(self, instance: JSONArray) -> KeywordResult:
        result = KeywordResult(
            valid=False,
            annotation=0,
            subresults=[],
        )
        for item in instance:
            result.subresults += [subresult := self.subschema.evaluate(item)]
            if subresult.valid:
                result.valid = True
                result.annotation += 1

        if not result.valid:
            result.error = "The array does not contain a required element"

        return result


class PropertiesKeyword(PropertyApplicatorKeyword):
    __keyword__ = "properties"
    __schema__ = {
        "type": "object",
        "additionalProperties": {"$recursiveRef": "#"},
        "default": {}
    }
    __types__ = "object"

    def evaluate(self, instance: JSONObject) -> KeywordResult:
        result = KeywordResult(
            valid=True,
            annotation=[],
            subresults=[],
        )
        for name, item in instance.items():
            if name in self.subschemas:
                result.subresults += [subresult := self.subschemas[name].evaluate(item)]
                if subresult.valid:
                    result.annotation += [name]
                else:
                    result.valid = False
                    result.annotation = None
                    result.error = "One or more object properties is invalid"
                    break

        return result


class PatternPropertiesKeyword(PropertyApplicatorKeyword):
    __keyword__ = "patternProperties"
    __schema__ = {
        "type": "object",
        "additionalProperties": {"$recursiveRef": "#"},
        "propertyNames": {"format": "regex"},
        "default": {}
    }
    __types__ = "object"

    def evaluate(self, instance: JSONObject) -> KeywordResult:
        result = KeywordResult(
            valid=True,
            subresults=[],
        )
        matched_names = set()
        for name, item in instance.items():
            for regex, subschema in self.subschemas.items():
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


class AdditionalPropertiesKeyword(ApplicatorKeyword):
    __keyword__ = "additionalProperties"
    __schema__ = {"$recursiveRef": "#"}
    __types__ = "object"
    __depends__ = "properties", "patternProperties"

    def evaluate(self, instance: JSONObject) -> KeywordResult:
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
                result.subresults += [subresult := self.subschema.evaluate(item)]
                if subresult.valid:
                    result.annotation += [name]
                else:
                    result.valid = False
                    result.annotation = None
                    result.error = "One or more object properties is invalid"
                    break

        return result


class UnevaluatedPropertiesKeyword(ApplicatorKeyword):
    __keyword__ = "unevaluatedProperties"
    __schema__ = {"$recursiveRef": "#"}
    __types__ = "object"
    __depends__ = "properties", "patternProperties", "additionalProperties", "if", "then", "else", "dependentSchemas", "allOf", "anyOf", "oneOf", "not"

    def evaluate(self, instance: JSONObject) -> KeywordResult:
        # TODO:
        #  check annotation results for properties, patternProperties, additionalProperties
        #  and unevaluatedProperties from adjacent in-place applicator keywords

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
                result.subresults += [subresult := self.subschema.evaluate(item)]
                if subresult.valid:
                    result.annotation += [name]
                else:
                    result.valid = False
                    result.annotation = None
                    result.error = "One or more object properties is invalid"
                    break

        return result


class PropertyNamesKeyword(ApplicatorKeyword):
    __keyword__ = "propertyNames"
    __schema__ = {"$recursiveRef": "#"}
    __types__ = "object"

    def evaluate(self, instance: JSONObject) -> KeywordResult:
        return KeywordResult(
            valid=(valid := all(self.subschema.evaluate(JSON(name)).valid for name in instance)),
            error="One or more property names is invalid" if not valid else None,
        )
