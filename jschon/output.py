from __future__ import annotations

from typing import Dict

from jschon.json import AnyJSONCompatible
from jschon.jsonschema import Scope

__all__ = [
    'OutputFormatter',
]


class OutputFormatter:

    @staticmethod
    def flag(scope: Scope) -> Dict[str, AnyJSONCompatible]:
        return {
            "valid": scope.valid
        }

    @staticmethod
    def basic(scope: Scope) -> Dict[str, AnyJSONCompatible]:
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
    def detailed(scope: Scope) -> Dict[str, AnyJSONCompatible]:
        raise NotImplementedError

    @staticmethod
    def verbose(scope: Scope) -> Dict[str, AnyJSONCompatible]:
        raise NotImplementedError
