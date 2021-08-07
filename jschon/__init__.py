from .catalogue import Catalogue
from .exceptions import CatalogueError, JSONSchemaError, JSONPointerError, URIError
from .json import JSON
from .jsonpointer import JSONPointer
from .jsonschema import JSONSchema
from .uri import URI

__all__ = [
    'Catalogue',
    'CatalogueError',
    'JSON',
    'JSONPointer',
    'JSONPointerError',
    'JSONSchema',
    'JSONSchemaError',
    'URI',
    'URIError',
    'create_catalogue',
]

__version__ = '0.7.0'


def create_catalogue(*versions: str, default: bool = False) -> Catalogue:
    """Create and return a new :class:`~jschon.catalogue.Catalogue` instance,
    optionally pre-populated with :class:`~jschon.vocabulary.Metaschema` objects
    supporting one or more versions of the JSON Schema vocabulary.

    :param versions: any of ``'2019-09'``, ``'2020-12'``
    :param default: if True, new :class:`~jschon.jsonschema.JSONSchema`
        instances are by default cached in this catalogue
    :raise CatalogueError: if a supplied version parameter is not recognized
    """
    return Catalogue(*versions, default=default)
