from .catalog import Catalog, LocalSource, RemoteSource
from .json import JSON, JSONCompatible
from .jsonpatch import JSONPatch, JSONPatchOperation
from .jsonpointer import JSONPointer, RelativeJSONPointer
from .jsonschema import JSONSchema, Result
from .uri import URI

__all__ = [
    'Catalog',
    'LocalSource',
    'RemoteSource',
    'JSON',
    'JSONCompatible',
    'JSONPatch',
    'JSONPatchOperation',
    'JSONPointer',
    'RelativeJSONPointer',
    'JSONSchema',
    'Result',
    'URI',
    'create_catalog',
]

__version__ = '0.12.0'


def create_catalog(*versions: str, name: str = 'catalog') -> Catalog:
    """Create and return a :class:`~jschon.catalog.Catalog` instance,
    initialized with a meta-schema and keyword support for each of the
    specified JSON Schema `versions`.

    The catalog created with the default name of ``'catalog'`` will
    automatically be used wherever a :class:`~jschon.catalog.Catalog`
    instance is needed, unless a different instance is provided.

    :param versions: Any of ``2019-09``, ``2020-12``, ``next``.
    :param name: A unique name for the :class:`~jschon.catalog.Catalog` instance.
    :raise ValueError: If any of `versions` is unrecognized.
    """
    from .catalog import _2019_09, _2020_12, _next

    catalog = Catalog(name=name)

    version_initializers = {
        '2019-09': _2019_09.initialize,
        '2020-12': _2020_12.initialize,
        'next': _next.initialize,
    }
    try:
        for version in versions:
            version_init = version_initializers[version]
            version_init(catalog)

    except KeyError as e:
        raise ValueError(f'Unrecognized version {e.args[0]!r}')

    return catalog
