import pathlib
from os import PathLike
from typing import Dict, Mapping, Union

from jschon.catalogue import _2019_09, _2020_12
from jschon.exceptions import CatalogueError, JSONPointerError, URIError
from jschon.json import AnyJSONCompatible
from jschon.jsonpointer import JSONPointer
from jschon.jsonschema import Metaschema, Vocabulary, KeywordClass, JSONSchema
from jschon.uri import URI
from jschon.utils import json_loadf
from jschon.vocabulary.format import FormatValidator

__all__ = [
    'Catalogue',
]


class Catalogue:
    """The catalogue is the largest organizational unit in jschon.

    A catalogue is an in-memory schema cache, usually initialized with a
    collection of metaschemas and associated vocabularies, and any number of
    format validation functions. It may be configured with base URI-to-directory
    mappings, so that JSON files (including the metaschema definition files)
    may be loaded from disk.
    """
    _version_initializers = {
        '2019-09': _2019_09.initialize,
        '2020-12': _2020_12.initialize,
    }

    def __init__(self, *versions: str):
        """Create a new catalogue, optionally initialized with the metaschema
        of one or more supported versions of the JSON Schema specification.
        
        Supported versions: '2019-09', '2020-12'
        """
        self._directories: Dict[URI, PathLike] = {}
        self._vocabularies: Dict[URI, Vocabulary] = {}
        self._format_validators: Dict[str, FormatValidator] = {}
        self._schema_cache: Dict[URI, JSONSchema] = {}
        try:
            initializers = [self._version_initializers[version] for version in versions]
        except KeyError as e:
            raise CatalogueError(f'Unrecognized version "{e.args[0]}"')

        for initializer in initializers:
            initializer(self)

    def add_directory(self, base_uri: URI, base_dir: PathLike) -> None:
        """Register a base URI-to-directory mapping.
        
        This enables JSON objects identified by URIs with a given base URI
        to be loaded from files within a corresponding directory hierarchy,
        as described under ``load_json``.
        """
        try:
            base_uri.validate(require_scheme=True, require_normalized=True, allow_fragment=False)
        except URIError as e:
            raise CatalogueError from e

        if not base_uri.path or not base_uri.path.endswith('/'):
            raise CatalogueError("base_uri must end with '/'")

        if not pathlib.Path(base_dir).is_dir():
            raise CatalogueError(f"'{base_dir}' is not a directory")

        self._directories[base_uri] = base_dir

    def load_json(self, uri: URI) -> AnyJSONCompatible:
        """Load a JSON-compatible object from the file corresponding to uri.
        
        The file path is determined by selecting the most specific matching
        base URI registered with ``add_directory`` and 'resolving' the URI
        against the corresponding base directory.
        """
        try:
            uri.validate(require_scheme=True, require_normalized=True, allow_fragment=False)
        except URIError as e:
            raise CatalogueError from e

        uristr = str(uri)
        candidates = [
            (base_uristr, base_dir)
            for base_uri, base_dir in self._directories.items()
            if uristr.startswith(base_uristr := str(base_uri))
        ]
        if candidates:
            # if there is more than one candidate base URI, we consider
            # only the longest one to be a match: it represents a mount
            # of a directory at a sub-path of a parent candidate, and
            # we shouldn't fall back to trying to find the file in the
            # parent's directory hierarchy
            candidates.sort(key=lambda c: len(c[0]), reverse=True)
            base_uristr, base_dir = candidates[0]
            filepath = pathlib.Path(base_dir) / uristr[len(base_uristr):]
            try:
                return json_loadf(filepath)
            except FileNotFoundError:
                pass
            try:
                return json_loadf(filepath.with_suffix('.json'))
            except FileNotFoundError:
                pass

        raise CatalogueError(f"File not found for '{uri}'")

    def create_vocabulary(self, uri: URI, *kwclasses: KeywordClass) -> None:
        self._vocabularies[uri] = Vocabulary(uri, *kwclasses)

    def get_vocabulary(self, uri: URI) -> Vocabulary:
        try:
            return self._vocabularies[uri]
        except KeyError:
            raise CatalogueError(f"Unrecognized vocabulary URI '{uri}'")

    def create_metaschema(
            self,
            metaschema_uri: URI,
            core_vocabulary_uri: URI,
            *default_vocabulary_uris: URI,
    ) -> None:
        metaschema_doc = self.load_json(metaschema_uri)
        core_vocabulary = self.get_vocabulary(core_vocabulary_uri)
        default_vocabularies = [self.get_vocabulary(vocab_uri) for vocab_uri in default_vocabulary_uris]
        metaschema = Metaschema(self, metaschema_doc, core_vocabulary, *default_vocabularies)
        metaschema.validate()

    def add_format_validators(self, validators: Mapping[str, FormatValidator]) -> None:
        self._format_validators.update(validators)

    def get_format_validator(self, format_attr: str) -> FormatValidator:
        try:
            return self._format_validators[format_attr]
        except KeyError:
            raise CatalogueError(f"Unsupported format attribute '{format_attr}'")

    def create_schema(
            self,
            value: Union[bool, Mapping[str, AnyJSONCompatible]],
            *,
            uri: URI = None,
            metaschema_uri: URI = None,
    ) -> JSONSchema:
        return JSONSchema(value, catalogue=self, uri=uri, metaschema_uri=metaschema_uri)

    def add_schema(self, uri: URI, schema: JSONSchema) -> None:
        self._schema_cache[uri] = schema

    def del_schema(self, uri: URI) -> None:
        self._schema_cache.pop(uri, None)

    def get_schema(self, uri: URI, *, metaschema_uri: URI = None) -> JSONSchema:
        """Get a (sub)schema identified by uri from the cache, or load it
        from disk if not already cached.

        metaschema_uri is passed to the JSONSchema constructor when loading
        a new instance from disk.
        """
        try:
            return self._schema_cache[uri]
        except KeyError:
            pass

        schema = None
        base_uri = uri.copy(fragment=False)

        if uri.fragment is not None:
            try:
                schema = self._schema_cache[base_uri]
            except KeyError:
                pass

        if schema is None:
            doc = self.load_json(base_uri)
            schema = self.create_schema(doc, uri=base_uri, metaschema_uri=metaschema_uri)

        if uri.fragment:
            try:
                ptr = JSONPointer.parse_uri_fragment(uri.fragment)
                schema = ptr.evaluate(schema)
            except JSONPointerError as e:
                raise CatalogueError(f"Schema not found for {uri}") from e

        if not isinstance(schema, JSONSchema):
            raise CatalogueError(f"The object referenced by {uri} is not a JSON Schema")

        return schema
