import json
from decimal import Decimal
from os import PathLike
from typing import Any, Tuple, Iterable, Union

__all__ = [
    'tuplify',
    'json_loadf',
    'json_loads',
]


def tuplify(value: Any) -> Tuple:
    if value is None:
        return ()
    if isinstance(value, Tuple):
        return value
    if isinstance(value, Iterable) and not isinstance(value, str):
        return tuple(value)
    return value,


def json_loadf(path: Union[str, PathLike]) -> Any:
    """Deserialize a JSON file to a JSON-compatible Python object."""
    with open(path) as f:
        return json.load(f, parse_float=Decimal, parse_constant=_parse_invalid_const)


def json_loads(value: str) -> Any:
    """Deserialize a JSON string to a JSON-compatible Python object."""
    return json.loads(value, parse_float=Decimal, parse_constant=_parse_invalid_const)


def _parse_invalid_const(c):
    """Called when '-Infinity', 'Infinity' or 'NaN' is encountered in the
    JSON-encoded input. These JavaScript constants are not strictly allowed
    by the JSON data model."""
    raise ValueError(f"{c} is not a valid JSON value")
