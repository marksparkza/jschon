from typing import Any, Callable, Dict

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
def basic(result: Result) -> JSONCompatible:
    def visit(node: Result):
        if node.valid == result.valid:
            if isinstance(node.schema_node, JSONSchema):
                output = {
                    "valid": node.valid,
                    "evaluationPath": str(node.path),
                    "schemaLocation": str(node.absolute_uri),
                    "instanceLocation": str(node.instance.path),
                }
                annotations = {}
                errors = {}
                for child in node.children.values():
                    if result.valid and child.annotation is not None:
                        annotations[child.key] = child.annotation
                    elif not result.valid and child.error is not None:
                        errors[child.key] = child.error

                if result.valid and annotations:
                    output["annotations"] = annotations
                    yield output
                elif not result.valid and errors:
                    output["errors"] = errors
                    yield output

                for child in node.children.values():
                    yield from (
                        childout for childout in (visit(child))
                        if child.valid == result.valid
                    )

            else:
                for child in node.children.values():
                    yield from visit(child)

    return {
        "valid": result.valid,
        "nested": [output for output in visit(result)],
    }


@output_formatter('hierarchical')
def hierarchical(result: Result) -> JSONCompatible:
    def visit(node: Result):
        if node.valid == result.valid:
            if isinstance(node.schema_node, JSONSchema):
                output = {
                    "valid": node.valid,
                    "evaluationPath": str(node.path),
                    "schemaLocation": str(node.absolute_uri),
                    "instanceLocation": str(node.instance.path),
                }
                nested = []
                annotations = {}
                errors = {}
                for child in node.children.values():
                    nested += [
                        childout for childout in (visit(child))
                        if child.valid == result.valid
                    ]
                    if result.valid and child.annotation is not None:
                        annotations[child.key] = child.annotation
                    elif not result.valid and child.error is not None:
                        errors[child.key] = child.error

                if nested:
                    output["nested"] = nested

                if result.valid and annotations:
                    output["annotations"] = annotations
                elif not result.valid and errors:
                    output["errors"] = errors

                yield output

            else:
                for child in node.children.values():
                    yield from visit(child)

    return list(visit(result))[0]


@output_formatter('verbose')
def verbose(result: Result) -> JSONCompatible:
    def visit(node: Result):
        output = {
            "valid": (valid := node.valid),
            "evaluationPath": str(node.path),
            "schemaLocation": str(node.absolute_uri),
            "instanceLocation": str(node.instance.path),
        }

        msgkey = "annotation" if valid else "error"
        if (msgval := getattr(node, msgkey)) is not None:
            output[msgkey] = msgval

        childkey = "annotations" if valid else "errors"
        if childarr := [visit(child) for child in node.children.values()]:
            output[childkey] = childarr

        return output

    return visit(result)
