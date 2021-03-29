import json
from decimal import Decimal
from typing import Any, Tuple, Iterable

__all__ = [
    'tuplify',
    'load_json',
]


def tuplify(value: Any) -> Tuple:
    if value is None:
        return ()
    if isinstance(value, Tuple):
        return value
    if isinstance(value, Iterable) and not isinstance(value, str):
        return tuple(value)
    return value,


def load_json(filepath) -> Any:
    def invalid_const(c):
        # called for '-Infinity', 'Infinity' and 'NaN'
        raise ValueError(f"{c} is not a valid JSON value")

    with open(filepath) as f:
        return json.load(f, parse_float=Decimal, parse_constant=invalid_const)
