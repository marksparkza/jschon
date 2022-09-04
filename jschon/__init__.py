from .catalog import Catalog, LocalSource, RemoteSource
from .exceptions import CatalogError, JSONError, JSONPatchError, JSONPointerError, JSONSchemaError, RelativeJSONPointerError, URIError
from .json import JSON
from .jsonpatch import JSONPatch, JSONPatchOperation
from .jsonpointer import JSONPointer, RelativeJSONPointer
from .jsonschema import JSONSchema, Result
from .uri import URI

__all__ = [
    'Catalog',
    'CatalogError',
    'JSON',
    'JSONError',
    'JSONPatch',
    'JSONPatchError',
    'JSONPatchOperation',
    'JSONPointer',
    'JSONPointerError',
    'JSONSchema',
    'JSONSchemaError',
    'LocalSource',
    'RelativeJSONPointer',
    'RelativeJSONPointerError',
    'RemoteSource',
    'Result',
    'URI',
    'URIError',
    'create_catalog',
]

__version__ = '0.10.0'


def create_catalog(*vocabularies: str, name: str = 'catalog') -> Catalog:
    """Create and return a :class:`~jschon.catalog.Catalog` instance,
    initialized with a meta-schema and keyword support for each of the
    specified JSON Schema `vocabularies`.

    :param vocabularies: Any of ``2019-09``, ``2020-12``.
    :param name: A unique name for the :class:`~jschon.catalog.Catalog` instance.
    :raise ValueError: If any of `vocabularies` is unrecognized.
    """
    from .catalog import _2019_09, _2020_12

    catalog = Catalog(name=name)

    vocabulary_initializers = {
        '2019-09': _2019_09.initialize,
        '2020-12': _2020_12.initialize,
    }
    try:
        for vocabulary in vocabularies:
            vocabulary_init = vocabulary_initializers[vocabulary]
            vocabulary_init(catalog)

    except KeyError as e:
        raise ValueError(f'Unsupported vocabulary "{e.args[0]}"')

    return catalog
