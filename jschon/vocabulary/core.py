from typing import Mapping

from jschon.catalogue import Catalogue
from jschon.exceptions import JSONSchemaError, URIError, CatalogueError, JSONPointerError
from jschon.json import JSON
from jschon.jsonschema import Keyword, JSONSchema, Scope, PropertyApplicator, Metaschema
from jschon.uri import URI

__all__ = [
    'SchemaKeyword',
    'VocabularyKeyword',
    'IdKeyword',
    'RefKeyword',
    'AnchorKeyword',
    'DynamicRefKeyword',
    'DynamicAnchorKeyword',
    'DefsKeyword',
    'CommentKeyword',
]


class SchemaKeyword(Keyword):
    key = "$schema"

    def __init__(self, parentschema: JSONSchema, value: str):
        super().__init__(parentschema, value)

        try:
            (uri := URI(value)).validate(require_scheme=True, require_normalized=True)
        except URIError as e:
            raise JSONSchemaError from e

        parentschema.metaschema_uri = uri

    def can_evaluate(self, instance: JSON) -> bool:
        return False


class VocabularyKeyword(Keyword):
    key = "$vocabulary"

    def __init__(self, parentschema: JSONSchema, value: Mapping[str, bool]):
        super().__init__(parentschema, value)

        if not isinstance(parentschema, Metaschema):
            return

        if (core_vocab_uri := str(parentschema.core_vocabulary.uri)) not in value or \
                value[core_vocab_uri] is not True:
            raise JSONSchemaError(f'The "$vocabulary" keyword must list the core vocabulary with a value of true')

        for vocab_uri, vocab_required in value.items():
            try:
                (vocab_uri := URI(vocab_uri)).validate(require_scheme=True, require_normalized=True)
            except URIError as e:
                raise JSONSchemaError from e

            try:
                vocabulary = Catalogue.get_vocabulary(vocab_uri)
                parentschema.kwclasses.update(vocabulary.kwclasses)
            except CatalogueError:
                if vocab_required:
                    raise JSONSchemaError(f"The metaschema requires an unrecognized vocabulary '{vocab_uri}'")

    def can_evaluate(self, instance: JSON) -> bool:
        return False


class IdKeyword(Keyword):
    key = "$id"

    def __init__(self, parentschema: JSONSchema, value: str):
        super().__init__(parentschema, value)

        (uri := URI(value)).validate(require_normalized=True, allow_fragment=False)
        if not uri.is_absolute():
            if (base_uri := parentschema.base_uri) is not None:
                uri = uri.resolve(base_uri)
            else:
                raise JSONSchemaError(f'No base URI against which to resolve the "$id" value "{value}"')

        parentschema.uri = uri

    def can_evaluate(self, instance: JSON) -> bool:
        return False


class RefKeyword(Keyword):
    key = "$ref"

    def __init__(self, parentschema: JSONSchema, value: str):
        super().__init__(parentschema, value)
        self.refschema = None

    def resolve(self) -> None:
        uri = URI(self.json.value)
        if not uri.has_absolute_base():
            if (base_uri := self.parentschema.base_uri) is not None:
                uri = uri.resolve(base_uri)
            else:
                raise JSONSchemaError(f'No base URI against which to resolve the "$ref" value "{uri}"')

        self.refschema = Catalogue.get_schema(uri, metaschema_uri=self.parentschema.metaschema_uri)

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        self.refschema.evaluate(instance, scope)


class AnchorKeyword(Keyword):
    key = "$anchor"

    def __init__(self, parentschema: JSONSchema, value: str):
        super().__init__(parentschema, value)

        if (base_uri := parentschema.base_uri) is not None:
            uri = URI(f'{base_uri}#{value}')
        else:
            raise JSONSchemaError(f'No base URI for "$anchor" value "{value}"')

        # just add a schema reference to the catalogue, rather than updating
        # the schema URI itself; this way we keep canonical URIs consistent
        # for subschemas regardless of anchor usage
        # parentschema.uri = uri
        Catalogue.add_schema(uri, parentschema)

    def can_evaluate(self, instance: JSON) -> bool:
        return False


class DynamicRefKeyword(Keyword):
    key = "$dynamicRef"

    def __init__(self, parentschema: JSONSchema, value: str):
        super().__init__(parentschema, value)
        self.refschema = None

    def resolve(self) -> None:
        uri = URI(self.json.value)
        if not uri.has_absolute_base():
            if (base_uri := self.parentschema.base_uri) is not None:
                uri = uri.resolve(base_uri)
            else:
                raise JSONSchemaError(f'No base URI against which to resolve the "$dynamicRef" value "{uri}"')

        self.refschema = Catalogue.get_schema(uri, metaschema_uri=self.parentschema.metaschema_uri)

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        refschema = self.refschema
        if dynamic_anchor := refschema.get("$dynamicAnchor"):
            base_scope = scope.root
            for key in scope.path:
                if isinstance(base_schema := base_scope.schema, JSONSchema):
                    if base_schema is refschema:
                        break
                    # Does this schema resource define an identical anchor?
                    sought_uri = URI(f"#{dynamic_anchor.value}").resolve(
                        base_schema.base_uri
                    )
                    try:
                        resolved_schema = Catalogue.get_schema(
                            sought_uri,
                            metaschema_uri=base_schema.metaschema_uri,
                        )
                    except JSONPointerError:
                        # The anchor couldn't be found, so Catalogue tried (and
                        # failed) to use it as a JSONPointer.
                        pass
                    else:
                        # Was the anchor created with $dynamicAnchor?
                        if resolved_schema.get("$dynamicAnchor") == dynamic_anchor:
                            refschema = resolved_schema
                            break
                base_scope = base_scope.children[key]

        refschema.evaluate(instance, scope)


class DynamicAnchorKeyword(Keyword):
    key = "$dynamicAnchor"

    def __init__(self, parentschema: JSONSchema, value: str):
        super().__init__(parentschema, value)

        if (base_uri := parentschema.base_uri) is not None:
            uri = URI(f'{base_uri}#{value}')
        else:
            raise JSONSchemaError(f'No base URI for "$dynamicAnchor" value "{value}"')

        Catalogue.add_schema(uri, parentschema)

    def can_evaluate(self, instance: JSON) -> bool:
        return False


class DefsKeyword(Keyword, PropertyApplicator):
    key = "$defs"

    def can_evaluate(self, instance: JSON) -> bool:
        return False


class CommentKeyword(Keyword):
    key = "$comment"

    def can_evaluate(self, instance: JSON) -> bool:
        return False
