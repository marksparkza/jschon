from typing import Any, Dict

from jschon.json import JSONCompatible
from jschon.jsonschema import Scope

__all__ = [
    'OutputFormatter',
    'JSONSchemaOutputFormatter',
]


class OutputFormatter:

    def create_output(self, scope: Scope, format: str, **kwargs: Any) -> JSONCompatible:
        raise NotImplementedError


class JSONSchemaOutputFormatter(OutputFormatter):

    def create_output(self, scope: Scope, format: str, **kwargs: Any) -> JSONCompatible:
        if format == 'flag':
            return self._flag(scope)
        if format == 'basic':
            return self._basic(scope)
        if format == 'detailed':
            return self._detailed(scope)
        if format == 'verbose':
            return self._verbose(scope)

    @staticmethod
    def _flag(scope: Scope) -> Dict[str, JSONCompatible]:
        return {
            "valid": scope.valid
        }

    @staticmethod
    def _basic(scope: Scope) -> Dict[str, JSONCompatible]:
        def visit(node: Scope):
            if node.valid is valid:
                if (msgval := getattr(node, msgkey)) is not None:
                    yield {
                        "instanceLocation": str(node.instance.path),
                        "keywordLocation": str(node.path),
                        "absoluteKeywordLocation": str(node.absolute_uri),
                        msgkey: msgval,
                    }
                for child in node.iter_children():
                    yield from visit(child)

        valid = scope.valid
        msgkey = "annotation" if valid else "error"
        childkey = "annotations" if valid else "errors"

        return {
            "valid": valid,
            childkey: [result for result in visit(scope)],
        }

    @staticmethod
    def _detailed(scope: Scope) -> Dict[str, JSONCompatible]:
        def visit(node: Scope):
            result = {
                "instanceLocation": str(node.instance.path),
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
            "instanceLocation": str(scope.instance.path),
            "keywordLocation": str(scope.path),
            "absoluteKeywordLocation": str(scope.absolute_uri),
            childkey: [visit(child) for child in scope.iter_children()
                       if child.valid is valid],
        }

    @staticmethod
    def _verbose(scope: Scope) -> Dict[str, JSONCompatible]:
        def visit(node: Scope):
            result = {
                "valid": (valid := node.valid),
                "instanceLocation": str(node.instance.path),
                "keywordLocation": str(node.path),
                "absoluteKeywordLocation": str(node.absolute_uri),
            }

            msgkey = "annotation" if valid else "error"
            if (msgval := getattr(node, msgkey)) is not None:
                result[msgkey] = msgval

            childkey = "annotations" if valid else "errors"
            if childarr := [visit(child) for child in node.iter_children()]:
                result[childkey] = childarr

            return result

        return visit(scope)
