from .catalog import Catalog, LocalSource, RemoteSource
from .exceptions import CatalogError, JSONSchemaError, JSONPointerError, URIError
from .json import JSON
from .jsonpointer import JSONPointer
from .jsonschema import JSONSchema
from .uri import URI

__all__ = [
    'Catalog',
    'CatalogError',
    'JSON',
    'JSONPointer',
    'JSONPointerError',
    'JSONSchema',
    'JSONSchemaError',
    'URI',
    'URIError',
    'create_catalog',
    'LocalSource',
    'RemoteSource',
]

__version__ = '0.8.0'


def create_catalog(*versions: str, name: str = 'catalog') -> Catalog:
    """Create and return a :class:`Catalog` instance, configured to
    support the specified versions of the JSON Schema vocabulary.

    :param versions: any of ``'2019-09'``, ``'2020-12'``
    :param name: a unique name for the :class:`Catalog` instance
    :raise ValueError: if a supplied version parameter is not recognized
    """
    from .catalog import _2019_09, _2020_12

    catalog = Catalog(name=name)

    version_initializers = {
        '2019-09': _2019_09.initialize,
        '2020-12': _2020_12.initialize,
    }
    try:
        for version in versions:
            version_init = version_initializers[version]
            version_init(catalog)

    except KeyError as e:
        raise ValueError(f'Unsupported version "{e.args[0]}"')

    return catalog
