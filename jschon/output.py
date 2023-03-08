from typing import Any, Callable, Dict, Iterable

from jschon.json import JSONCompatible
from jschon.jsonschema import JSONSchema, Result

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


def output_formatter(format: str):
    """A decorator for a JSON Schema output formatting function.

    :param format: A string identifying the output format.
    """

    def decorator(f: OutputFormatter):
        _formatters[format] = f
        return f

    return decorator


def create_output(result: Result, format: str, **kwargs: Any) -> JSONCompatible:
    return _formatters[format](result, **kwargs)


@output_formatter('flag')
def flag(result: Result) -> JSONCompatible:
    return {
        "valid": result.valid
    }


@output_formatter('basic')
def basic(result: Result, annotations: Iterable[str] = None) -> JSONCompatible:
    def visit(node: Result):
        if node.valid is valid:
            if (
                    (annotations is None or node.key in annotations) and
                    (msgval := getattr(node, msgkey)) is not None
            ):
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


@output_formatter('detailed')
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


@output_formatter('verbose')
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


@output_formatter('hierarchical')
def hierarchical(result: Result) -> JSONCompatible:
    def visit(node: Result):
        if isinstance(node.schema_node, JSONSchema):
            output = {
                "valid": (valid := node.valid),
                "evaluationPath": str(node.path),
                "schemaLocation": str(node.absolute_uri),
                "instanceLocation": str(node.instance.path),
            }
            details = []
            annotations = {}
            errors = {}
            for child in node.children.values():
                details += [
                    childout for childout in (visit(child))
                    if child.valid == valid
                ]
                if valid and child.annotation is not None:
                    annotations[child.key] = child.annotation
                elif not valid and child.error is not None:
                    errors[child.key] = child.error

            if details:
                output["details"] = details
            if valid and annotations:
                output["annotations"] = annotations
            elif not valid and errors:
                output["errors"] = errors

            yield output

        else:
            for child in node.children.values():
                yield from visit(child)

    return list(visit(result))[0]
