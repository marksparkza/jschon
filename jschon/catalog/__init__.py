from __future__ import annotations

import pathlib
import uuid
from contextlib import contextmanager
from os import PathLike
from typing import Any, ContextManager, Dict, Hashable, Mapping, Union

from jschon.exceptions import CatalogError, JSONPointerError, URIError
from jschon.json import JSONCompatible
from jschon.jsonpointer import JSONPointer
from jschon.jsonschema import JSONSchema
from jschon.output import JSONSchemaOutputFormatter, OutputFormatter
from jschon.uri import URI
from jschon.utils import json_loadf, json_loadr
from jschon.vocabulary import KeywordClass, Metaschema, Vocabulary
from jschon.vocabulary.format import FormatValidator

__all__ = [
    'Catalog',
    'Source',
    'LocalSource',
    'RemoteSource',
]


class Source:
    def __init__(self, suffix: str = None) -> None:
        self.suffix = suffix

    def __call__(self, relative_path: str) -> JSONCompatible:
        raise NotImplementedError


class LocalSource(Source):
    def __init__(self, base_dir: Union[str, PathLike], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.base_dir = base_dir

    def __call__(self, relative_path: str) -> JSONCompatible:
        filepath = pathlib.Path(self.base_dir) / relative_path
        if self.suffix:
            filepath = filepath.with_suffix(self.suffix)

        return json_loadf(filepath)


class RemoteSource(Source):
    def __init__(self, base_url: URI, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.base_url = base_url

    def __call__(self, relative_path: str) -> JSONCompatible:
        url = str(URI(relative_path).resolve(self.base_url))
        if self.suffix:
            url += self.suffix

        return json_loadr(url)


class Catalog:
    """The :class:`Catalog` acts as a schema cache, enabling schemas and subschemas
    to be indexed, re-used, and cross-referenced by URI. The cache is transparently
    partitioned by (arbitrary) session identifiers, which may optionally be provided
    when creating :class:`~jschon.jsonschema.JSONSchema` objects."""

    _catalog_registry: Dict[Hashable, Catalog] = {}

    @classmethod
    def get_catalog(cls, name: str = 'catalog') -> Catalog:
        try:
            return cls._catalog_registry[name]
        except KeyError:
            raise CatalogError(f'Catalog name "{name}" not found.')

    def __init__(self, name: str = 'catalog') -> None:
        """Initialize a :class:`Catalog` instance.

        :param name: a unique name for this :class:`Catalog` instance
        """
        self.__class__._catalog_registry[name] = self

        self.name: str = name
        """The unique name of this :class:`Catalog` instance."""

        self.output_formatter: OutputFormatter = JSONSchemaOutputFormatter()
        """A JSON Schema output formatter."""

        self._uri_sources: Dict[URI, Source] = {}
        self._vocabularies: Dict[URI, Vocabulary] = {}
        self._format_validators: Dict[str, FormatValidator] = {}
        self._schema_cache: Dict[Hashable, Dict[URI, JSONSchema]] = {}

    def add_uri_source(self, base_uri: URI, source: Source):
        """Register a source for URI-identified JSON resources.

        :param base_uri: a normalized, absolute URI - including scheme, without
            a fragment, and ending with ``'/'``
        :param source: a :class:`Source` object
        :raise CatalogError: if `base_uri` is invalid
        """
        try:
            base_uri.validate(require_scheme=True, require_normalized=True, allow_fragment=False)
        except URIError as e:
            raise CatalogError from e

        if not base_uri.path or not base_uri.path.endswith('/'):
            raise CatalogError('base_uri must end with "/"')

        self._uri_sources[base_uri] = source

    def load_json(self, uri: URI) -> JSONCompatible:
        """Load a JSON-compatible object from the source for `uri`.

        If there are multiple candidate base URIs for `uri`, the most specific
        match (i.e. the longest one) is selected.

        :param uri: a normalized, absolute URI - including scheme, without
            a fragment
        :raise CatalogError: if `uri` is invalid, a source is not available
            for `uri`, or if a loading error occurs
        """
        try:
            uri.validate(require_scheme=True, require_normalized=True, allow_fragment=False)
        except URIError as e:
            raise CatalogError from e

        uristr = str(uri)
        candidates = [
            (base_uristr, source)
            for base_uri, source in self._uri_sources.items()
            if uristr.startswith(base_uristr := str(base_uri))
        ]
        if candidates:
            candidates.sort(key=lambda c: len(c[0]), reverse=True)
            base_uristr, source = candidates[0]
            relative_path = uristr[len(base_uristr):]
            try:
                return source(relative_path)
            except Exception as e:
                raise CatalogError(*e.args) from e

        raise CatalogError(f'A source is not available for "{uri}"')

    def create_vocabulary(self, uri: URI, *kwclasses: KeywordClass) -> None:
        """Create a :class:`~jschon.vocabulary.Vocabulary` object, which
        may be used by a :class:`~jschon.vocabulary.Metaschema` to provide
        keyword classes used in schema construction.

        :param uri: the URI identifying the vocabulary
        :param kwclasses: the :class:`~jschon.vocabulary.Keyword` classes
            constituting the vocabulary
        """
        self._vocabularies[uri] = Vocabulary(uri, *kwclasses)

    def get_vocabulary(self, uri: URI) -> Vocabulary:
        """Get a :class:`~jschon.vocabulary.Vocabulary` by its `uri`.

        :param uri: the URI identifying the vocabulary
        :raise CatalogError: if `uri` is not a recognized vocabulary URI
        """
        try:
            return self._vocabularies[uri]
        except KeyError:
            raise CatalogError(f"Unrecognized vocabulary URI '{uri}'")

    def create_metaschema(
            self,
            uri: URI,
            core_vocabulary_uri: URI,
            *default_vocabulary_uris: URI,
            **kwargs: Any,
    ) -> None:
        """Create, cache and validate a :class:`~jschon.vocabulary.Metaschema`.

        :param uri: the URI identifying the metaschema
        :param core_vocabulary_uri: the URI identifying the metaschema's
            core :class:`~jschon.vocabulary.Vocabulary`
        :param default_vocabulary_uris: default :class:`~jschon.vocabulary.Vocabulary`
            URIs, used in the absence of a ``"$vocabulary"`` keyword in the
            metaschema JSON file
        :param kwargs: additional keyword arguments to pass through to the
            :class:`~jschon.jsonschema.JSONSchema` constructor
        """
        metaschema_doc = self.load_json(uri)
        core_vocabulary = self.get_vocabulary(core_vocabulary_uri)
        default_vocabularies = [
            self.get_vocabulary(vocab_uri)
            for vocab_uri in default_vocabulary_uris
        ]
        metaschema = Metaschema(
            self,
            metaschema_doc,
            core_vocabulary,
            *default_vocabularies,
            **kwargs,
            uri=uri,
        )
        if not metaschema.validate().valid:
            raise CatalogError("The metaschema is invalid against itself")

    def add_format_validators(self, validators: Mapping[str, FormatValidator]) -> None:
        """Register a collection of format validators.
        
        In jschon, a given occurrence of the ``"format"`` keyword evaluates
        a JSON instance using a format validation callable, if one has been
        registered for the applicable *format attribute* (the keyword's value).
        If a validator has not been registered for that format attribute,
        keyword evaluation simply passes.

        :param validators: a dictionary of :class:`~jschon.vocabulary.format.FormatValidator`
            callables, keyed by format attribute
        """
        self._format_validators.update(validators)

    def get_format_validator(self, format_attr: str) -> FormatValidator:
        """Get a registered :class:`~jschon.vocabulary.format.FormatValidator`
        function.

        :param format_attr: the format attribute (``"format"`` keyword value)
            to which the validator applies
        :raise CatalogError: if no format validator is registered for the
            given `format_attr`
        """
        try:
            return self._format_validators[format_attr]
        except KeyError:
            raise CatalogError(f"Unsupported format attribute '{format_attr}'")

    def add_schema(
            self,
            uri: URI,
            schema: JSONSchema,
            *,
            session: Hashable = 'default',
    ) -> None:
        """Add a (sub)schema to a session cache.

        :param uri: the URI identifying the (sub)schema
        :param schema: the :class:`~jschon.jsonschema.JSONSchema` instance to cache
        :param session: a session identifier
        """
        self._schema_cache.setdefault(session, {})
        self._schema_cache[session][uri] = schema

    def del_schema(
            self,
            uri: URI,
            *,
            session: Hashable = 'default',
    ) -> None:
        """Remove a (sub)schema from a session cache.

        :param uri: the URI identifying the (sub)schema
        :param session: a session identifier
        """
        if session in self._schema_cache:
            self._schema_cache[session].pop(uri, None)

    def get_schema(
            self,
            uri: URI,
            *,
            metaschema_uri: URI = None,
            session: Hashable = 'default',
    ) -> JSONSchema:
        """Get a (sub)schema identified by `uri` from a session cache, or
        load it from disk if not already cached.

        :param uri: the URI identifying the (sub)schema
        :param metaschema_uri: passed to the :class:`~jschon.jsonschema.JSONSchema`
            constructor when loading a new instance from disk
        :param session: a session identifier
        :raise CatalogError: if a schema cannot be found for `uri`, or if the
            object referenced by `uri` is not a :class:`~jschon.jsonschema.JSONSchema`
        """
        try_caches = ('__meta__',) \
            if session == '__meta__' \
            else (session, '__meta__')

        for cacheid in try_caches:
            try:
                return self._schema_cache[cacheid][uri]
            except KeyError:
                pass

        schema = None
        base_uri = uri.copy(fragment=False)

        if uri.fragment is not None:
            for cacheid in try_caches:
                try:
                    schema = self._schema_cache[cacheid][base_uri]
                    break
                except KeyError:
                    pass

        if schema is None:
            doc = self.load_json(base_uri)
            schema = JSONSchema(
                doc,
                catalog=self,
                session=session,
                uri=base_uri,
                metaschema_uri=metaschema_uri,
            )

        if uri.fragment:
            try:
                ptr = JSONPointer.parse_uri_fragment(uri.fragment)
                schema = ptr.evaluate(schema)
            except JSONPointerError as e:
                raise CatalogError(f"Schema not found for {uri}") from e

        if not isinstance(schema, JSONSchema):
            raise CatalogError(f"The object referenced by {uri} is not a JSON Schema")

        return schema

    @contextmanager
    def session(self, session: Hashable = None) -> ContextManager[Hashable]:
        if session is None:
            session = uuid.uuid4()

        if session in self._schema_cache:
            raise CatalogError("session is already in use")

        try:
            yield session
        finally:
            self._schema_cache.pop(session, None)
