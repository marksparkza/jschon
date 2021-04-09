import re

from jschon.json import JSON
from jschon.jsonschema import Keyword, Scope, Applicator, ArrayApplicator, PropertyApplicator

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
    'UnevaluatedItemsKeyword',
    'ContainsKeyword',
    'PropertiesKeyword',
    'PatternPropertiesKeyword',
    'AdditionalPropertiesKeyword',
    'UnevaluatedPropertiesKeyword',
    'PropertyNamesKeyword',
]


class AllOfKeyword(Keyword, ArrayApplicator):
    key = "allOf"

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
    key = "anyOf"

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
    key = "oneOf"

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
    key = "not"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        self.json.evaluate(instance, scope)

        if scope.valid:
            scope.fail(instance, 'The instance must not be valid against the subschema')
        else:
            scope.errors.clear()


class IfKeyword(Keyword, Applicator):
    key = "if"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        self.json.evaluate(instance, scope)
        scope.noassert()


class ThenKeyword(Keyword, Applicator):
    key = "then"
    depends = "if"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        if (if_ := scope.sibling("if")) and if_.valid:
            self.json.evaluate(instance, scope)
        else:
            scope.discard()


class ElseKeyword(Keyword, Applicator):
    key = "else"
    depends = "if"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        if (if_ := scope.sibling("if")) and not if_.valid:
            self.json.evaluate(instance, scope)
        else:
            scope.discard()


class DependentSchemasKeyword(Keyword, PropertyApplicator):
    key = "dependentSchemas"
    types = "object"

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
                                 f'the corresponding "dependentSchemas" subschemas')
        else:
            scope.annotate(instance, self.key, annotation)


class PrefixItemsKeyword(Keyword, ArrayApplicator):
    key = "prefixItems"
    types = "array"

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
    key = "items"
    types = "array"
    depends = "prefixItems"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        if (prefix_items := scope.sibling("prefixItems")) and \
                (prefix_items_annotation := prefix_items.annotations.get("prefixItems")):
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


class UnevaluatedItemsKeyword(Keyword, Applicator):
    key = "unevaluatedItems"
    types = "array"
    depends = "prefixItems", "items", "contains", "if", "then", "else", "allOf", "anyOf", "oneOf", "not"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        last_evaluated_item = -1
        for prefix_items_annotation in scope.parent.collect_annotations(instance, "prefixItems"):
            if prefix_items_annotation.value is True:
                scope.discard()
                return
            if prefix_items_annotation.value > last_evaluated_item:
                last_evaluated_item = prefix_items_annotation.value

        for items_annotation in scope.parent.collect_annotations(instance, "items"):
            if items_annotation.value is True:
                scope.discard()
                return

        for unevaluated_items_annotation in scope.parent.collect_annotations(instance, "unevaluatedItems"):
            if unevaluated_items_annotation.value is True:
                scope.discard()
                return

        contains_indices = set()
        for contains_annotation in scope.parent.collect_annotations(instance, "contains"):
            contains_indices |= set(contains_annotation.value)

        annotation = None
        for index, item in enumerate(instance[(start := last_evaluated_item + 1):], start):
            if index not in contains_indices:
                annotation = True
                self.json.evaluate(item, scope)

        if scope.valid:
            scope.annotate(instance, self.key, annotation)


class ContainsKeyword(Keyword, Applicator):
    key = "contains"
    types = "array"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        annotation = []
        for index, item in enumerate(instance):
            if self.json.evaluate(item, scope).valid:
                annotation += [index]
            else:
                scope.errors.clear()

        scope.annotate(instance, self.key, annotation)
        if not annotation:
            scope.fail(instance, 'The array does not contain any element that is valid '
                                 f'against the "{self.key}" subschema')


class PropertiesKeyword(Keyword, PropertyApplicator):
    key = "properties"
    types = "object"

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
    key = "patternProperties"
    types = "object"

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
    key = "additionalProperties"
    types = "object"
    depends = "properties", "patternProperties"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
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
                if self.json.evaluate(item, scope).valid:
                    annotation += [name]

        if scope.valid:
            scope.annotate(instance, self.key, annotation)


class UnevaluatedPropertiesKeyword(Keyword, Applicator):
    key = "unevaluatedProperties"
    types = "object"
    depends = "properties", "patternProperties", "additionalProperties", \
              "if", "then", "else", "dependentSchemas", \
              "allOf", "anyOf", "oneOf", "not"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
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
                if self.json.evaluate(item, scope).valid:
                    annotation += [name]

        if scope.valid:
            scope.annotate(instance, self.key, annotation)


class PropertyNamesKeyword(Keyword, Applicator):
    key = "propertyNames"
    types = "object"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        err_names = []
        for name in instance:
            if not self.json.evaluate(JSON(name), scope).valid:
                err_names += [name]

        if err_names:
            scope.errors.clear()
            scope.fail(instance, f"Property names {err_names} are invalid")
