from enum import Enum
from typing import Dict, Any

from jschon.json import JSON
from jschon.jsonschema import JSONSchema, Scope

__all__ = [
    'Evaluator',
    'OutputFormat',
]


class OutputFormat(str, Enum):
    FLAG = 'flag'
    BASIC = 'basic'
    DETAILED = 'detailed'
    VERBOSE = 'verbose'


class Evaluator:
    """The :class:`Evaluator` class provides a high-level interface to
    schema validation and instance evaluation, with output formatting."""

    def __init__(self, schema: JSONSchema):
        self.schema: JSONSchema = schema

    def validate_schema(self, output_format=OutputFormat.FLAG) -> Dict[str, Any]:
        scope = self.schema.metaschema.evaluate(JSON(self.schema.value))
        fn = eval(f'self._{output_format.value}')
        return fn(scope)

    def evaluate_instance(self, instance: JSON, output_format=OutputFormat.FLAG) -> Dict[str, Any]:
        scope = self.schema.evaluate(instance)
        fn = eval(f'self._{output_format.value}')
        return fn(scope)

    @staticmethod
    def _flag(scope: Scope) -> Dict[str, Any]:
        return {
            "valid": scope.valid
        }

    @staticmethod
    def _basic(scope: Scope) -> Dict[str, Any]:
        result = {
            "valid": scope.valid
        }
        if result["valid"]:
            result["annotations"] = []
            for annotation in scope.collect_annotations():
                result["annotations"] += [{
                    "instanceLocation": str(annotation.instance_path),
                    "keywordLocation": str(annotation.evaluation_path),
                    "absoluteKeywordLocation": str(annotation.absolute_uri),
                    "annotation": annotation.value,
                }]
        else:
            result["errors"] = []
            for error in scope.collect_errors():
                result["errors"] += [{
                    "instanceLocation": str(error.instance_path),
                    "keywordLocation": str(error.evaluation_path),
                    "absoluteKeywordLocation": str(error.absolute_uri),
                    "error": error.message,
                }]

        return result

    @staticmethod
    def _detailed(scope: Scope) -> Dict[str, Any]:
        raise NotImplementedError

    @staticmethod
    def _verbose(scope: Scope) -> Dict[str, Any]:
        raise NotImplementedError
