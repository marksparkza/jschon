import re
import typing as _t

from jschon.json import *
from jschon.pointer import Pointer
from jschon.schema import Schema, Keyword, KeywordResult
from jschon.types import SchemaCompatible

__all__ = [
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


class AllOfKeyword(Keyword):
    __keyword__ = "allOf"
    __schema__ = {
        "type": "array",
        "minItems": 1,
        "items": {"$recursiveRef": "#"}
    }
    __types__ = JSON

    def __init__(
            self,
            superschema: Schema,
            value: _t.Sequence['SchemaCompatible'],
    ) -> None:
        super().__init__(superschema, value)
        self.subschemas = [
            Schema(item, location=self.location + Pointer(f'/{index}'), metaschema_uri=superschema.metaschema.uri)
            for index, item in enumerate(value)
        ]

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


class AnyOfKeyword(Keyword):
    __keyword__ = "anyOf"
    __schema__ = {
        "type": "array",
        "minItems": 1,
        "items": {"$recursiveRef": "#"}
    }
    __types__ = JSON

    def __init__(
            self,
            superschema: Schema,
            value: _t.Sequence['SchemaCompatible'],
    ) -> None:
        super().__init__(superschema, value)
        self.subschemas = [
            Schema(item, location=self.location + Pointer(f'/{index}'), metaschema_uri=superschema.metaschema.uri)
            for index, item in enumerate(value)
        ]

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


class OneOfKeyword(Keyword):
    __keyword__ = "oneOf"
    __schema__ = {
        "type": "array",
        "minItems": 1,
        "items": {"$recursiveRef": "#"}
    }
    __types__ = JSON

    def __init__(
            self,
            superschema: Schema,
            value: _t.Sequence['SchemaCompatible'],
    ) -> None:
        super().__init__(superschema, value)
        self.subschemas = [
            Schema(item, location=self.location + Pointer(f'/{index}'), metaschema_uri=superschema.metaschema.uri)
            for index, item in enumerate(value)
        ]

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


class NotKeyword(Keyword):
    __keyword__ = "not"
    __schema__ = {"$recursiveRef": "#"}
    __types__ = JSON

    def __init__(
            self,
            superschema: Schema,
            value: SchemaCompatible,
    ) -> None:
        super().__init__(superschema, value)
        self.subschema = Schema(value, location=self.location, metaschema_uri=superschema.metaschema.uri)

    def evaluate(self, instance: JSON) -> KeywordResult:
        return KeywordResult(
            valid=(valid := not (subresult := self.subschema.evaluate(instance)).valid),
            error="The instance must not be valid against the given subschema" if not valid else None,
            subresults=[subresult],
        )


class IfKeyword(Keyword):
    __keyword__ = "if"
    __schema__ = {"$recursiveRef": "#"}
    __types__ = JSON

    def __init__(
            self,
            superschema: Schema,
            value: SchemaCompatible,
    ) -> None:
        super().__init__(superschema, value)
        self.subschema = Schema(value, location=self.location, metaschema_uri=superschema.metaschema.uri)

    def evaluate(self, instance: JSON) -> KeywordResult:
        raise NotImplementedError


class ThenKeyword(Keyword):
    __keyword__ = "then"
    __schema__ = {"$recursiveRef": "#"}
    __types__ = JSON

    def __init__(
            self,
            superschema: Schema,
            value: SchemaCompatible,
    ) -> None:
        super().__init__(superschema, value)
        self.subschema = Schema(value, location=self.location, metaschema_uri=superschema.metaschema.uri)

    def evaluate(self, instance: JSON) -> KeywordResult:
        raise NotImplementedError


class ElseKeyword(Keyword):
    __keyword__ = "else"
    __schema__ = {"$recursiveRef": "#"}
    __types__ = JSON

    def __init__(
            self,
            superschema: Schema,
            value: SchemaCompatible,
    ) -> None:
        super().__init__(superschema, value)
        self.subschema = Schema(value, location=self.location, metaschema_uri=superschema.metaschema.uri)

    def evaluate(self, instance: JSON) -> KeywordResult:
        raise NotImplementedError


class DependentSchemasKeyword(Keyword):
    __keyword__ = "dependentSchemas"
    __schema__ = {
        "type": "object",
        "additionalProperties": {"$recursiveRef": "#"}
    }
    __types__ = JSONObject

    def __init__(
            self,
            superschema: Schema,
            value: _t.Mapping[str, 'SchemaCompatible'],
    ) -> None:
        super().__init__(superschema, value)
        self.subschemas = {
            name: Schema(item, location=self.location + Pointer(f'/{name}'), metaschema_uri=superschema.metaschema.uri)
            for name, item in value.items()
        }

    def evaluate(self, instance: JSONObject) -> KeywordResult:
        raise NotImplementedError


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
    __types__ = JSONArray

    def __init__(
            self,
            superschema: Schema,
            value: _t.Union['SchemaCompatible', _t.Sequence['SchemaCompatible']],
    ) -> None:
        super().__init__(superschema, value)
        if isinstance(value, _t.Mapping):
            self.subschema = Schema(value, location=self.location, metaschema_uri=superschema.metaschema.uri)
        elif isinstance(value, _t.Sequence):
            self.subschemas = [
                Schema(item, location=self.location + Pointer(f'/{index}'), metaschema_uri=superschema.metaschema.uri)
                for index, item in enumerate(value)
            ]

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
                for index, item in enumerate(instance):
                    if index < len(self.subschemas):
                        result.annotation = index
                        result.subresults += [subresult := self.subschemas[index].evaluate(item)]
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
    __types__ = JSONArray

    def __init__(
            self,
            superschema: Schema,
            value: SchemaCompatible,
    ) -> None:
        super().__init__(superschema, value)
        self.subschema = Schema(value, location=self.location, metaschema_uri=superschema.metaschema.uri)

    def evaluate(self, instance: JSONArray) -> KeywordResult:
        raise NotImplementedError


class UnevaluatedItemsKeyword(Keyword):
    __keyword__ = "unevaluatedItems"
    __schema__ = {"$recursiveRef": "#"}
    __types__ = JSONArray

    def __init__(
            self,
            superschema: Schema,
            value: SchemaCompatible,
    ) -> None:
        super().__init__(superschema, value)
        self.subschema = Schema(value, location=self.location, metaschema_uri=superschema.metaschema.uri)

    def evaluate(self, instance: JSONArray) -> KeywordResult:
        raise NotImplementedError


class ContainsKeyword(Keyword):
    __keyword__ = "contains"
    __schema__ = {"$recursiveRef": "#"}
    __types__ = JSONArray

    def __init__(
            self,
            superschema: Schema,
            value: SchemaCompatible,
    ) -> None:
        super().__init__(superschema, value)
        self.subschema = Schema(value, location=self.location, metaschema_uri=superschema.metaschema.uri)

    def evaluate(self, instance: JSONArray) -> KeywordResult:
        result = KeywordResult(
            valid=False,
            subresults=[],
        )
        for item in instance:
            result.subresults += [subresult := self.subschema.evaluate(item)]
            if subresult.valid:
                result.valid = True

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
    __types__ = JSONObject

    def __init__(
            self,
            superschema: Schema,
            value: _t.Mapping[str, 'SchemaCompatible'],
    ) -> None:
        super().__init__(superschema, value)
        self.subschemas = {
            name: Schema(item, location=self.location + Pointer(f'/{name}'), metaschema_uri=superschema.metaschema.uri)
            for name, item in value.items()
        }

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


class PatternPropertiesKeyword(Keyword):
    __keyword__ = "patternProperties"
    __schema__ = {
        "type": "object",
        "additionalProperties": {"$recursiveRef": "#"},
        "propertyNames": {"format": "regex"},
        "default": {}
    }
    __types__ = JSONObject

    def __init__(
            self,
            superschema: Schema,
            value: _t.Mapping[str, 'SchemaCompatible'],
    ) -> None:
        super().__init__(superschema, value)
        self.subschemas = {
            re.compile(name): Schema(item, location=self.location + Pointer(f'/{name}'), metaschema_uri=superschema.metaschema.uri)
            for name, item in value.items()
        }

    def evaluate(self, instance: JSONObject) -> KeywordResult:
        result = KeywordResult(
            valid=True,
            subresults=[],
        )
        matched_names = set()
        for name, item in instance.items():
            for regex, subschema in self.subschemas.items():
                if regex.search(name) is not None:
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
    __types__ = JSONObject

    def __init__(
            self,
            superschema: Schema,
            value: SchemaCompatible,
    ) -> None:
        super().__init__(superschema, value)
        self.subschema = Schema(value, location=self.location, metaschema_uri=superschema.metaschema.uri)

    def evaluate(self, instance: JSONObject) -> KeywordResult:
        raise NotImplementedError


class UnevaluatedPropertiesKeyword(Keyword):
    __keyword__ = "unevaluatedProperties"
    __schema__ = {"$recursiveRef": "#"}
    __types__ = JSONObject

    def __init__(
            self,
            superschema: Schema,
            value: SchemaCompatible,
    ) -> None:
        super().__init__(superschema, value)
        self.subschema = Schema(value, location=self.location, metaschema_uri=superschema.metaschema.uri)

    def evaluate(self, instance: JSONObject) -> KeywordResult:
        raise NotImplementedError


class PropertyNamesKeyword(Keyword):
    __keyword__ = "propertyNames"
    __schema__ = {"$recursiveRef": "#"}
    __types__ = JSONObject

    def __init__(
            self,
            superschema: Schema,
            value: SchemaCompatible,
    ) -> None:
        super().__init__(superschema, value)
        self.subschema = Schema(value, location=self.location, metaschema_uri=superschema.metaschema.uri)

    def evaluate(self, instance: JSONObject) -> KeywordResult:
        return KeywordResult(
            valid=(valid := all(self.subschema.evaluate(JSON(name)).valid for name in instance)),
            error="One or more property names is invalid" if not valid else None,
        )
