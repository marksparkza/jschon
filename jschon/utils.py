import json
from decimal import Decimal
from os import PathLike
from typing import Any, Tuple, Iterable, Union

__all__ = [
    'tuplify',
    'json_loadf',
    'json_loadr',
    'json_loads',
]

requests = None


def _import_requests():
    global requests
    try:
        import requests
    except ImportError as e:
        raise ImportError('requests is not installed, run `pip install jschon[requests]`') from e


def tuplify(value: Any) -> Tuple:
    if value is None:
        return ()
    if isinstance(value, Tuple):
        return value
    if isinstance(value, Iterable) and not isinstance(value, str):
        return tuple(value)
    return value,


def json_loadf(path: Union[str, PathLike]) -> Any:
    """Open and deserialize a JSON file, returning a JSON-compatible Python object."""
    with open(path) as f:
        return json.load(f, parse_float=Decimal, parse_constant=_parse_invalid_const)


def json_loadr(url: str) -> Any:
    """Fetch and deserialize a remote JSON resource, returning a JSON-compatible Python object."""
    if requests is None:
        _import_requests()
    r = requests.get(url)
    r.raise_for_status()
    return r.json(parse_float=Decimal, parse_constant=_parse_invalid_const)


def json_loads(value: str) -> Any:
    """Deserialize a JSON string, returning a JSON-compatible Python object."""
    return json.loads(value, parse_float=Decimal, parse_constant=_parse_invalid_const)


def _parse_invalid_const(c):
    """Called when '-Infinity', 'Infinity' or 'NaN' is encountered in the
    JSON-encoded input. These JavaScript constants are not strictly allowed
    by the JSON data model."""
    raise ValueError(f"{c} is not a valid JSON value")
