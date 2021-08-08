from .catalog import Catalog
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
]

__version__ = '0.7.1'


def create_catalog(*versions: str, default: bool = False) -> Catalog:
    """Create and return a new :class:`~jschon.catalog.Catalog` instance,
    optionally pre-populated with :class:`~jschon.vocabulary.Metaschema` objects
    supporting one or more versions of the JSON Schema vocabulary.

    :param versions: any of ``'2019-09'``, ``'2020-12'``
    :param default: if True, new :class:`~jschon.jsonschema.JSONSchema`
        instances are by default cached in this catalog
    :raise CatalogError: if a supplied version parameter is not recognized
    """
    return Catalog(*versions, default=default)
