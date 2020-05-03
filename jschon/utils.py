import typing as _t

import rfc3986.exceptions
import rfc3986.validators

__all__ = [
    'validate_uri',
    'tuplify',
    'arrayify',
]


def validate_uri(uri: str) -> None:
    validator = rfc3986.validators.Validator()
    try:
        validator.validate(rfc3986.uri_reference(uri))
    except rfc3986.exceptions.ValidationError as e:
        raise ValueError(f"'{uri}' is not a valid URI") from e


def tuplify(value: _t.Any) -> _t.Tuple:
    if value is None:
        return ()
    if isinstance(value, _t.Tuple):
        return value
    if isinstance(value, _t.Iterable) and not isinstance(value, str):
        return tuple(value)
    return value,


def arrayify(value: _t.Any) -> _t.List:
    if value is None:
        return []
    if isinstance(value, _t.List):
        return value
    if isinstance(value, _t.Iterable) and not isinstance(value, str):
        return list(value)
    return [value]
