import re

from jschon.json import JSON
from jschon.jsonschema import Scope
from jschon.vocabulary import Keyword, Applicator, ArrayApplicator, PropertyApplicator

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
            with scope(instance, str(index)) as subscope:
                subschema.evaluate(instance, subscope)
                if not subscope.passed:
                    err_indices += [index]

        if err_indices:
            scope.fail(f'The instance is invalid against subschemas {err_indices}')


class AnyOfKeyword(Keyword, ArrayApplicator):
    key = "anyOf"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        valid = False
        for index, subschema in enumerate(self.json):
            with scope(instance, str(index)) as subscope:
                subschema.evaluate(instance, subscope)
                if subscope.passed:
                    valid = True

        if not valid:
            scope.fail(f'The instance must be valid against at least one subschema')


class OneOfKeyword(Keyword, ArrayApplicator):
    key = "oneOf"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        valid_indices = []
        err_indices = []
        for index, subschema in enumerate(self.json):
            with scope(instance, str(index)) as subscope:
                subschema.evaluate(instance, subscope)
                if subscope.passed:
                    valid_indices += [index]
                else:
                    err_indices += [index]

        if len(valid_indices) != 1:
            scope.fail('The instance must be valid against exactly one subschema; '
                       f'it is valid against {valid_indices} and invalid against {err_indices}')


class NotKeyword(Keyword, Applicator):
    key = "not"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        self.json.evaluate(instance, scope)

        if scope.passed:
            scope.fail('The instance must not be valid against the subschema')
        else:
            scope.pass_()


class IfKeyword(Keyword, Applicator):
    key = "if"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        self.json.evaluate(instance, scope)
        scope.noassert()


class ThenKeyword(Keyword, Applicator):
    key = "then"
    depends = "if"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        if (if_ := scope.sibling(instance, "if")) and if_.valid:
            self.json.evaluate(instance, scope)
        else:
            scope.discard()


class ElseKeyword(Keyword, Applicator):
    key = "else"
    depends = "if"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        if (if_ := scope.sibling(instance, "if")) and not if_.valid:
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
                with scope(instance, name) as subscope:
                    subschema.evaluate(instance, subscope)
                    if subscope.passed:
                        annotation += [name]
                    else:
                        err_names += [name]

        if err_names:
            scope.fail(f'Properties {err_names} are invalid against '
                       f'the corresponding "dependentSchemas" subschemas')
        else:
            scope.annotate(annotation)


class PrefixItemsKeyword(Keyword, ArrayApplicator):
    key = "prefixItems"
    types = "array"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        eval_index = None
        err_indices = []
        for index, item in enumerate(instance[:len(self.json)]):
            eval_index = index
            with scope(item, str(index)) as subscope:
                self.json[index].evaluate(item, subscope)
                if not subscope.passed:
                    err_indices += [index]

        if err_indices:
            scope.fail(f"Array elements {err_indices} are invalid")
        elif eval_index is not None:
            if eval_index == len(instance) - 1:
                eval_index = True
            scope.annotate(eval_index)


class ItemsKeyword(Keyword, Applicator):
    key = "items"
    types = "array"
    depends = "prefixItems"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        if (prefix_items := scope.sibling(instance, "prefixItems")) and \
                prefix_items.annotation is not None:
            if prefix_items.annotation is True:
                return
            else:
                start_index = prefix_items.annotation + 1
        else:
            start_index = 0

        annotation = None
        for index, item in enumerate(instance[start_index:]):
            annotation = True
            self.json.evaluate(item, scope)

        if annotation is True and scope.passed:
            scope.annotate(annotation)


class UnevaluatedItemsKeyword(Keyword, Applicator):
    key = "unevaluatedItems"
    types = "array"
    depends = "prefixItems", "items", "contains", "if", "then", "else", "allOf", "anyOf", "oneOf", "not"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        last_evaluated_item = -1
        for prefix_items_annotation in scope.parent.collect_annotations(instance, "prefixItems"):
            if prefix_items_annotation is True:
                scope.discard()
                return
            if prefix_items_annotation > last_evaluated_item:
                last_evaluated_item = prefix_items_annotation

        for items_annotation in scope.parent.collect_annotations(instance, "items"):
            if items_annotation is True:
                scope.discard()
                return

        for unevaluated_items_annotation in scope.parent.collect_annotations(instance, "unevaluatedItems"):
            if unevaluated_items_annotation is True:
                scope.discard()
                return

        contains_indices = set()
        for contains_annotation in scope.parent.collect_annotations(instance, "contains"):
            contains_indices |= set(contains_annotation)

        annotation = None
        for index, item in enumerate(instance[(start := last_evaluated_item + 1):], start):
            if index not in contains_indices:
                annotation = True
                self.json.evaluate(item, scope)

        if scope.passed:
            scope.annotate(annotation)


class ContainsKeyword(Keyword, Applicator):
    key = "contains"
    types = "array"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        annotation = []
        for index, item in enumerate(instance):
            if self.json.evaluate(item, scope).passed:
                annotation += [index]
            else:
                scope.pass_()

        scope.annotate(annotation)
        if not annotation:
            scope.fail('The array does not contain any element that is valid '
                       f'against the "{self.key}" subschema')


class PropertiesKeyword(Keyword, PropertyApplicator):
    key = "properties"
    types = "object"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        annotation = []
        err_names = []
        for name, item in instance.items():
            if name in self.json:
                with scope(item, name) as subscope:
                    self.json[name].evaluate(item, subscope)
                    if subscope.passed:
                        annotation += [name]
                    else:
                        err_names += [name]

        if err_names:
            scope.fail(f"Properties {err_names} are invalid")
        else:
            scope.annotate(annotation)


class PatternPropertiesKeyword(Keyword, PropertyApplicator):
    key = "patternProperties"
    types = "object"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        matched_names = set()
        err_names = []
        for name, item in instance.items():
            for regex, subschema in self.json.items():
                if re.search(regex, name) is not None:
                    with scope(item, regex) as subscope:
                        subschema.evaluate(item, subscope)
                        if subscope.passed:
                            matched_names |= {name}
                        else:
                            err_names += [name]

        if err_names:
            scope.fail(f"Properties {err_names} are invalid")
        else:
            scope.annotate(list(matched_names))


class AdditionalPropertiesKeyword(Keyword, Applicator):
    key = "additionalProperties"
    types = "object"
    depends = "properties", "patternProperties"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        evaluated_names = set()
        if (properties := scope.sibling(instance, "properties")) and \
                properties.annotation is not None:
            evaluated_names |= set(properties.annotation)

        if (pattern_properties := scope.sibling(instance, "patternProperties")) and \
                pattern_properties.annotation is not None:
            evaluated_names |= set(pattern_properties.annotation)

        annotation = []
        for name, item in instance.items():
            if name not in evaluated_names:
                if self.json.evaluate(item, scope).passed:
                    annotation += [name]

        if scope.passed:
            scope.annotate(annotation)


class UnevaluatedPropertiesKeyword(Keyword, Applicator):
    key = "unevaluatedProperties"
    types = "object"
    depends = "properties", "patternProperties", "additionalProperties", \
              "if", "then", "else", "dependentSchemas", \
              "allOf", "anyOf", "oneOf", "not"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        evaluated_names = set()
        for properties_annotation in scope.parent.collect_annotations(instance, "properties"):
            evaluated_names |= set(properties_annotation)
        for pattern_properties_annotation in scope.parent.collect_annotations(instance, "patternProperties"):
            evaluated_names |= set(pattern_properties_annotation)
        for additional_properties_annotation in scope.parent.collect_annotations(instance, "additionalProperties"):
            evaluated_names |= set(additional_properties_annotation)
        for unevaluated_properties_annotation in scope.parent.collect_annotations(instance, "unevaluatedProperties"):
            evaluated_names |= set(unevaluated_properties_annotation)

        annotation = []
        for name, item in instance.items():
            if name not in evaluated_names:
                if self.json.evaluate(item, scope).passed:
                    annotation += [name]

        if scope.passed:
            scope.annotate(annotation)


class PropertyNamesKeyword(Keyword, Applicator):
    key = "propertyNames"
    types = "object"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        err_names = []
        for name in instance:
            if not self.json.evaluate(JSON(name, parent=instance, key=name), scope).passed:
                err_names += [name]

        if err_names:
            scope.fail(f"Property names {err_names} are invalid")
