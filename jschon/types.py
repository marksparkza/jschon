from typing import *

__all__ = [
    'JSONCompatible',
    'AnyJSONCompatible',
    'is_schema_compatible',
    'tuplify',
    'arrayify',
]

# for runtime type checks
JSONCompatible = (type(None), bool, int, float, str, Sequence, Mapping)

# for type hints
AnyJSONCompatible = TypeVar('AnyJSONCompatible', 'None', bool, int, float, str, Sequence, Mapping)


def is_schema_compatible(value: Any, allowbool: bool = True) -> bool:
    return (allowbool and isinstance(value, bool)) or \
           (isinstance(value, Mapping) and
            all(isinstance(k, str) and isinstance(v, JSONCompatible)
                for k, v in value.items()))


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
