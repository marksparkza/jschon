import re

from jschon.json import JSON
from jschon.jsonschema import Result
from jschon.vocabulary import ArrayOfSubschemas, Keyword, ObjectOfSubschemas, Subschema

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
    'ContainsKeyword_2019_09',
    'ContainsKeyword_Next',
    'MinContainsKeyword_Next',
    'MaxContainsKeyword_Next',
    'PropertiesKeyword',
    'PatternPropertiesKeyword',
    'AdditionalPropertiesKeyword',
    'UnevaluatedPropertiesKeyword_2019_09',
    'UnevaluatedPropertiesKeyword_Next',
    'PropertyNamesKeyword',
]


class _ApplicatorAnnotationKeyword(Keyword):

    def evaluate(self, instance: JSON, result: Result) -> None:
        result.annotate(self.json.data)
        result.noassert()


class AllOfKeyword(Keyword, ArrayOfSubschemas):
    key = "allOf"

    def evaluate(self, instance: JSON, result: Result) -> None:
        err_indices = []
        for index, subschema in enumerate(self.json):
            with result(instance, str(index)) as subresult:
                subschema.evaluate(instance, subresult)
                if not subresult.passed:
                    err_indices += [index]

        if err_indices:
            result.fail(f'The instance is invalid against subschemas {err_indices}')


class AnyOfKeyword(Keyword, ArrayOfSubschemas):
    key = "anyOf"

    def evaluate(self, instance: JSON, result: Result) -> None:
        valid = False
        for index, subschema in enumerate(self.json):
            with result(instance, str(index)) as subresult:
                subschema.evaluate(instance, subresult)
                if subresult.passed:
                    valid = True

        if not valid:
            result.fail(f'The instance must be valid against at least one subschema')


class OneOfKeyword(Keyword, ArrayOfSubschemas):
    key = "oneOf"

    def evaluate(self, instance: JSON, result: Result) -> None:
        valid_indices = []
        err_indices = []
        for index, subschema in enumerate(self.json):
            with result(instance, str(index)) as subresult:
                subschema.evaluate(instance, subresult)
                if subresult.passed:
                    valid_indices += [index]
                else:
                    err_indices += [index]

        if len(valid_indices) != 1:
            result.fail('The instance must be valid against exactly one subschema; '
                        f'it is valid against {valid_indices} and invalid against {err_indices}')


class NotKeyword(Keyword, Subschema):
    key = "not"

    def evaluate(self, instance: JSON, result: Result) -> None:
        self.json.evaluate(instance, result)

        if result.passed:
            result.fail('The instance must not be valid against the subschema')
        else:
            result.pass_()


class IfKeyword(Keyword, Subschema):
    key = "if"

    def evaluate(self, instance: JSON, result: Result) -> None:
        self.json.evaluate(instance, result)
        result.noassert()


class ThenKeyword(Keyword, Subschema):
    key = "then"
    depends_on = "if",

    def evaluate(self, instance: JSON, result: Result) -> None:
        if (if_ := result.sibling(instance, "if")) and if_.valid:
            self.json.evaluate(instance, result)
        else:
            result.discard()


class ElseKeyword(Keyword, Subschema):
    key = "else"
    depends_on = "if",

    def evaluate(self, instance: JSON, result: Result) -> None:
        if (if_ := result.sibling(instance, "if")) and not if_.valid:
            self.json.evaluate(instance, result)
        else:
            result.discard()


class DependentSchemasKeyword(Keyword, ObjectOfSubschemas):
    key = "dependentSchemas"
    instance_types = "object",

    def evaluate(self, instance: JSON, result: Result) -> None:
        annotation = []
        err_names = []
        for name, subschema in self.json.items():
            if name in instance:
                with result(instance, name) as subresult:
                    subschema.evaluate(instance, subresult)
                    if subresult.passed:
                        annotation += [name]
                    else:
                        err_names += [name]

        if err_names:
            result.fail(f'Properties {err_names} are invalid against '
                        f'the corresponding "dependentSchemas" subschemas')
        else:
            result.annotate(annotation)


class PrefixItemsKeyword(Keyword, ArrayOfSubschemas):
    key = "prefixItems"
    instance_types = "array",

    def evaluate(self, instance: JSON, result: Result) -> None:
        annotation = None
        error = []
        for index, item in enumerate(instance[:len(self.json)]):
            annotation = index
            with result(item, str(index)) as subresult:
                if not self.json[index].evaluate(item, subresult).passed:
                    error += [index]

        if error:
            result.fail(error)
        elif annotation is not None:
            if annotation == len(instance) - 1:
                annotation = True
            result.annotate(annotation)


class ItemsKeyword(Keyword, Subschema):
    key = "items"
    instance_types = "array",
    depends_on = "prefixItems",

    def evaluate(self, instance: JSON, result: Result) -> None:
        if prefix_items := result.sibling(instance, "prefixItems"):
            start_index = len(prefix_items.schema_node)
        else:
            start_index = 0

        annotation = None
        error = []
        for index, item in enumerate(instance[start_index:], start_index):
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


class UnevaluatedItemsKeyword(Keyword, Subschema):
    key = "unevaluatedItems"
    instance_types = "array",
    depends_on = "prefixItems", "items", "contains", "if", "then", "else", "allOf", "anyOf", "oneOf", "not",

    def evaluate(self, instance: JSON, result: Result) -> None:
        last_evaluated_item = -1
        for prefix_items_annotation in result.parent.collect_annotations(instance, "prefixItems"):
            if prefix_items_annotation is True:
                result.discard()
                return
            if prefix_items_annotation > last_evaluated_item:
                last_evaluated_item = prefix_items_annotation

        for items_annotation in result.parent.collect_annotations(instance, "items"):
            if items_annotation is True:
                result.discard()
                return

        for unevaluated_items_annotation in result.parent.collect_annotations(instance, "unevaluatedItems"):
            if unevaluated_items_annotation is True:
                result.discard()
                return

        contains_indices = set()
        for contains_annotation in result.parent.collect_annotations(instance, "contains"):
            contains_indices |= set(contains_annotation)

        annotation = None
        error = []
        for index, item in enumerate(instance[(start := last_evaluated_item + 1):], start):
            if index not in contains_indices:
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


class ContainsKeyword_2019_09(Keyword, Subschema):
    key = "contains"
    instance_types = "array",

    def evaluate(self, instance: JSON, result: Result) -> None:
        annotation = []

        for index, item in enumerate(instance):
            if self.json.evaluate(item, result).passed:
                annotation += [index]
            else:
                result.pass_()

        result.annotate(annotation)
        if not annotation:
            result.fail('The array does not contain any element that is valid '
                        f'against the "{self.key}" subschema')


class ContainsKeyword_Next(Keyword, Subschema):
    key = "contains"
    instance_types = "array", "object",
    depends_on = "minContains", "maxContains",

    # def _evaluate_array(self, instance: JSON, result: Result) -> [Integer]:
    def evaluate(self, instance: JSON, result: Result) -> None:
        annotation = []

        for identifier, item in (
            enumerate(instance) if instance.type == 'array' else instance.items()
        ):
            if self.json.evaluate(item, result).passed:
                annotation += [identifier]
            else:
                result.pass_()
        result.annotate(annotation)

        # TODO: What should happen if both minContains and
        #       maxContains are violated, which can only
        #       happen if they are in the wrong relationship
        #       to each other?  Is that a failure or
        #       a runtime error of some sort?
        minimum = 1
        maximum = None
        if minContains := result.sibling(instance, "minContains"):
            minimum = minContains.annotation
        if maxContains := result.sibling(instance, "maxContains"):
            maximum = maxContains.annotation

        if len(annotation) < minimum:
            result.fail(
                f'The array contains too few elements ({len(annotation)}) that '
                f'are valid against the "{self.key}" subschema; '
                f'at least {minimum} are required.'
            )
        if maximum is not None and len(annotation) > maximum:
            result.fail(
                f'The array contains too many elements ({len(annotation)}) that '
                f'are valid against the "{self.key}" subschema; '
                f'at most {maximum} are allowed.'
            )

        if minContains is None and maxContains is None and not annotation:
            result.fail('The array does not contain any element that is valid '
                        f'against the "{self.key}" subschema')


class MaxContainsKeyword_Next(_ApplicatorAnnotationKeyword):
    key = "maxContains"
    instance_types = "array", "object",


class MinContainsKeyword_Next(_ApplicatorAnnotationKeyword):
    key = "minContains"
    instance_types = "array", "object",


class PropertiesKeyword(Keyword, ObjectOfSubschemas):
    key = "properties"
    instance_types = "object",

    def evaluate(self, instance: JSON, result: Result) -> None:
        annotation = []
        err_names = []
        for name, item in instance.items():
            if name in self.json:
                with result(item, name) as subresult:
                    self.json[name].evaluate(item, subresult)
                    if subresult.passed:
                        annotation += [name]
                    else:
                        err_names += [name]

        if err_names:
            result.fail(f"Properties {err_names} are invalid")
        else:
            result.annotate(annotation)


class PatternPropertiesKeyword(Keyword, ObjectOfSubschemas):
    key = "patternProperties"
    instance_types = "object",

    def evaluate(self, instance: JSON, result: Result) -> None:
        matched_names = set()
        err_names = []
        for name, item in instance.items():
            for regex, subschema in self.json.items():
                if re.search(regex, name) is not None:
                    with result(item, regex) as subresult:
                        subschema.evaluate(item, subresult)
                        if subresult.passed:
                            matched_names |= {name}
                        else:
                            err_names += [name]

        if err_names:
            result.fail(f"Properties {err_names} are invalid")
        else:
            result.annotate(list(matched_names))


class AdditionalPropertiesKeyword(Keyword, Subschema):
    key = "additionalProperties"
    instance_types = "object",
    depends_on = "properties", "patternProperties",

    def evaluate(self, instance: JSON, result: Result) -> None:
        if properties := result.sibling(instance, "properties"):
            known_property_names = properties.schema_node.keys()
        else:
            known_property_names = ()

        if pattern_properties := result.sibling(instance, "patternProperties"):
            known_property_patterns = pattern_properties.schema_node.keys()
        else:
            known_property_patterns = ()

        annotation = []
        error = []
        for name, item in instance.items():
            if name not in known_property_names and not any(
                    re.search(regex, name) for regex in known_property_patterns
            ):
                if self.json.evaluate(item, result).passed:
                    annotation += [name]
                else:
                    error += [name]
                    # reset to passed for the next iteration
                    result.pass_()

        if error:
            result.fail(error)
        else:
            result.annotate(annotation)


class UnevaluatedPropertiesKeyword_2019_09(Keyword, Subschema):
    key = "unevaluatedProperties"
    instance_types = "object",
    depends_on = "properties", "patternProperties", "additionalProperties", \
                 "if", "then", "else", "dependentSchemas", \
                 "allOf", "anyOf", "oneOf", "not",
    @classmethod
    def _annotation_sources(cls):
        return "properties", "patternProperties", \
               "additionalProperties", "unevaluatedProperties",

    def evaluate(self, instance: JSON, result: Result) -> None:
        evaluated_names = set()

        for source in self._annotation_sources():
            for evaluated in result.parent.collect_annotations(instance, source):
                evaluated_names |= set(evaluated)

        annotation = []
        error = []
        for name, item in instance.items():
            if name not in evaluated_names:
                if self.json.evaluate(item, result).passed:
                    annotation += [name]
                else:
                    error += [name]
                    # reset to passed for the next iteration
                    result.pass_()

        if error:
            result.fail(error)
        else:
            result.annotate(annotation)


class UnevaluatedPropertiesKeyword_Next(UnevaluatedPropertiesKeyword_2019_09):
    depends_on = UnevaluatedPropertiesKeyword_2019_09.depends_on + ("contains",)

    @classmethod
    def _annotation_sources(cls):
        return super()._annotation_sources() + ("contains",)


class PropertyNamesKeyword(Keyword, Subschema):
    key = "propertyNames"
    instance_types = "object",

    def evaluate(self, instance: JSON, result: Result) -> None:
        error = []
        for name in instance:
            if not self.json.evaluate(JSON(name, parent=instance, key=name), result).passed:
                error += [name]
                result.pass_()

        if error:
            result.fail(error)
