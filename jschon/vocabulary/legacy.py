from jschon.catalogue import Catalogue
from jschon.exceptions import JSONSchemaError
from jschon.json import JSON
from jschon.jsonschema import Keyword, JSONSchema, Scope, Applicator, ArrayApplicator

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
            self.refschema = Catalogue.get_schema(base_uri, metaschema_uri=self.parentschema.metaschema_uri)
        else:
            raise JSONSchemaError(f'No base URI against which to resolve "$recursiveRef"')

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        refschema = self.refschema
        if (recursive_anchor := refschema.get("$recursiveAnchor")) and \
                recursive_anchor.value is True:
            base_scope = scope.root
            for key in scope.path:
                if (base_schema := base_scope.schema) is refschema:
                    break
                if (base_anchor := base_schema.get("$recursiveAnchor")) and \
                        base_anchor.value is True:
                    refschema = base_schema
                    break
                base_scope = base_scope.children[key]

        refschema.evaluate(instance, scope)


class RecursiveAnchorKeyword_2019_09(Keyword):
    key = "$recursiveAnchor"

    def can_evaluate(self, instance: JSON) -> bool:
        return False


class ItemsKeyword_2019_09(Keyword, Applicator, ArrayApplicator):
    key = "items"
    types = "array"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        if len(instance) == 0:
            return

        elif isinstance(self.json.value, bool):
            self.json.evaluate(instance, scope)

        elif isinstance(self.json, JSONSchema):
            for index, item in enumerate(instance):
                self.json.evaluate(item, scope)

            if scope.valid:
                scope.annotate(instance, "items", True)

        elif self.json.type == "array":
            eval_index = None
            err_indices = []
            for index, item in enumerate(instance[:len(self.json)]):
                eval_index = index
                with scope(str(index)) as subscope:
                    self.json[index].evaluate(item, subscope)
                    if not subscope.valid:
                        err_indices += [index]

            if err_indices:
                scope.fail(instance, f"Array elements {err_indices} are invalid")
            else:
                scope.annotate(instance, "items", eval_index)


class AdditionalItemsKeyword_2019_09(Keyword, Applicator):
    key = "additionalItems"
    types = "array"
    depends = "items"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        if (items := scope.sibling("items")) and \
                (items_annotation := items.annotations.get("items")) and \
                type(items_annotation.value) is int:
            annotation = None
            for index, item in enumerate(instance[items_annotation.value + 1:]):
                annotation = True
                self.json.evaluate(item, scope)

            if scope.valid:
                scope.annotate(instance, "additionalItems", annotation)
        else:
            scope.discard()


class UnevaluatedItemsKeyword_2019_09(Keyword, Applicator):
    key = "unevaluatedItems"
    types = "array"
    depends = "items", "additionalItems", "if", "then", "else", "allOf", "anyOf", "oneOf", "not"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        last_evaluated_item = -1
        for items_annotation in scope.parent.collect_annotations(instance, "items"):
            if items_annotation.value is True:
                scope.discard()
                return
            if type(items_annotation.value) is int and items_annotation.value > last_evaluated_item:
                last_evaluated_item = items_annotation.value

        for additional_items_annotation in scope.parent.collect_annotations(instance, "additionalItems"):
            if additional_items_annotation.value is True:
                scope.discard()
                return

        for unevaluated_items_annotation in scope.parent.collect_annotations(instance, "unevaluatedItems"):
            if unevaluated_items_annotation.value is True:
                scope.discard()
                return

        annotation = None
        for index, item in enumerate(instance[last_evaluated_item + 1:]):
            annotation = True
            self.json.evaluate(item, scope)

        if scope.valid:
            scope.annotate(instance, self.key, annotation)
