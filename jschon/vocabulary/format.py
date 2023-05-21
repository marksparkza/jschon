from typing import Callable, Dict, Tuple

from jschon.json import JSON, JSONCompatible
from jschon.jsonschema import JSONSchema, Result
from jschon.vocabulary import Keyword

__all__ = [
    'FormatKeyword',
    'FormatValidator',
    'format_validator',
]


class FormatKeyword(Keyword):
    key = "format"

    def __init__(self, parentschema: JSONSchema, value: str):
        super().__init__(parentschema, value)
        if parentschema.catalog.is_format_enabled(value):
            self.validator, self.validates_types = _format_validators[value]
        else:
            self.validator = None

    def evaluate(self, instance: JSON, result: Result) -> None:
        result.annotate(self.json.value)
        if self.validator and instance.type in self.validates_types:
            try:
                self.validator(instance.data)
            except ValueError as e:
                result.fail(f'The instance is invalid against the "{self.json.data}" format: {e}')
        else:
            result.noassert()


FormatValidator = Callable[[JSONCompatible], None]
"""Call signature for a function decorated with :func:`format_validator`.

The function validates a JSON-compatible Python object (typically, a string)
and raises a :exc:`ValueError` if the object is invalid per the applicable
format specification.
"""

# dict of {'format_attr': (validator_fn, (instance_type, ...))}
_format_validators: Dict[str, Tuple[FormatValidator, Tuple[str, ...]]] = {}


def format_validator(
        format_attr: str,
        *,
        instance_types: Tuple[str, ...] = ('string',)
):
    """A decorator for a format validation function.

    The decorator only registers a function as a format validator.
    Assertion behaviour must be enabled in a catalog using
    :meth:`~jschon.catalog.Catalog.enable_formats`.

    :param format_attr: The format attribute that the decorated function validates.
    :param instance_types: The set of instance types validated by this format.
    """

    def decorator(f: FormatValidator):
        _format_validators[format_attr] = (f, instance_types)
        return f

    return decorator
