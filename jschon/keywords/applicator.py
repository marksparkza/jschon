import typing as _t

from jschon.json import JSONArray, JSONObject
from jschon.pointer import Pointer
from jschon.schema import Schema, Keyword, KeywordResult
from jschon.types import SchemaCompatible

__all__ = [
    'ItemsKeyword',
    'AdditionalItemsKeyword',
    'UnevaluatedItemsKeyword',
    'ContainsKeyword',
    'PropertiesKeyword',
]


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
            annotation=None,
            error=None,
            subresults=[],
        )
        if len(instance) > 0:
            if self.value is False:
                result.valid = False

            elif self.subschema is not None:
                for item in instance:
                    result.subresults += [subresult := self.subschema.evaluate(item)]
                    if not subresult.valid:
                        result.valid = False
                result.annotation = True

            elif self.subschemas is not None:
                for index, item in enumerate(instance):
                    if index < len(self.subschemas):
                        result.subresults += [subresult := self.subschemas[index].evaluate(item)]
                        if not subresult.valid:
                            result.valid = False
                        result.annotation = index

        if not result.valid:
            result.error = "One or more array elements is invalid"

        return result


class AdditionalItemsKeyword(Keyword):
    __keyword__ = "additionalItems"
    __schema__ = {"$recursiveRef": "#"}
    __types__ = JSONArray


class UnevaluatedItemsKeyword(Keyword):
    __keyword__ = "unevaluatedItems"
    __schema__ = {"$recursiveRef": "#"}
    __types__ = JSONArray


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
            annotation=None,
            error=None,
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
            error=None,
            subresults=[],
        )
        for name, item in instance.items():
            if name in self.subschemas:
                result.subresults += [subresult := self.subschemas[name].evaluate(item)]
                if not subresult.valid:
                    result.valid = False
                result.annotation += [name]

        if not result.valid:
            result.error = "One or more object properties is invalid"

        return result
