class JschonError(Exception):
    """Generic error class."""


class CatalogError(JschonError):
    """An error originating in the :mod:`~jschon.catalog` module."""


class JSONError(JschonError):
    """An error originating in the :class:`~jschon.json` module."""


class JSONPatchError(JschonError):
    """An error originating in the :mod:`~jschon.jsonpatch` module."""


class JSONPointerError(JschonError):
    """An error originating in the :mod:`~jschon.jsonpointer` module."""


class JSONPointerMalformedError(JSONPointerError):
    """Raised for an invalid :class:`~jschon.jsonpointer.JSONPointer`
    constructor argument."""


class JSONPointerReferenceError(JSONPointerError):
    """Raised when a :class:`~jschon.jsonpointer.JSONPointer`
    evaluates a non-existent location in a document."""


class RelativeJSONPointerMalformedError(JSONPointerError):
    """Raised for an invalid :class:`~jschon.jsonpointer.RelativeJSONPointer`
    constructor argument."""


class RelativeJSONPointerReferenceError(JSONPointerError):
    """Raised when a :class:`~jschon.jsonpointer.RelativeJSONPointer`
    evaluates a non-existent location in a document."""


class JSONSchemaError(JschonError):
    """Raised when an error occurs during construction of a
    :class:`~jschon.jsonschema.JSONSchema` object. May be raised by
    :class:`~jschon.vocabulary.Keyword` initializers and reference
    resolution methods.
    """


class URIError(JschonError):
    """An error originating in the :mod:`~jschon.uri` module."""
