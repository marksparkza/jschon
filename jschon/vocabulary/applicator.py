import re

from jschon.json import JSON
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


class AllOfKeyword(Keyword, ArrayApplicator):
    __keyword__ = "allOf"
    __schema__ = {
        "type": "array",
        "minItems": 1,
        "items": {"$recursiveRef": "#"}
    }

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        err_indices = []
        for index, subschema in enumerate(self.json):
            with scope(self.parentschema, str(index)) as subscope:
                subschema.evaluate(instance, subscope)
                if not subscope.valid:
                    err_indices += [index]

        if err_indices:
            scope.fail(instance, f'The instance is invalid against "allOf" subschemas {err_indices}')


class AnyOfKeyword(Keyword, ArrayApplicator):
    __keyword__ = "anyOf"
    __schema__ = {
        "type": "array",
        "minItems": 1,
        "items": {"$recursiveRef": "#"}
    }

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        valid = False
        for index, subschema in enumerate(self.json):
            with scope(self.parentschema, str(index)) as subscope:
                subschema.evaluate(instance, subscope)
                if subscope.valid:
                    valid = True

        if not valid:
            scope.fail(instance, f'The instance must be valid against at least one "anyOf" subschema')


class OneOfKeyword(Keyword, ArrayApplicator):
    __keyword__ = "oneOf"
    __schema__ = {
        "type": "array",
        "minItems": 1,
        "items": {"$recursiveRef": "#"}
    }

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        valid_indices = []
        err_indices = []
        for index, subschema in enumerate(self.json):
            with scope(self.parentschema, str(index)) as subscope:
                subschema.evaluate(instance, subscope)
                if subscope.valid:
                    valid_indices += [index]
                else:
                    err_indices += [index]

        if len(valid_indices) != 1:
            scope.fail(instance, 'The instance must be valid against exactly one "oneOf" subschema;'
                                 f'it is valid against {valid_indices} and invalid against {err_indices}')


class NotKeyword(Keyword, Applicator):
    __keyword__ = "not"
    __schema__ = {"$recursiveRef": "#"}

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        self.json.evaluate(instance, scope)

        if scope.valid:
            scope.fail(instance, 'The instance must not be valid against the "not" subschema')
        else:
            scope.errors.clear()


class IfKeyword(Keyword, Applicator):
    __keyword__ = "if"
    __schema__ = {"$recursiveRef": "#"}

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        self.json.evaluate(instance, scope)
        scope.assert_ = False
        scope.keep = True


class ThenKeyword(Keyword, Applicator):
    __keyword__ = "then"
    __schema__ = {"$recursiveRef": "#"}
    __depends__ = "if"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        if (if_ := scope.sibling("if")) and if_.valid:
            self.json.evaluate(instance, scope)


class ElseKeyword(Keyword, Applicator):
    __keyword__ = "else"
    __schema__ = {"$recursiveRef": "#"}
    __depends__ = "if"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        if (if_ := scope.sibling("if")) and not if_.valid:
            self.json.evaluate(instance, scope)


class DependentSchemasKeyword(Keyword, PropertyApplicator):
    __keyword__ = "dependentSchemas"
    __schema__ = {
        "type": "object",
        "additionalProperties": {"$recursiveRef": "#"}
    }
    __types__ = "object"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        annotation = []
        err_names = []
        for name, subschema in self.json.items():
            if name in instance:
                with scope(self.parentschema, name) as subscope:
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


class ItemsKeyword(Keyword, Applicator, ArrayApplicator):
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
                with scope(self.parentschema, str(index)) as subscope:
                    self.json[index].evaluate(item, subscope)
                    if not subscope.valid:
                        err_indices += [index]

            if err_indices:
                scope.fail(instance, f"Array elements {err_indices} are invalid")
            else:
                scope.annotate(instance, "items", eval_index)


class AdditionalItemsKeyword(Keyword, Applicator):
    __keyword__ = "additionalItems"
    __schema__ = {"$recursiveRef": "#"}
    __types__ = "array"
    __depends__ = "items"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        if (items := scope.sibling("items")) and (items_annotation := items.annotations.get("items")) and \
                type(items_annotation.value) is int:
            annotation = None
            for index, item in enumerate(instance[items_annotation.value + 1:]):
                annotation = True
                self.json.evaluate(item, scope)

            if scope.valid:
                scope.annotate(instance, "additionalItems", annotation)


class UnevaluatedItemsKeyword(Keyword, Applicator):
    __keyword__ = "unevaluatedItems"
    __schema__ = {"$recursiveRef": "#"}
    __types__ = "array"
    __depends__ = "items", "additionalItems", "if", "then", "else", "allOf", "anyOf", "oneOf", "not"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        last_evaluated_item = -1
        for items_annotation in scope.parent.collect_annotations(instance, "items"):
            if items_annotation.value is True:
                return
            if type(items_annotation.value) is int and items_annotation.value > last_evaluated_item:
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


class ContainsKeyword(Keyword, Applicator):
    __keyword__ = "contains"
    __schema__ = {"$recursiveRef": "#"}
    __types__ = "array"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        annotation = 0
        for index, item in enumerate(instance):
            if self.json.evaluate(item, scope).valid:
                annotation += 1
            else:
                scope.errors.clear()

        if annotation > 0:
            scope.annotate(instance, "contains", annotation)
        else:
            scope.fail(instance, 'The array does not contain an element that is valid '
                                 'against the "contains" subschema')


class PropertiesKeyword(Keyword, PropertyApplicator):
    __keyword__ = "properties"
    __schema__ = {
        "type": "object",
        "additionalProperties": {"$recursiveRef": "#"},
        "default": {}
    }
    __types__ = "object"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        annotation = []
        err_names = []
        for name, item in instance.items():
            if name in self.json:
                with scope(self.parentschema, name) as subscope:
                    self.json[name].evaluate(item, subscope)
                    if subscope.valid:
                        annotation += [name]
                    else:
                        err_names += [name]

        if err_names:
            scope.fail(instance, f"Properties {err_names} are invalid")
        else:
            scope.annotate(instance, "properties", annotation)


class PatternPropertiesKeyword(Keyword, PropertyApplicator):
    __keyword__ = "patternProperties"
    __schema__ = {
        "type": "object",
        "additionalProperties": {"$recursiveRef": "#"},
        "propertyNames": {"format": "regex"},
        "default": {}
    }
    __types__ = "object"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        matched_names = set()
        err_names = []
        for name, item in instance.items():
            for regex, subschema in self.json.items():
                if re.search(regex, name) is not None:
                    with scope(self.parentschema, regex) as subscope:
                        subschema.evaluate(item, subscope)
                        if subscope.valid:
                            matched_names |= {name}
                        else:
                            err_names += [name]

        if err_names:
            scope.fail(instance, f"Properties {err_names} are invalid")
        else:
            scope.annotate(instance, "patternProperties", list(matched_names))


class AdditionalPropertiesKeyword(Keyword, Applicator):
    __keyword__ = "additionalProperties"
    __schema__ = {"$recursiveRef": "#"}
    __types__ = "object"
    __depends__ = "properties", "patternProperties"

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
            scope.annotate(instance, "additionalProperties", annotation)


class UnevaluatedPropertiesKeyword(Keyword, Applicator):
    __keyword__ = "unevaluatedProperties"
    __schema__ = {"$recursiveRef": "#"}
    __types__ = "object"
    __depends__ = "properties", "patternProperties", "additionalProperties", \
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
            scope.annotate(instance, "unevaluatedProperties", annotation)


class PropertyNamesKeyword(Keyword, Applicator):
    __keyword__ = "propertyNames"
    __schema__ = {"$recursiveRef": "#"}
    __types__ = "object"

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        err_names = []
        for name in instance:
            if not self.json.evaluate(JSON(name), scope).valid:
                err_names += [name]

        if err_names:
            scope.errors.clear()
            scope.fail(instance, f"Property names {err_names} are invalid")
