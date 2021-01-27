from typing import *

__all__ = [
    'tuplify',
    'arrayify',
]


def tuplify(value: Any) -> Tuple:
    if value is None:
        return ()
    if isinstance(value, Tuple):
        return value
    if isinstance(value, Iterable) and not isinstance(value, str):
        return tuple(value)
    return value,


def arrayify(value: Any) -> List:
    if value is None:
        return []
    if isinstance(value, List):
        return value
    if isinstance(value, Iterable) and not isinstance(value, str):
        return list(value)
    return [value]
