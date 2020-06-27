import typing as _t

__all__ = [
    'tuplify',
    'arrayify',
]


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
