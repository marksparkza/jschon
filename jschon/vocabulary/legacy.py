from jschon.exceptions import JSONSchemaError
from jschon.json import JSON
from jschon.jsonschema import JSONSchema, Result
from jschon.vocabulary import ArrayOfSubschemas, Keyword, Subschema

__all__ = [
    'RecursiveRefKeyword_2019_09',
    'RecursiveAnchorKeyword_2019_09',
    'ItemsKeyword_2019_09',
    'AdditionalItemsKeyword_2019_09',
    'UnevaluatedItemsKeyword_2019_09',
]


class RecursiveRefKeyword_2019_09(Keyword):
    key = "$recursiveRef"

    def __init__(self, parentschema: JSONSchema, value: str):
        super().__init__(parentschema, value)
        if value != '#':
            raise JSONSchemaError(f'"$recursiveRef" may only take the value "#"')

        self.refschema = None

    def resolve(self) -> None:
        if (base_uri := self.parentschema.base_uri) is not None:
            self.refschema = self.parentschema.catalog.get_schema(
                base_uri, metaschema_uri=self.parentschema.metaschema_uri, cacheid=self.parentschema.cacheid
            )
        else:
            raise JSONSchemaError(f'No base URI against which to resolve "$recursiveRef"')

    def evaluate(self, instance: JSON, result: Result) -> None:
        refschema = self.refschema
        if (recursive_anchor := refschema.get("$recursiveAnchor")) and \
                recursive_anchor.data is True:

            target = result
            while target is not None:
                if (base_anchor := target.schema.get("$recursiveAnchor")) and \
                        base_anchor.data is True:
                    refschema = target.schema

                target = target.parent

        refschema.evaluate(instance, result)
        result.refschema(refschema)


class RecursiveAnchorKeyword_2019_09(Keyword):
    key = "$recursiveAnchor"
    static = True


class ItemsKeyword_2019_09(Keyword, Subschema, ArrayOfSubschemas):
    key = "items"
    instance_types = "array",

    def evaluate(self, instance: JSON, result: Result) -> None:
        if len(instance) == 0:
            return

        elif isinstance(self.json.data, bool):
            self.json.evaluate(instance, result)

        elif isinstance(self.json, JSONSchema):
            for index, item in enumerate(instance):
                self.json.evaluate(item, result)

            if result.passed:
                result.annotate(True)

        elif self.json.type == "array":
            annotation = None
            error = []
            for index, item in enumerate(instance[:len(self.json)]):
                annotation = index
                with result(item, str(index)) as subresult:
                    if not self.json[index].evaluate(item, subresult).passed:
                        error += [index]

            if error:
                result.fail(error)
            else:
                result.annotate(annotation)


class AdditionalItemsKeyword_2019_09(Keyword, Subschema):
    key = "additionalItems"
    instance_types = "array",
    depends_on = "items",

    def evaluate(self, instance: JSON, result: Result) -> None:
        if (items := result.sibling(instance, "items")) and type(items.annotation) is int:
            annotation = None
            error = []
            for index, item in enumerate(instance[(start := items.annotation + 1):], start):
                if self.json.evaluate(item, result).passed:
                    annotation = True
                else:
                    error += [index]
                    # reset to passed for the next iteration
                    result.pass_()

            if error:
                result.fail(error)
            else:
                result.annotate(annotation)

        else:
            result.discard()


class UnevaluatedItemsKeyword_2019_09(Keyword, Subschema):
    key = "unevaluatedItems"
    instance_types = "array",
    depends_on = "items", "additionalItems", "if", "then", "else", "allOf", "anyOf", "oneOf", "not",

    def evaluate(self, instance: JSON, result: Result) -> None:
        last_evaluated_item = -1
        for items_annotation in result.parent.collect_annotations(instance, "items"):
            if items_annotation is True:
                result.discard()
                return
            if type(items_annotation) is int and items_annotation > last_evaluated_item:
                last_evaluated_item = items_annotation

        for additional_items_annotation in result.parent.collect_annotations(instance, "additionalItems"):
            if additional_items_annotation is True:
                result.discard()
                return

        for unevaluated_items_annotation in result.parent.collect_annotations(instance, "unevaluatedItems"):
            if unevaluated_items_annotation is True:
                result.discard()
                return

        annotation = None
        error = []
        for index, item in enumerate(instance[(start := last_evaluated_item + 1):], start):
            if self.json.evaluate(item, result).passed:
                annotation = True
            else:
                error += [index]
                # reset to passed for the next iteration
                result.pass_()

        if error:
            result.fail(error)
        else:
            result.annotate(annotation)
