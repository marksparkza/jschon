from enum import Enum
from typing import Dict, Any

from jschon.json import JSON
from jschon.jsonschema import JSONSchema, Scope

__all__ = [
    'JSONEvaluator',
    'OutputFormat',
]


class OutputFormat(str, Enum):
    FLAG = 'flag'
    BASIC = 'basic'
    DETAILED = 'detailed'
    VERBOSE = 'verbose'


class JSONEvaluator:
    """JSONEvaluator provides a high-level interface to schema
    validation and instance evaluation, with output formatting."""

    def __init__(self, schema: JSONSchema, instance: JSON):
        self.schema: JSONSchema = schema
        self.instance: JSON = instance

    def validate_schema(self, output_format=OutputFormat.FLAG) -> Dict[str, Any]:
        scope = self.schema.metaschema.evaluate(JSON(self.schema.value))
        fn = eval(f'self.{output_format.value}')
        return fn(scope)

    def evaluate_instance(self, output_format=OutputFormat.FLAG) -> Dict[str, Any]:
        scope = self.schema.evaluate(self.instance)
        fn = eval(f'self.{output_format.value}')
        return fn(scope)

    @staticmethod
    def flag(scope: Scope) -> Dict[str, Any]:
        return {
            "valid": scope.valid
        }

    @staticmethod
    def basic(scope: Scope) -> Dict[str, Any]:
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
    def detailed(scope: Scope) -> Dict[str, Any]:
        raise NotImplementedError

    @staticmethod
    def verbose(scope: Scope) -> Dict[str, Any]:
        raise NotImplementedError
