from .catalog import Catalog, LocalSource, RemoteSource
from .exceptions import CatalogError, JSONError, JSONPatchError, JSONPointerError, JSONSchemaError, URIError
from .json import JSON, JSONCompatible
from .jsonpatch import JSONPatch, JSONPatchOperation
from .jsonpointer import JSONPointer, RelativeJSONPointer
from .jsonschema import JSONSchema, Result
from .uri import URI

__all__ = [
    'Catalog',
    'JSON',
    'JSONCompatible',
    'JSONPatch',
    'JSONPatchOperation',
    'JSONPointer',
    'JSONSchema',
    'LocalSource',
    'RelativeJSONPointer',
    'RemoteSource',
    'Result',
    'URI',
    'create_catalog',
]

__version__ = '0.11.1'


def create_catalog(
    *versions: str,
    name: str = 'catalog',
    resolve_references: bool = True
) -> Catalog:
    """Create and return a :class:`~jschon.catalog.Catalog` instance,
    initialized with a meta-schema and keyword support for each of the
    specified JSON Schema `versions`.

    :param versions: Any of ``2019-09``, ``2020-12``, ``next``.
    :param name: A unique name for the :class:`~jschon.catalog.Catalog` instance.
    :param resolve_references: Passed through to any calls made to the
        :class:`~jschon.jsonschema.JSONSchema` constructor; defaults to ``True``;
        if set to ``False`` a separate call to
        :meth:`~jschon.catalog.Catalog.resolve_references` is required prior to
        evaluating any schemas.
    :raise ValueError: If any of `versions` is unrecognized.
    """
    from .catalog import _2019_09, _2020_12, _next

    catalog = Catalog(name=name, resolve_references=resolve_references)

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
