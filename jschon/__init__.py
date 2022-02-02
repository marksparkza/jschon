from .catalog import Catalog, LocalSource, RemoteSource
from .exceptions import CatalogError, JSONPatchError, JSONPointerError, JSONSchemaError, RelativeJSONPointerError, URIError
from .json import JSON
from .jsonpatch import JSONPatch, JSONPatchOperation
from .jsonpointer import JSONPointer, RelativeJSONPointer
from .jsonschema import JSONSchema
from .uri import URI

__all__ = [
    'Catalog',
    'CatalogError',
    'JSON',
    'JSONPatch',
    'JSONPatchError',
    'JSONPatchOperation',
    'JSONPointer',
    'JSONPointerError',
    'RelativeJSONPointer',
    'RelativeJSONPointerError',
    'JSONSchema',
    'JSONSchemaError',
    'LocalSource',
    'RemoteSource',
    'URI',
    'URIError',
    'create_catalog',
]

__version__ = '0.8.4'


def create_catalog(*vocabularies: str, name: str = 'catalog') -> Catalog:
    """Create and return a :class:`Catalog` instance, configured with
    support for the specified JSON Schema vocabularies.

    :param vocabularies: any of ``2019-09``, ``2020-12``, ``translation``
    :param name: a unique name for the :class:`Catalog` instance
    :raise ValueError: if a supplied vocabulary parameter is not recognized
    """
    from .catalog import _2019_09, _2020_12, _translation

    catalog = Catalog(name=name)

    vocabulary_initializers = {
        '2019-09': _2019_09.initialize,
        '2020-12': _2020_12.initialize,
        'translation': _translation.initialize,
    }
    try:
        for vocabulary in vocabularies:
            vocabulary_init = vocabulary_initializers[vocabulary]
            vocabulary_init(catalog)

    except KeyError as e:
        raise ValueError(f'Unsupported vocabulary "{e.args[0]}"')

    return catalog
