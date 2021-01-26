from typing import *

__all__ = [
    'JSONCompatible',
    'AnyJSONCompatible',
    'tuplify',
    'arrayify',
]

# for runtime type checks
JSONCompatible = (type(None), bool, int, float, str, Sequence, Mapping)

# for type hints
AnyJSONCompatible = TypeVar('AnyJSONCompatible', 'None', bool, int, float, str, Sequence, Mapping)


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
