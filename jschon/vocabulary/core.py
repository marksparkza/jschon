from typing import Mapping

from jschon.exceptions import CatalogError, JSONSchemaError, URIError
from jschon.json import JSON
from jschon.jsonschema import JSONSchema, Result
from jschon.uri import URI
from jschon.vocabulary import Keyword, Metaschema, ObjectOfSubschemas

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
    static = True

    def __init__(self, parentschema: JSONSchema, value: str):
        super().__init__(parentschema, value)

        try:
            (uri := URI(value)).validate(require_scheme=True, require_normalized=True)
        except URIError as e:
            raise JSONSchemaError from e

        parentschema.metaschema_uri = uri


class VocabularyKeyword(Keyword):
    key = "$vocabulary"
    static = True

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
                vocabulary = parentschema.catalog.get_vocabulary(vocab_uri)
                parentschema.kwclasses.update(vocabulary.kwclasses)
            except CatalogError:
                if vocab_required:
                    raise JSONSchemaError(f"The metaschema requires an unrecognized vocabulary '{vocab_uri}'")


class IdKeyword(Keyword):
    key = "$id"
    static = True

    def __init__(self, parentschema: JSONSchema, value: str):
        super().__init__(parentschema, value)

        (uri := URI(value)).validate(allow_non_empty_fragment=False)
        if not uri.is_absolute():
            if (base_uri := parentschema.base_uri) is not None:
                uri = uri.resolve(base_uri)
            else:
                raise JSONSchemaError(f'No base URI against which to resolve the "$id" value "{value}"')

        parentschema.uri = uri


class RefKeyword(Keyword):
    key = "$ref"

    def __init__(self, parentschema: JSONSchema, value: str):
        super().__init__(parentschema, value)
        self.refschema = None

    def resolve(self) -> None:
        uri = URI(self.json.data)
        if not uri.has_absolute_base():
            if (base_uri := self.parentschema.base_uri) is not None:
                uri = uri.resolve(base_uri)
            else:
                raise JSONSchemaError(f'No base URI against which to resolve the "$ref" value "{uri}"')

        self.refschema = self.parentschema.catalog.get_schema(
            uri, metaschema_uri=self.parentschema.metaschema_uri, cacheid=self.parentschema.cacheid
        )

    def evaluate(self, instance: JSON, result: Result) -> None:
        self.refschema.evaluate(instance, result)
        result.refschema(self.refschema)


class AnchorKeyword(Keyword):
    key = "$anchor"
    static = True

    def __init__(self, parentschema: JSONSchema, value: str):
        super().__init__(parentschema, value)

        if (base_uri := parentschema.base_uri) is not None:
            uri = URI(f'{base_uri}#{value}')
        else:
            raise JSONSchemaError(f'No base URI for "$anchor" value "{value}"')

        parentschema.catalog.add_schema(uri, parentschema, cacheid=parentschema.cacheid)


class DynamicRefKeyword(Keyword):
    key = "$dynamicRef"

    def __init__(self, parentschema: JSONSchema, value: str):
        super().__init__(parentschema, value)

        self.fragment = URI(value).fragment
        self.refschema = None
        self.dynamic = False

    def resolve(self) -> None:
        uri = URI(self.json.data)
        if not uri.has_absolute_base():
            if (base_uri := self.parentschema.base_uri) is not None:
                uri = uri.resolve(base_uri)
            else:
                raise JSONSchemaError(f'No base URI against which to resolve the "$dynamicRef" value "{uri}"')

        self.refschema = self.parentschema.catalog.get_schema(
            uri, metaschema_uri=self.parentschema.metaschema_uri, cacheid=self.parentschema.cacheid
        )
        if (dynamic_anchor := self.refschema.get("$dynamicAnchor")) and dynamic_anchor.data == self.fragment:
            self.dynamic = True

    def evaluate(self, instance: JSON, result: Result) -> None:
        refschema = self.refschema

        if self.dynamic:
            target = result
            checked_uris = set()

            while target is not None:
                if (base_uri := target.schema.base_uri) is not None and base_uri not in checked_uris:
                    checked_uris |= {base_uri}
                    target_uri = URI(f"#{self.fragment}").resolve(base_uri)
                    try:
                        found_schema = self.parentschema.catalog.get_schema(
                            target_uri, cacheid=self.parentschema.cacheid
                        )
                        if (dynamic_anchor := found_schema.get("$dynamicAnchor")) and \
                                dynamic_anchor.data == self.fragment:
                            refschema = found_schema
                    except CatalogError:
                        pass

                target = target.parent

        refschema.evaluate(instance, result)
        result.refschema(refschema)


class DynamicAnchorKeyword(Keyword):
    key = "$dynamicAnchor"
    static = True

    def __init__(self, parentschema: JSONSchema, value: str):
        super().__init__(parentschema, value)

        if (base_uri := parentschema.base_uri) is not None:
            uri = URI(f'{base_uri}#{value}')
        else:
            raise JSONSchemaError(f'No base URI for "$dynamicAnchor" value "{value}"')

        parentschema.catalog.add_schema(uri, parentschema, cacheid=parentschema.cacheid)


class DefsKeyword(Keyword, ObjectOfSubschemas):
    key = "$defs"
    static = True


class CommentKeyword(Keyword):
    key = "$comment"
    static = True
