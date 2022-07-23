from typing import Any, Callable, Dict

from jschon.json import JSONCompatible
from jschon.jsonschema import Result

__all__ = [
    'OutputFormatter',
    'output_formatter',
    'create_output',
]

OutputFormatter = Callable[..., JSONCompatible]
"""Call signature for a function decorated with :func:`output_formatter`.

The function must take a :class:`~jschon.jsonschema.Result` object
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


def create_output(result: Result, format: str, **kwargs: Any) -> JSONCompatible:
    return _formatters[format](result, **kwargs)


@output_formatter
def flag(result: Result) -> JSONCompatible:
    return {
        "valid": result.valid
    }


@output_formatter
def basic(result: Result) -> JSONCompatible:
    def visit(node: Result):
        if node.valid is valid:
            if (msgval := getattr(node, msgkey)) is not None:
                yield {
                    "instanceLocation": str(node.instance.path),
                    "keywordLocation": str(node.path),
                    "absoluteKeywordLocation": str(node.absolute_uri),
                    msgkey: msgval,
                }
            for child in node.children.values():
                yield from visit(child)

    valid = result.valid
    msgkey = "annotation" if valid else "error"
    childkey = "annotations" if valid else "errors"

    return {
        "valid": valid,
        childkey: [output for output in visit(result)],
    }


@output_formatter
def detailed(result: Result) -> JSONCompatible:
    def visit(node: Result):
        output = {
            "instanceLocation": str(node.instance.path),
            "keywordLocation": str(node.path),
            "absoluteKeywordLocation": str(node.absolute_uri),
            childkey: [visit(child) for child in node.children.values()
                       if child.valid is valid],
        }
        if not output[childkey]:
            del output[childkey]
            if (msgval := getattr(node, msgkey)) is not None:
                output[msgkey] = msgval
        elif len(output[childkey]) == 1:
            output = output[childkey][0]

        return output

    valid = result.valid
    msgkey = "annotation" if valid else "error"
    childkey = "annotations" if valid else "errors"

    return {
        "valid": valid,
        "instanceLocation": str(result.instance.path),
        "keywordLocation": str(result.path),
        "absoluteKeywordLocation": str(result.absolute_uri),
        childkey: [visit(child) for child in result.children.values()
                   if child.valid is valid],
    }


@output_formatter
def verbose(result: Result) -> JSONCompatible:
    def visit(node: Result):
        output = {
            "valid": (valid := node.valid),
            "instanceLocation": str(node.instance.path),
            "keywordLocation": str(node.path),
            "absoluteKeywordLocation": str(node.absolute_uri),
        }

        msgkey = "annotation" if valid else "error"
        if (msgval := getattr(node, msgkey)) is not None:
            output[msgkey] = msgval

        childkey = "annotations" if valid else "errors"
        if childarr := [visit(child) for child in node.children.values()]:
            output[childkey] = childarr

        return output

    return visit(result)
