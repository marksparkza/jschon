from __future__ import annotations

from typing import Dict, Iterator

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
            result["annotations"] = [annotation for annotation in OutputFormatter._flatten_annotations(scope)]
        else:
            result["errors"] = [error for error in OutputFormatter._flatten_errors(scope)]

        return result

    @staticmethod
    def detailed(scope: Scope) -> Dict[str, AnyJSONCompatible]:
        raise NotImplementedError

    @staticmethod
    def verbose(scope: Scope) -> Dict[str, AnyJSONCompatible]:
        def visit(node: Scope):
            result = {
                "valid": node.valid,
                "instanceLocation": str(node.instpath),
                "keywordLocation": str(node.path),
                "absoluteKeywordLocation": str(node.absolute_uri),
            }
            if node.valid:
                if node.annotation is not None:
                    result["annotation"] = node.annotation
                result["annotations"] = [visit(child) for child in node.iter_children()]
                if not result["annotations"]:
                    del result["annotations"]
            else:
                result["errors"] = [visit(child) for child in node.iter_children()]
                if not result["errors"]:
                    del result["errors"]
                    result["error"] = node.error

            return result

        return visit(scope)

    @staticmethod
    def _flatten_annotations(scope: Scope) -> Iterator[Dict]:
        if not scope.error:
            if scope.annotation is not None:
                yield {
                    "instanceLocation": str(scope.instpath),
                    "keywordLocation": str(scope.path),
                    "absoluteKeywordLocation": str(scope.absolute_uri),
                    "annotation": scope.annotation,
                }
            for child in scope.iter_children():
                yield from OutputFormatter._flatten_annotations(child)

    @staticmethod
    def _flatten_errors(scope: Scope) -> Iterator[Dict]:
        if not scope.valid:
            yield {
                "instanceLocation": str(scope.instpath),
                "keywordLocation": str(scope.path),
                "absoluteKeywordLocation": str(scope.absolute_uri),
                "error": scope.error,
            }
            for child in scope.iter_children():
                yield from OutputFormatter._flatten_errors(child)
