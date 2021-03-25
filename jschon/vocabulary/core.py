from typing import Mapping, Any

from jschon.catalogue import Catalogue
from jschon.exceptions import JSONSchemaError, URIError, CatalogueError
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

    def __init__(
            self,
            parentschema: JSONSchema,
            key: str,
            value: str,
            *args: Any,
            **kwargs: Any,
    ):
        super().__init__(parentschema, key, value, *args, **kwargs)

        try:
            (uri := URI(value)).validate(require_scheme=True, require_normalized=True)
        except URIError as e:
            raise JSONSchemaError from e

        parentschema.metaschema_uri = uri

    def can_evaluate(self, instance: JSON) -> bool:
        return False


class VocabularyKeyword(Keyword):

    def __init__(
            self,
            parentschema: JSONSchema,
            key: str,
            value: Mapping[str, bool],
            *args: Any,
            **kwargs: Any,
    ):
        super().__init__(parentschema, key, value, *args, **kwargs)

        if not isinstance(parentschema, Metaschema):
            return

        if (core_vocab_uri := str(parentschema.core_vocabulary.uri)) not in value or \
                value[core_vocab_uri] is not True:
            raise JSONSchemaError(f'The "{key}" keyword must list the core vocabulary with a value of true')

        for vocab_uri, vocab_required in value.items():
            try:
                (vocab_uri := URI(vocab_uri)).validate(require_scheme=True, require_normalized=True)
            except URIError as e:
                raise JSONSchemaError from e

            try:
                vocabulary = Catalogue.get_vocabulary(vocab_uri)
                parentschema.kwdefs.update(vocabulary.kwdefs)
            except CatalogueError:
                if vocab_required:
                    raise JSONSchemaError(f"The metaschema requires an unrecognized vocabulary '{vocab_uri}'")

    def can_evaluate(self, instance: JSON) -> bool:
        return False


class IdKeyword(Keyword):

    def __init__(
            self,
            parentschema: JSONSchema,
            key: str,
            value: str,
            *args: Any,
            **kwargs: Any,
    ):
        super().__init__(parentschema, key, value, *args, **kwargs)

        (uri := URI(value)).validate(require_normalized=True, allow_fragment=False)
        if not uri.is_absolute():
            if (base_uri := parentschema.base_uri) is not None:
                uri = uri.resolve(base_uri)
            else:
                raise JSONSchemaError(f'No base URI against which to resolve the "{key}" value "{value}"')

        parentschema.uri = uri

    def can_evaluate(self, instance: JSON) -> bool:
        return False


class RefKeyword(Keyword):

    def __init__(
            self,
            parentschema: JSONSchema,
            key: str,
            value: str,
            *args: Any,
            **kwargs: Any,
    ):
        super().__init__(parentschema, key, value, *args, **kwargs)
        self.refschema = None

    def resolve(self) -> None:
        uri = URI(self.json.value)
        if not uri.can_absolute():
            if (base_uri := self.parentschema.base_uri) is not None:
                uri = uri.resolve(base_uri)
            else:
                raise JSONSchemaError(f'No base URI against which to resolve the "{self.key}" value "{uri}"')

        self.refschema = Catalogue.get_schema(uri, metaschema_uri=self.parentschema.metaschema_uri)

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        self.refschema.evaluate(instance, scope)


class AnchorKeyword(Keyword):

    def __init__(
            self,
            parentschema: JSONSchema,
            key: str,
            value: str,
            *args: Any,
            **kwargs: Any,
    ):
        super().__init__(parentschema, key, value, *args, **kwargs)

        if (base_uri := parentschema.base_uri) is not None:
            uri = URI(f'{base_uri}#{value}')
        else:
            raise JSONSchemaError(f'No base URI for "{key}" value "{value}"')

        # just add a schema reference to the catalogue, rather than updating
        # the schema URI itself; this way we keep canonical URIs consistent
        # for subschemas regardless of anchor usage
        # parentschema.uri = uri
        Catalogue.add_schema(uri, parentschema)

    def can_evaluate(self, instance: JSON) -> bool:
        return False


class DynamicRefKeyword(Keyword):

    def __init__(
            self,
            parentschema: JSONSchema,
            key: str,
            value: str,
            *args: Any,
            **kwargs: Any,
    ):
        super().__init__(parentschema, key, value, *args, **kwargs)

        if value != '#':
            raise JSONSchemaError(f'"{key}" may only take the value "#"')

        self.keymap.setdefault("$dynamicAnchor", "$dynamicAnchor")

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        if (base_uri := self.parentschema.base_uri) is not None:
            refschema = Catalogue.get_schema(base_uri, metaschema_uri=self.parentschema.metaschema_uri)
        else:
            raise JSONSchemaError(f'No base URI against which to resolve the "{self.key}" value "{self.json.value}"')

        if (dynamic_anchor := refschema.get(self.keymap["$dynamicAnchor"])) and \
                dynamic_anchor.value is True:
            base_scope = scope.root
            for key in scope.path:
                if isinstance(base_schema := base_scope.schema, JSONSchema):
                    if base_schema is refschema:
                        break
                    if (base_anchor := base_schema.get(self.keymap["$dynamicAnchor"])) and \
                            base_anchor.value is True:
                        refschema = base_schema
                        break
                base_scope = base_scope.children[key]

        refschema.evaluate(instance, scope)


class DynamicAnchorKeyword(Keyword):

    def can_evaluate(self, instance: JSON) -> bool:
        return False


class DefsKeyword(Keyword, PropertyApplicator):

    def can_evaluate(self, instance: JSON) -> bool:
        return False


class CommentKeyword(Keyword):

    def can_evaluate(self, instance: JSON) -> bool:
        return False
