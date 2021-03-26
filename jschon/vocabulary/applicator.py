import re
from typing import Any, Union, Mapping

from jschon.json import JSON, AnyJSONCompatible
from jschon.jsonschema import Keyword, Scope, JSONSchema, Applicator, ArrayApplicator, PropertyApplicator

__all__ = [
    'AllOfKeyword',
    'AnyOfKeyword',
    'OneOfKeyword',
    'NotKeyword',
    'IfKeyword',
    'ThenKeyword',
    'ElseKeyword',
    'DependentSchemasKeyword',
    'PrefixItemsKeyword',
    'ItemsKeyword',
    'LegacyItemsKeyword',
    'LegacyAdditionalItemsKeyword',
    'UnevaluatedItemsKeyword',
    'ContainsKeyword',
    'PropertiesKeyword',
    'PatternPropertiesKeyword',
    'AdditionalPropertiesKeyword',
    'UnevaluatedPropertiesKeyword',
    'PropertyNamesKeyword',
]


class AllOfKeyword(Keyword, ArrayApplicator):

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        err_indices = []
        for index, subschema in enumerate(self.json):
            with scope(str(index)) as subscope:
                subschema.evaluate(instance, subscope)
                if not subscope.valid:
                    err_indices += [index]

        if err_indices:
            scope.fail(instance, f'The instance is invalid against subschemas {err_indices}')


class AnyOfKeyword(Keyword, ArrayApplicator):

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        valid = False
        for index, subschema in enumerate(self.json):
            with scope(str(index)) as subscope:
                subschema.evaluate(instance, subscope)
                if subscope.valid:
                    valid = True

        if not valid:
            scope.fail(instance, f'The instance must be valid against at least one subschema')


class OneOfKeyword(Keyword, ArrayApplicator):

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        valid_indices = []
        err_indices = []
        for index, subschema in enumerate(self.json):
            with scope(str(index)) as subscope:
                subschema.evaluate(instance, subscope)
                if subscope.valid:
                    valid_indices += [index]
                else:
                    err_indices += [index]

        if len(valid_indices) != 1:
            scope.fail(instance, 'The instance must be valid against exactly one subschema; '
                                 f'it is valid against {valid_indices} and invalid against {err_indices}')


class NotKeyword(Keyword, Applicator):

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        self.json.evaluate(instance, scope)

        if scope.valid:
            scope.fail(instance, 'The instance must not be valid against the subschema')
        else:
            scope.errors.clear()


class IfKeyword(Keyword, Applicator):

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        self.json.evaluate(instance, scope)
        scope.noassert()


class ThenKeyword(Keyword, Applicator):

    def __init__(
            self,
            parentschema: JSONSchema,
            key: str,
            value: Union[bool, Mapping[str, AnyJSONCompatible]],
            *args: Any,
            **kwargs: Any,
    ):
        super().__init__(parentschema, key, value, *args, **kwargs)
        self.keymap.setdefault("if", "if")

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        if (if_ := scope.sibling(self.keymap["if"])) and if_.valid:
            self.json.evaluate(instance, scope)
        else:
            scope.discard()


class ElseKeyword(Keyword, Applicator):

    def __init__(
            self,
            parentschema: JSONSchema,
            key: str,
            value: Union[bool, Mapping[str, AnyJSONCompatible]],
            *args: Any,
            **kwargs: Any,
    ):
        super().__init__(parentschema, key, value, *args, **kwargs)
        self.keymap.setdefault("if", "if")

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        if (if_ := scope.sibling(self.keymap["if"])) and not if_.valid:
            self.json.evaluate(instance, scope)
        else:
            scope.discard()


class DependentSchemasKeyword(Keyword, PropertyApplicator):

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        annotation = []
        err_names = []
        for name, subschema in self.json.items():
            if name in instance:
                with scope(name) as subscope:
                    subschema.evaluate(instance, subscope)
                    if subscope.valid:
                        annotation += [name]
                    else:
                        err_names += [name]

        if err_names:
            scope.fail(instance, f'Properties {err_names} are invalid against '
                                 f'the corresponding "{self.key}" subschemas')
        else:
            scope.annotate(instance, self.key, annotation)


class PrefixItemsKeyword(Keyword, ArrayApplicator):

    def evaluate(self, instance: JSON, scope: Scope) -> None:
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
        elif eval_index is not None:
            if eval_index == len(instance) - 1:
                eval_index = True
            scope.annotate(instance, self.key, eval_index)


class ItemsKeyword(Keyword, Applicator):

    def __init__(
            self,
            parentschema: JSONSchema,
            key: str,
            value: Union[bool, Mapping[str, AnyJSONCompatible]],
            *args: Any,
            **kwargs: Any,
    ):
        super().__init__(parentschema, key, value, *args, **kwargs)
        self.keymap.setdefault("prefixItems", "prefixItems")

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        if (prefix_items := scope.sibling(self.keymap["prefixItems"])) and \
                (prefix_items_annotation := prefix_items.annotations.get(self.keymap["prefixItems"])):
            if prefix_items_annotation.value is True:
                return
            else:
                start_index = prefix_items_annotation.value + 1
        else:
            start_index = 0

        annotation = None
        for index, item in enumerate(instance[start_index:]):
            annotation = True
            self.json.evaluate(item, scope)

        if annotation is True and scope.valid:
            scope.annotate(instance, self.key, annotation)


class LegacyItemsKeyword(Keyword, Applicator, ArrayApplicator):

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        if len(instance) == 0:
            return

        elif isinstance(self.json.value, bool):
            self.json.evaluate(instance, scope)

        elif isinstance(self.json, JSONSchema):
            for index, item in enumerate(instance):
                self.json.evaluate(item, scope)

            if scope.valid:
                scope.annotate(instance, self.key, True)

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
                scope.annotate(instance, self.key, eval_index)


class LegacyAdditionalItemsKeyword(Keyword, Applicator):

    def __init__(
            self,
            parentschema: JSONSchema,
            key: str,
            value: Union[bool, Mapping[str, AnyJSONCompatible]],
            *args: Any,
            **kwargs: Any,
    ):
        super().__init__(parentschema, key, value, *args, **kwargs)
        self.keymap.setdefault("items", "items")

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        if (items := scope.sibling(self.keymap["items"])) and \
                (items_annotation := items.annotations.get(self.keymap["items"])) and \
                type(items_annotation.value) is int:
            annotation = None
            for index, item in enumerate(instance[items_annotation.value + 1:]):
                annotation = True
                self.json.evaluate(item, scope)

            if scope.valid:
                scope.annotate(instance, self.key, annotation)
        else:
            scope.discard()


class UnevaluatedItemsKeyword(Keyword, Applicator):

    def __init__(
            self,
            parentschema: JSONSchema,
            key: str,
            value: Union[bool, Mapping[str, AnyJSONCompatible]],
            *args: Any,
            **kwargs: Any,
    ):
        super().__init__(parentschema, key, value, *args, **kwargs)
        self.keymap.setdefault("items", "items")
        self.keymap.setdefault("additionalItems", "additionalItems")
        self.keymap.setdefault("unevaluatedItems", "unevaluatedItems")

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        last_evaluated_item = -1
        for items_annotation in scope.parent.collect_annotations(instance, self.keymap["items"]):
            if items_annotation.value is True:
                scope.discard()
                return
            if type(items_annotation.value) is int and items_annotation.value > last_evaluated_item:
                last_evaluated_item = items_annotation.value

        for additional_items_annotation in scope.parent.collect_annotations(instance, self.keymap["additionalItems"]):
            if additional_items_annotation.value is True:
                scope.discard()
                return

        for unevaluated_items_annotation in scope.parent.collect_annotations(instance, self.keymap["unevaluatedItems"]):
            if unevaluated_items_annotation.value is True:
                scope.discard()
                return

        annotation = None
        for index, item in enumerate(instance[last_evaluated_item + 1:]):
            annotation = True
            self.json.evaluate(item, scope)

        if scope.valid:
            scope.annotate(instance, self.key, annotation)


class ContainsKeyword(Keyword, Applicator):

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        annotation = 0
        for index, item in enumerate(instance):
            if self.json.evaluate(item, scope).valid:
                annotation += 1
            else:
                scope.errors.clear()

        if annotation > 0:
            scope.annotate(instance, self.key, annotation)
        else:
            scope.fail(instance, 'The array does not contain an element that is valid '
                                 f'against the "{self.key}" subschema')


class PropertiesKeyword(Keyword, PropertyApplicator):

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        annotation = []
        err_names = []
        for name, item in instance.items():
            if name in self.json:
                with scope(name) as subscope:
                    self.json[name].evaluate(item, subscope)
                    if subscope.valid:
                        annotation += [name]
                    else:
                        err_names += [name]

        if err_names:
            scope.fail(instance, f"Properties {err_names} are invalid")
        else:
            scope.annotate(instance, self.key, annotation)


class PatternPropertiesKeyword(Keyword, PropertyApplicator):

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        matched_names = set()
        err_names = []
        for name, item in instance.items():
            for regex, subschema in self.json.items():
                if re.search(regex, name) is not None:
                    with scope(regex) as subscope:
                        subschema.evaluate(item, subscope)
                        if subscope.valid:
                            matched_names |= {name}
                        else:
                            err_names += [name]

        if err_names:
            scope.fail(instance, f"Properties {err_names} are invalid")
        else:
            scope.annotate(instance, self.key, list(matched_names))


class AdditionalPropertiesKeyword(Keyword, Applicator):

    def __init__(
            self,
            parentschema: JSONSchema,
            key: str,
            value: Union[bool, Mapping[str, AnyJSONCompatible]],
            *args: Any,
            **kwargs: Any,
    ):
        super().__init__(parentschema, key, value, *args, **kwargs)
        self.keymap.setdefault("properties", "properties")
        self.keymap.setdefault("patternProperties", "patternProperties")

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        evaluated_names = set()
        if (properties := scope.sibling(self.keymap["properties"])) and \
                (properties_annotation := properties.annotations.get(self.keymap["properties"])):
            evaluated_names |= set(properties_annotation.value)

        if (pattern_properties := scope.sibling(self.keymap["patternProperties"])) and \
                (pattern_properties_annotation := pattern_properties.annotations.get(self.keymap["patternProperties"])):
            evaluated_names |= set(pattern_properties_annotation.value)

        annotation = []
        for name, item in instance.items():
            if name not in evaluated_names:
                if self.json.evaluate(item, scope).valid:
                    annotation += [name]

        if scope.valid:
            scope.annotate(instance, self.key, annotation)


class UnevaluatedPropertiesKeyword(Keyword, Applicator):

    def __init__(
            self,
            parentschema: JSONSchema,
            key: str,
            value: Union[bool, Mapping[str, AnyJSONCompatible]],
            *args: Any,
            **kwargs: Any,
    ):
        super().__init__(parentschema, key, value, *args, **kwargs)
        self.keymap.setdefault("properties", "properties")
        self.keymap.setdefault("patternProperties", "patternProperties")
        self.keymap.setdefault("additionalProperties", "additionalProperties")
        self.keymap.setdefault("unevaluatedProperties", "unevaluatedProperties")

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        evaluated_names = set()
        for properties_annotation in scope.parent.collect_annotations(instance, self.keymap["properties"]):
            evaluated_names |= set(properties_annotation.value)
        for pattern_properties_annotation in scope.parent.collect_annotations(instance, self.keymap["patternProperties"]):
            evaluated_names |= set(pattern_properties_annotation.value)
        for additional_properties_annotation in scope.parent.collect_annotations(instance, self.keymap["additionalProperties"]):
            evaluated_names |= set(additional_properties_annotation.value)
        for unevaluated_properties_annotation in scope.parent.collect_annotations(instance, self.keymap["unevaluatedProperties"]):
            evaluated_names |= set(unevaluated_properties_annotation.value)

        annotation = []
        for name, item in instance.items():
            if name not in evaluated_names:
                if self.json.evaluate(item, scope).valid:
                    annotation += [name]

        if scope.valid:
            scope.annotate(instance, self.key, annotation)


class PropertyNamesKeyword(Keyword, Applicator):

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        err_names = []
        for name in instance:
            if not self.json.evaluate(JSON(name), scope).valid:
                err_names += [name]

        if err_names:
            scope.errors.clear()
            scope.fail(instance, f"Property names {err_names} are invalid")
