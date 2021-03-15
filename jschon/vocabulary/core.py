from typing import Mapping

from jschon.catalogue import Catalogue
from jschon.exceptions import JSONSchemaError, URIError
from jschon.json import JSON
from jschon.jsonschema import Keyword, JSONSchema, Scope, PropertyApplicator, Metaschema
from jschon.uri import URI

__all__ = [
    'SchemaKeyword',
    'VocabularyKeyword',
    'IdKeyword',
    'RefKeyword',
    'AnchorKeyword',
    'RecursiveRefKeyword',
    'RecursiveAnchorKeyword',
    'DefsKeyword',
    'CommentKeyword',
]


class SchemaKeyword(Keyword):
    __keyword__ = "$schema"
    __schema__ = {
        "type": "string",
        "format": "uri"
    }

    def __init__(self, parentschema: JSONSchema, value: str):
        super().__init__(parentschema, value)
        if not isinstance(value, str):
            raise JSONSchemaError('Invalid "$schema" keyword value')

        if parentschema.parent is not None:
            raise JSONSchemaError('The "$schema" keyword may not appear in a subschema')

        try:
            (uri := URI(value)).validate(require_scheme=True, require_normalized=True)
        except URIError as e:
            raise JSONSchemaError from e

        parentschema.metaschema_uri = uri


class VocabularyKeyword(Keyword):
    __keyword__ = "$vocabulary"
    __schema__ = {
        "type": "object",
        "propertyNames": {
            "type": "string",
            "format": "uri"
        },
        "additionalProperties": {
            "type": "boolean"
        }
    }

    def __init__(self, parentschema: JSONSchema, value: Mapping[str, bool]):
        super().__init__(parentschema, value)
        if not isinstance(value, Mapping) or \
                not all(isinstance(k, str) and isinstance(v, bool) for k, v in value.items()):
            raise JSONSchemaError('Invalid "$vocabulary" keyword value')

        if parentschema.parent is not None:
            raise JSONSchemaError('The "$vocabulary" keyword may not appear in a subschema')

        if not isinstance(parentschema, Metaschema):
            return

        if (core_vocab_uri := str(parentschema.core_vocabulary.uri)) not in value or \
                value[core_vocab_uri] is not True:
            raise JSONSchemaError('The "$vocabulary" keyword must list the core vocabulary with a value of true')

        for vocab_uri, vocab_required in value.items():
            try:
                (vocab_uri := URI(vocab_uri)).validate(require_scheme=True, require_normalized=True)
            except URIError as e:
                raise JSONSchemaError from e

            if vocabulary := Catalogue.get_vocabulary(vocab_uri):
                parentschema.kwclasses.update(vocabulary.kwclasses)
            elif vocab_required:
                raise JSONSchemaError(f"The metaschema requires an unrecognized vocabulary '{vocab_uri}'")


class IdKeyword(Keyword):
    __keyword__ = "$id"
    __schema__ = {
        "type": "string",
        "format": "uri-reference",
        "$comment": "Non-empty fragments not allowed.",
        "pattern": "^[^#]*#?$"
    }

    def __init__(self, parentschema: JSONSchema, value: str):
        super().__init__(parentschema, value)
        if not isinstance(value, str):
            raise JSONSchemaError('Invalid "$id" keyword value')

        (uri := URI(value)).validate(require_normalized=True, allow_fragment=False)
        if not uri.is_absolute():
            if (base_uri := parentschema.base_uri) is not None:
                uri = uri.resolve(base_uri)
            else:
                raise JSONSchemaError(f'No base URI against which to resolve the "$id" value "{value}"')

        parentschema.uri = uri


class RefKeyword(Keyword):
    __keyword__ = "$ref"
    __schema__ = {
        "type": "string",
        "format": "uri-reference"
    }

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        uri = URI(self.json.value)
        if not uri.can_absolute():
            if (base_uri := self.parentschema.base_uri) is not None:
                uri = uri.resolve(base_uri)
            else:
                raise JSONSchemaError(f'No base URI against which to resolve the "$ref" value "{uri}"')

        refschema = JSONSchema.load(uri, metaschema_uri=self.parentschema.metaschema_uri)
        refschema.evaluate(instance, scope)


class AnchorKeyword(Keyword):
    __keyword__ = "$anchor"
    __schema__ = {
        "type": "string",
        "pattern": "^[A-Za-z][-A-Za-z0-9.:_]*$"
    }

    def __init__(self, parentschema: JSONSchema, value: str):
        super().__init__(parentschema, value)
        if (base_uri := parentschema.base_uri) is not None:
            uri = URI(f'{base_uri}#{value}')
        else:
            raise JSONSchemaError(f'No base URI for anchor "{value}"')

        JSONSchema.store(uri, parentschema)


class RecursiveRefKeyword(Keyword):
    __keyword__ = "$recursiveRef"
    __schema__ = {
        "type": "string",
        "format": "uri-reference"
    }

    def __init__(self, parentschema: JSONSchema, value: str):
        super().__init__(parentschema, value)
        if value != '#':
            raise JSONSchemaError('The "$recursiveRef" keyword may only take the value "#"')

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        if (base_uri := self.parentschema.base_uri) is not None:
            refschema = JSONSchema.load(base_uri, metaschema_uri=self.parentschema.metaschema_uri)
        else:
            raise JSONSchemaError(f'No base URI against which to resolve "$recursiveRef"')

        if (recursive_anchor := refschema.get("$recursiveAnchor")) and \
                recursive_anchor.value is True:
            base_scope = scope.root
            for key in scope.path:
                if isinstance(base_schema := base_scope.schema, JSONSchema):
                    if base_schema is refschema:
                        break
                    if (base_anchor := base_schema.get("$recursiveAnchor")) and \
                            base_anchor.value is True:
                        refschema = base_schema
                        break
                base_scope = base_scope.children[key]

        refschema.evaluate(instance, scope)


class RecursiveAnchorKeyword(Keyword):
    __keyword__ = "$recursiveAnchor"
    __schema__ = {
        "type": "boolean",
        "default": False
    }


class DefsKeyword(Keyword):
    __keyword__ = "$defs"
    __schema__ = {
        "type": "object",
        "additionalProperties": {"$recursiveRef": "#"},
        "default": {}
    }
    applicators = PropertyApplicator,


class CommentKeyword(Keyword):
    __keyword__ = "$comment"
    __schema__ = {"type": "string"}
