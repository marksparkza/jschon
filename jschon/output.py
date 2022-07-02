from typing import Any, Callable, Dict

from jschon.json import JSONCompatible
from jschon.jsonschema import Scope

__all__ = [
    'OutputFormatter',
    'output_formatter',
    'create_output',
]

OutputFormatter = Callable[..., JSONCompatible]
"""Call signature for a function decorated with :func:`output_formatter`.

The function must take a :class:`~jschon.jsonschema.Scope` object
as its first argument.
"""

_formatters: Dict[str, OutputFormatter] = {}


def output_formatter(name: str = None):
    """A decorator for a JSON Schema output formatting function.

    :param name: The format name; defaults to the name of the decorated
        function.
    """

    def decorator(f):
        formatter_name = name if isinstance(name, str) else f.__name__
        _formatters[formatter_name] = f
        return f

    return decorator(name) if callable(name) else decorator


def create_output(scope: Scope, format: str, **kwargs: Any) -> JSONCompatible:
    return _formatters[format](scope, **kwargs)


@output_formatter
def flag(scope: Scope) -> JSONCompatible:
    return {
        "valid": scope.valid
    }


@output_formatter
def basic(scope: Scope) -> JSONCompatible:
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


@output_formatter
def detailed(scope: Scope) -> JSONCompatible:
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


@output_formatter
def verbose(scope: Scope) -> JSONCompatible:
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
