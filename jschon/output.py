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
        def flatten_results(node: Scope, prop: str):
            if (prop == 'annotation' and node.valid) or not node.valid:
                if (propval := getattr(node, prop)) is not None:
                    yield {
                        "instanceLocation": str(node.instpath),
                        "keywordLocation": str(node.path),
                        "absoluteKeywordLocation": str(node.absolute_uri),
                        prop: propval,
                    }
                for child in node.iter_children():
                    yield from flatten_results(child, prop)

        result = {
            "valid": scope.valid
        }
        if result["valid"]:
            result["annotations"] = [annotation for annotation in flatten_results(scope, 'annotation')]
        else:
            result["errors"] = [error for error in flatten_results(scope, 'error')]

        return result

    @staticmethod
    def detailed(scope: Scope) -> Dict[str, AnyJSONCompatible]:
        def visit(node: Scope):
            result = {
                "instanceLocation": str(node.instpath),
                "keywordLocation": str(node.path),
                "absoluteKeywordLocation": str(node.absolute_uri),
                childkey: [visit(child) for child in node.iter_children()
                           if child.valid is valid],
            }
            if not result[childkey]:
                del result[childkey]
                if (msgval := getattr(node, msgkey)) is not None:
                    result[msgkey] = msgval
            elif len(result[childkey]) == 1:
                result = result[childkey][0]

            return result

        valid = scope.valid
        msgkey = "annotation" if valid else "error"
        childkey = "annotations" if valid else "errors"
        return {
            "valid": valid,
            "instanceLocation": "",
            "keywordLocation": "",
            childkey: [visit(child) for child in scope.iter_children()
                       if child.valid is valid],
        }

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
                result["error"] = node.error
                result["errors"] = [visit(child) for child in node.iter_children()]
                if not result["errors"]:
                    del result["errors"]

            return result

        return visit(scope)
