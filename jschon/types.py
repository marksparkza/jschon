import typing as _t

__all__ = [
    'JSONCompatible',
    'SchemaCompatible',
]

JSONCompatible = (type(None), bool, int, float, str, _t.Sequence, _t.Mapping)
SchemaCompatible = (bool, _t.Mapping)
