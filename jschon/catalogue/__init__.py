import pathlib
from os import PathLike
from typing import Dict, Mapping, Any

from jschon.exceptions import CatalogueError, JSONPointerError
from jschon.json import AnyJSONCompatible
from jschon.jsonpointer import JSONPointer
from jschon.jsonschema import Metaschema, Vocabulary, KeywordClass, JSONSchema
from jschon.uri import URI
from jschon.utils import json_loadf
from jschon.vocabulary.format import FormatValidator

__all__ = [
    'Catalogue',
    'catalogue_dir',
]

catalogue_dir = pathlib.Path(__file__).parent


class Catalogue:
    _directories: Dict[URI, PathLike] = {}
    _vocabularies: Dict[URI, Vocabulary] = {}
    _format_validators: Dict[str, FormatValidator] = {}
    _schema_cache: Dict[URI, JSONSchema] = {}

    @classmethod
    def add_directory(cls, base_uri: URI, base_dir: PathLike) -> None:
        if not pathlib.Path(base_dir).is_dir():
            raise CatalogueError(f"'{base_dir}' is not a directory")

        cls._directories[base_uri] = base_dir

    @classmethod
    def load_json(cls, uri: URI) -> AnyJSONCompatible:
        uristr = str(uri)
        for base_uri, base_dir in cls._directories.items():
            if uristr.startswith(str(base_uri)):
                filepath = pathlib.Path(base_dir) / uristr[len(base_uri):]
                try:
                    return json_loadf(filepath)
                except FileNotFoundError:
                    return json_loadf(filepath.with_suffix('.json'))

        raise CatalogueError(f"File not found for '{uri}'")

    @classmethod
    def create_vocabulary(cls, uri: URI, *kwclasses: KeywordClass) -> None:
        cls._vocabularies[uri] = Vocabulary(uri, *kwclasses)

    @classmethod
    def get_vocabulary(cls, uri: URI) -> Vocabulary:
        try:
            return cls._vocabularies[uri]
        except KeyError:
            raise CatalogueError(f"Unrecognized vocabulary URI '{uri}'")

    @classmethod
    def create_metaschema(
            cls,
            metaschema_uri: URI,
            core_vocabulary_uri: URI,
            *default_vocabulary_uris: URI,
    ) -> None:
        metaschema_doc = cls.load_json(metaschema_uri)
        core_vocabulary = cls.get_vocabulary(core_vocabulary_uri)
        default_vocabularies = [cls.get_vocabulary(vocab_uri) for vocab_uri in default_vocabulary_uris]
        metaschema = Metaschema(metaschema_doc, core_vocabulary, *default_vocabularies)
        metaschema.validate()

    @classmethod
    def add_format_validators(cls, validators: Mapping[str, FormatValidator]) -> None:
        cls._format_validators.update(validators)

    @classmethod
    def get_format_validator(cls, format_attr: str) -> FormatValidator:
        try:
            return cls._format_validators[format_attr]
        except KeyError:
            raise CatalogueError(f"Unsupported format attribute '{format_attr}'")

    @classmethod
    def add_schema(cls, uri: URI, schema: JSONSchema) -> None:
        cls._schema_cache[uri] = schema

    @classmethod
    def del_schema(cls, uri: URI) -> None:
        cls._schema_cache.pop(uri, None)

    @classmethod
    def get_schema(cls, uri: URI, **kwargs: Any) -> JSONSchema:
        """Get a (sub)schema identified by uri from the cache, or load it
        from disk if not already cached.

        Additional kwargs are passed to the JSONSchema constructor for
        newly created instances.
        """
        try:
            return cls._schema_cache[uri]
        except KeyError:
            pass

        schema = None
        base_uri = uri.copy(fragment=False)

        if uri.fragment is not None:
            try:
                schema = cls._schema_cache[base_uri]
            except KeyError:
                pass

        if schema is None:
            doc = cls.load_json(base_uri)
            schema = JSONSchema(doc, uri=base_uri, **kwargs)

        if uri.fragment:
            try:
                ptr = JSONPointer.parse_uri_fragment(uri.fragment)
                schema = ptr.evaluate(schema)
            except JSONPointerError as e:
                raise CatalogueError(f"Schema not found for {uri}") from e

        if not isinstance(schema, JSONSchema):
            raise CatalogueError(f"The object referenced by {uri} is not a JSON Schema")

        return schema
