from __future__ import annotations

from collections import deque
from contextlib import contextmanager
from functools import cached_property
from typing import Any, ContextManager, Dict, Hashable, Iterator, Mapping, Optional, TYPE_CHECKING, Type, Union
from uuid import uuid4

from jschon.exceptions import JSONSchemaError
from jschon.json import JSON, JSONCompatible
from jschon.jsonpointer import JSONPointer
from jschon.uri import URI

if TYPE_CHECKING:
    from jschon.catalog import Catalog
    from jschon.vocabulary import Keyword, KeywordClass, Metaschema

__all__ = [
    'JSONSchema',
    'Scope',
]


class JSONSchema(JSON):
    """JSON schema document model."""

    def __init__(
            self,
            value: Union[bool, Mapping[str, JSONCompatible]],
            *,
            catalog: Union[str, Catalog] = 'catalog',
            session: Hashable = 'default',
            uri: URI = None,
            metaschema_uri: URI = None,
            parent: JSON = None,
            key: str = None,
    ):
        """Initialize a :class:`JSONSchema` instance from the given
        schema-compatible `value`.

        :param value: a schema-compatible Python object
        :param catalog: the catalog in which the schema is cached
        :param session: a session identifier, identifying which session
            cache to put the schema in
        :param uri: the URI identifying the schema; an ``"$id"`` keyword
            appearing in `value` will override this
        :param metaschema_uri: the URI identifying the schema's metaschema;
            a ``"$schema"`` keyword appearing in `value` will override this
        :param parent: the parent node of the schema; used internally when
            creating a subschema
        :param key: the index of the schema within its parent; used internally
            when creating a subschema
        """
        from jschon.catalog import Catalog

        if not isinstance(catalog, Catalog):
            catalog = Catalog.get_catalog(catalog)

        self.catalog: Catalog = catalog
        """The catalog in which the schema is cached."""

        self.session: Hashable = session
        """A session identifier, identifying which session
        cache to use for the schema."""

        if uri is not None:
            catalog.add_schema(uri, self, session=session)

        self._uri: Optional[URI] = uri
        self._metaschema_uri: Optional[URI] = metaschema_uri

        self.keywords: Dict[str, Keyword] = {}
        """A dictionary of the schema's :class:`~jschon.vocabulary.Keyword`
        objects, indexed by keyword name."""

        # do not call super().__init__
        # all inherited attributes are initialized here:

        self.type: str
        """The JSON type of the schema. One of ``"boolean"``, ``"object"``."""

        self.data: Union[bool, Dict[str, JSON]]
        """The schema data.
        
        =========   ===============
        JSON type   data type
        =========   ===============
        boolean     bool
        object      dict[str, JSON]
        =========   ===============
        """

        self.parent: Optional[JSON] = parent
        """The containing :class:`~jschon.json.JSON` or :class:`JSONSchema` node."""

        self.key: Optional[str] = key
        """The index of the schema within its parent."""

        if isinstance(value, bool):
            self.type = "boolean"
            self.data = value

        elif isinstance(value, Mapping):
            self.type = "object"
            self.data = {}

            if self.parent is None and self.uri is None:
                self.uri = URI(f'urn:uuid:{uuid4()}')

            self._bootstrap(value)

            kwclasses = {
                key: kwclass for key in value
                if (key not in self.keywords and  # skip bootstrapped keywords
                    (kwclass := self.metaschema.kwclasses.get(key)))
            }

            for kwclass in self._resolve_dependencies(kwclasses):
                kw = kwclass(self, value[(key := kwclass.key)])
                self.keywords[key] = kw
                self.data[key] = kw.json

            if self.parent is None:
                self._resolve_references()

        else:
            raise TypeError(f"{value=} is not JSONSchema-compatible")

    def _bootstrap(self, value: Mapping[str, JSONCompatible]) -> None:
        from jschon.vocabulary.core import IdKeyword, SchemaKeyword, VocabularyKeyword
        boostrap_kwclasses = {
            "$id": IdKeyword,
            "$schema": SchemaKeyword,
            "$vocabulary": VocabularyKeyword,
        }
        for key, kwclass in boostrap_kwclasses.items():
            if key in value:
                kw = kwclass(self, value[key])
                self.keywords[key] = kw
                self.data[key] = kw.json

    def _resolve_references(self) -> None:
        for kw in self.keywords.values():
            if hasattr(kw, 'resolve'):
                kw.resolve()
            elif isinstance(kw.json, JSONSchema):
                kw.json._resolve_references()
            elif kw.json.type == "array":
                for item in kw.json:
                    if isinstance(item, JSONSchema):
                        item._resolve_references()
            elif kw.json.type == "object":
                for item in kw.json.values():
                    if isinstance(item, JSONSchema):
                        item._resolve_references()

    @staticmethod
    def _resolve_dependencies(kwclasses: Dict[str, KeywordClass]) -> Iterator[KeywordClass]:
        dependencies = {
            kwclass: [depclass for dep in kwclass.depends
                      if (depclass := kwclasses.get(dep))]
            for kwclass in kwclasses.values()
        }
        while dependencies:
            for kwclass, depclasses in dependencies.items():
                if not depclasses:
                    del dependencies[kwclass]
                    for deps in dependencies.values():
                        try:
                            deps.remove(kwclass)
                        except ValueError:
                            pass
                    yield kwclass
                    break

    def validate(self) -> Scope:
        """Validate the schema against its metaschema."""
        return self.metaschema.evaluate(self)

    def evaluate(self, instance: JSON, scope: Scope = None) -> Scope:
        """Evaluate a JSON document.
        
        The returned :class:`Scope` represents the complete evaluation
        result tree for this (sub)schema node.

        :param instance: the JSON document to evaluate
        :param scope: the dynamic evaluation scope; used by keywords
            when invoking this method recursively
        """
        if scope is None:
            scope = Scope(self, instance)

        if self.data is True:
            pass

        elif self.data is False:
            scope.fail("The instance is disallowed by a boolean false schema")

        else:
            for key, keyword in self.keywords.items():
                if not keyword.static and keyword.can_evaluate(instance):
                    with scope(instance, key, self) as subscope:
                        keyword.evaluate(instance, subscope)

            if any(
                    not child.passed
                    for child in scope.iter_children(instance)
            ):
                scope.fail()

        return scope

    @cached_property
    def parentschema(self) -> Optional[JSONSchema]:
        """The containing :class:`JSONSchema` instance.
        
        Note that this is not necessarily the same as `self.parent`.
        """
        parent = self.parent
        while parent is not None:
            if isinstance(parent, JSONSchema):
                return parent
            parent = parent.parent

    @property
    def metaschema(self) -> Metaschema:
        """The schema's :class:`~jschon.vocabulary.Metaschema`."""
        from jschon.vocabulary import Metaschema

        if (uri := self.metaschema_uri) is None:
            raise JSONSchemaError("The schema's metaschema URI has not been set")

        if not isinstance(
                metaschema := self.catalog.get_schema(uri, session='__meta__'),
                Metaschema,
        ):
            raise JSONSchemaError(f"The schema referenced by {uri} is not a metachema")

        return metaschema

    @property
    def metaschema_uri(self) -> Optional[URI]:
        """The :class:`~jschon.uri.URI` identifying the schema's metaschema.
        
        If not defined on this (sub)schema, the metaschema URI
        is determined by the parent schema.
        """
        if self._metaschema_uri is not None:
            return self._metaschema_uri
        if self.parentschema is not None:
            return self.parentschema.metaschema_uri

    @metaschema_uri.setter
    def metaschema_uri(self, value: Optional[URI]) -> None:
        self._metaschema_uri = value

    @property
    def base_uri(self) -> Optional[URI]:
        """The schema's base :class:`~jschon.uri.URI`.
        
        The base URI is obtained by searching up the schema tree
        for a schema URI, and removing any fragment.
        """
        if self._uri is not None:
            return self._uri.copy(fragment=False)
        if self.parentschema is not None:
            return self.parentschema.base_uri

    @property
    def uri(self) -> Optional[URI]:
        """The :class:`~jschon.uri.URI` identifying the schema.

        Used as the key for caching the schema in the catalog.
        """
        return self._uri

    @uri.setter
    def uri(self, value: Optional[URI]) -> None:
        if self._uri != value:
            if self._uri is not None:
                self.catalog.del_schema(self._uri, session=self.session)

            self._uri = value

            if self._uri is not None:
                self.catalog.add_schema(self._uri, self, session=self.session)

    @property
    def canonical_uri(self) -> Optional[URI]:
        """The absolute location of the (sub)schema.
        
        This is not necessarily an 'absolute URI', as it may contain
        a fragment.
        """
        if self._uri is not None:
            return self._uri

        keys = deque()
        node = self
        while node.parent is not None:
            keys.appendleft(node.key)
            node = node.parent

            if isinstance(node, JSONSchema) and node._uri is not None:
                if fragment := node._uri.fragment:
                    relpath = JSONPointer.parse_uri_fragment(fragment) / keys
                else:
                    relpath = JSONPointer(keys)

                return node._uri.copy(fragment=relpath.uri_fragment())


class Scope:
    def __init__(
            self,
            schema: JSONSchema,
            instance: JSON,
            *,
            parent: Scope = None,
            key: str = None,
    ):
        self.schema: JSONSchema = schema
        self.instance: JSON = instance
        self.parent: Optional[Scope] = parent
        self.key: Optional[str] = key
        self.children: Dict[JSONPointer, Dict[str, Scope]] = {}
        self.annotation: JSONCompatible = None
        self.error: Optional[str] = None
        self._valid = True
        self._assert = True
        self._discard = False
        self._refschema: Optional[JSONSchema] = None

        if parent is None:
            self.path = JSONPointer()
            self.relpath = JSONPointer()
            self._globals = {}
        else:
            self.path = parent.path / key
            self.relpath = parent.relpath / key if schema is parent.schema else JSONPointer((key,))
            self._globals = None

    @contextmanager
    def __call__(
            self,
            instance: JSON,
            key: str,
            schema: JSONSchema = None,
            *,
            cls: Type[Scope] = None,
    ) -> ContextManager[Scope]:
        """Yield a subscope of the current scope, for evaluating `instance`.
        Descend down the evaluation path by `key`, into `schema` if given, or
        within the schema of the current scope otherwise.

        Extension keywords may provide a custom Scope class via `cls`, which
        is applied to all nodes within the yielded subtree.
        """
        if schema is None:
            schema = self.schema

        self.children.setdefault(instance_path := instance.path, {})
        self.children[instance_path][key] = (child := (cls or self.__class__)(
            schema,
            instance,
            parent=self,
            key=key,
        ))

        try:
            yield child
        finally:
            if child._discard:
                del self.children[instance_path][key]

    @cached_property
    def globals(self) -> Dict:
        root = self
        while root.parent is not None:
            root = root.parent
        return root._globals

    @cached_property
    def schema_node(self) -> JSON:
        """Return the schema node associated with this scope."""
        return self.relpath.evaluate(self.schema)

    def sibling(self, instance: JSON, key: str) -> Optional[Scope]:
        try:
            return self.parent.children[instance.path][key] if self.parent else None
        except KeyError:
            return None

    def annotate(self, value: JSONCompatible) -> None:
        """Set an annotation on the scope."""
        self.annotation = value

    def fail(self, error: str = None) -> None:
        """Flag the scope as invalid, optionally with an error message."""
        self._valid = False
        self.error = error

    def pass_(self) -> None:
        """Flag the scope as valid.
        
        A scope is initially valid, so this should ordinarily only need
        to be called by a keyword when it must reverse a scope failure.
        """
        self._valid = True
        self.error = None

    def noassert(self) -> None:
        """Indicate that the scope's validity should not affect its
        assertion result."""
        self._assert = False

    def discard(self) -> None:
        """Indicate that the scope should be ignored and discarded."""
        self._discard = True

    def refschema(self, schema: JSONSchema) -> None:
        """Set the referenced schema for the scope of a by-reference keyword.
        
        The referenced schema's URI is then returned by :attr:`absolute_uri`,
        instead of calculating the absolute URI using the containing schema.
        """
        self._refschema = schema

    @property
    def valid(self) -> bool:
        """Return the validation result of the scope.

        :rtype: bool
        """
        return self._valid

    @property
    def passed(self) -> bool:
        """Return the assertion result of the scope.
        
        In the current implementation, this can only ever differ from
        :attr:`valid` for an "if" keyword subscope: its validation result
        may be false (triggering "else") while its assertion result is always
        true. For the root scope (representing the overall document evaluation
        result), :attr:`valid` will always equal :attr:`passed`.

        :rtype: bool
        """
        return self._valid or not self._assert

    @property
    def absolute_uri(self) -> Optional[URI]:
        if self._refschema is not None:
            return self._refschema.canonical_uri

        if (schema_uri := self.schema.canonical_uri) is not None:
            if fragment := schema_uri.fragment:
                relpath = JSONPointer.parse_uri_fragment(fragment) / self.relpath
            else:
                relpath = self.relpath
            return schema_uri.copy(fragment=relpath.uri_fragment())

    def iter_children(self, instance: JSON = None) -> Iterator[Scope]:
        """Return an iterator over child scopes of this scope, optionally
        filtered by an instance to which they apply."""
        for instance_path, keyword_scopes in self.children.items():
            if instance is None or instance.path == instance_path:
                yield from keyword_scopes.values()

    def collect_annotations(self, instance: JSON = None, key: str = None) -> Iterator[JSONCompatible]:
        """Return an iterator over annotations produced in this subtree,
        optionally filtered by instance and/or keyword."""
        if self._valid and not self._discard:
            if self.annotation is not None and \
                    (key is None or key == self.key) and \
                    (instance is None or instance.path == self.instance.path):
                yield self.annotation
            for child in self.iter_children():
                yield from child.collect_annotations(instance, key)

    def output(self, format: str, **kwargs: Any) -> JSONCompatible:
        """Return the evaluation result in the specified `format`.

        :param format: The format of the returned document. The default
            :class:`~jschon.output.JSONSchemaOutputFormatter` supports
            the ``flag``, ``basic``, ``detailed`` and ``verbose`` output
            formats, as defined by the JSON Schema specification.
        :param kwargs: Additional keyword arguments to pass to the output
            formatter.
        """
        return self.schema.catalog.output_formatter.create_output(self, format, **kwargs)

    def __str__(self) -> str:
        return str(self.path)
