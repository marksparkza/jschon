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
]

__version__ = '0.8.0'
