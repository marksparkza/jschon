from typing import Mapping

from jschon.exceptions import JSONSchemaError
from jschon.jsonschema import JSONSchema
from jschon.uri import URI
from jschon.vocabulary import Keyword

__all__ = [
    'IdKeyword_Next',
]


class IdKeyword_Next(Keyword):
    key = "$id"
    static = True

    def __init__(self, parentschema: JSONSchema, value: str):
        super().__init__(parentschema, value)

        (uri := URI(value)).validate(allow_fragment=False)
        if not uri.is_absolute():
            if (base_uri := parentschema.base_uri) is not None:
                uri = uri.resolve(base_uri)
            else:
                raise JSONSchemaError(f'No base URI against which to resolve the "$id" value "{value}"')

        parentschema.uri = uri
