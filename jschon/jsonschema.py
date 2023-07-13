from __future__ import annotations

from collections import deque
from contextlib import contextmanager
from functools import cached_property
from typing import Any, ContextManager, Dict, Hashable, Iterator, Mapping, Optional, TYPE_CHECKING, Tuple, Type, Union
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
    'Result',
]


class JSONSchema(JSON):
    """JSON schema document model."""

    def __init__(
            self,
            value: Union[bool, Mapping[str, JSONCompatible]],
            *,
            catalog: Union[str, Catalog] = 'catalog',
            cacheid: Hashable = 'default',
            uri: URI = None,
            metaschema_uri: URI = None,
            parent: JSON = None,
            key: str = None,
    ):
        """Initialize a :class:`JSONSchema` instance from the given
        schema-compatible `value`.

        :param value: a schema-compatible Python object
        :param catalog: catalog instance or catalog name
        :param cacheid: schema cache identifier
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

        self.cacheid: Hashable = cacheid
        """Schema cache identifier."""

        if uri is not None:
            catalog.add_schema(uri, self, cacheid=cacheid)

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
                    (kwclass := self.metaschema.get_kwclass(key)))
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
        from jschon.vocabulary.core import SchemaKeyword, VocabularyKeyword

        boostrap_kwclasses = {
            "$schema": SchemaKeyword,
            "$vocabulary": VocabularyKeyword,
        }
        for key, kwclass in boostrap_kwclasses.items():
            if key in value:
                kw = kwclass(self, value[key])
                self.keywords[key] = kw
                self.data[key] = kw.json

        if "$id" in value:
            if str(self.metaschema.core_vocabulary.uri) in (
                "https://json-schema.org/draft/2019-09/vocab/core",
                "https://json-schema.org/draft/2020-12/vocab/core",
            ):
                from jschon.vocabulary.core import IdKeyword
            else:
                from jschon.vocabulary.future import IdKeyword_Next as IdKeyword

            id_kw = IdKeyword(self, value["$id"])
            self.keywords["$id"] = id_kw
            self.data["$id"] = id_kw.json

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
            kwclass: [depclass for dep in kwclass.depends_on
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

    def validate(self) -> Result:
        """Validate the schema against its metaschema."""
        return self.metaschema.evaluate(self)

    def evaluate(self, instance: JSON, result: Result = None) -> Result:
        """Evaluate a JSON document and return the evaluation result.

        :param instance: the JSON document to evaluate
        :param result: the current result node; given by keywords
            when invoking this method recursively
        """
        if result is None:
            result = Result(self, instance)

        if self.data is True:
            pass

        elif self.data is False:
            result.fail("The instance is disallowed by a boolean false schema")

        else:
            for key, keyword in self.keywords.items():
                if not keyword.static and instance.type in keyword.instance_types:
                    with result(instance, key, self) as subresult:
                        keyword.evaluate(instance, subresult)

            if any(
                    not child.passed
                    for child in result.children.values()
                    if child.instance.path == instance.path
            ):
                result.fail()

        return result

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

    @cached_property
    def resource_rootschema(self) -> JSONSchema:
        """The :class:`JSONSchema` at the root of the containing resource.

        This is the nearest ancestor (including `self`) containing ``"$id"``,
        or if none exist, it is the same as `self.document_rootschema`.
        """
        if '$id' in self.keywords:
            return self
        ancestor = self
        while ancestor.parentschema:
            ancestor = ancestor.parentschema
            if '$id' in ancestor.keywords:
                return ancestor
        return ancestor

    @cached_property
    def document_rootschema(self) -> JSONSchema:
        """The :class:`JSONSchema` at the root of the entire document.

        If no ancestor schemas contain ``"$id"``, this is the same as
        `self.resource_rootschema`.  If this schema has no `self.parentschema`,
        this method returns `self`.
        """
        ancestor = self
        while ancestor.parentschema:
            ancestor = ancestor.parentschema
        return ancestor

    @cached_property
    def metaschema(self) -> Metaschema:
        """The schema's :class:`~jschon.vocabulary.Metaschema`."""
        if (uri := self.metaschema_uri) is None:
            raise JSONSchemaError("The schema's metaschema URI has not been set")

        return self.catalog.get_metaschema(uri)

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
                self.catalog.del_schema(self._uri, cacheid=self.cacheid)

            self._uri = value

            if self._uri is not None:
                self.catalog.add_schema(self._uri, self, cacheid=self.cacheid)

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


class Result:
    """The result of evaluating a JSON document
    node against a JSON schema node.

    The root of a :class:`Result` tree represents
    a complete document evaluation result.
    """

    def __init__(
            self,
            schema: JSONSchema,
            instance: JSON,
            *,
            parent: Result = None,
            key: str = None,
    ) -> None:
        self.path: JSONPointer
        """The dynamic evaluation path to the current schema node."""

        self.relpath: JSONPointer
        """The path to the current schema node relative to the evaluating (sub)schema."""

        self.schema: JSONSchema = schema
        """The evaluating (sub)schema."""

        self.instance: JSON = instance
        """The instance under evaluation."""

        self.parent: Optional[Result] = parent
        """The parent result node."""

        self.key: Optional[str] = key
        """The index of the current schema node within its dynamic parent."""

        self.children: Dict[Tuple[str, JSONPointer], Result] = {}
        """Subresults of the current result node, indexed by schema key and instance path."""

        self.annotation: JSONCompatible = None
        """The annotation value of the result."""

        self.error: JSONCompatible = None
        """The error value of the result."""

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
            cls: Type[Result] = None,
    ) -> ContextManager[Result]:
        """Yield a subresult for the evaluation of `instance`.
        Descend down the evaluation path by `key`, into `schema` if given, or
        within `self.schema` otherwise.

        Extension keywords may provide a custom :class:`Result` class via `cls`,
        which is applied to all nodes within the yielded subtree.
        """
        if schema is None:
            schema = self.schema

        self.children[key, instance.path] = (child := (cls or self.__class__)(
            schema,
            instance,
            parent=self,
            key=key,
        ))

        try:
            yield child
        finally:
            if child._discard:
                del self.children[key, instance.path]

    @cached_property
    def globals(self) -> Dict:
        root = self
        while root.parent is not None:
            root = root.parent
        return root._globals

    @cached_property
    def schema_node(self) -> JSON:
        """Return the current schema node."""
        return self.relpath.evaluate(self.schema)

    def sibling(self, instance: JSON, key: str) -> Optional[Result]:
        """Return a sibling schema node's evaluation result for `instance`."""
        try:
            return self.parent.children[key, instance.path] if self.parent else None
        except KeyError:
            return None

    def annotate(self, value: JSONCompatible) -> None:
        """Annotate the result."""
        self.annotation = value

    def fail(self, error: JSONCompatible = None) -> None:
        """Mark the result as invalid, optionally with an error."""
        self._valid = False
        self.error = error

    def pass_(self) -> None:
        """Mark the result as valid.
        
        A result is initially valid, so this should only need
        to be called by a keyword when it must reverse a failure.
        """
        self._valid = True
        self.error = None

    def noassert(self) -> None:
        """Indicate that evaluation passes regardless of validity."""
        self._assert = False

    def discard(self) -> None:
        """Indicate that the result should be ignored and discarded."""
        self._discard = True

    def refschema(self, schema: JSONSchema) -> None:
        """Set the referenced schema for a by-reference keyword.
        
        This ensures that :attr:`absolute_uri` returns the URI of the
        referenced schema rather than the referencing keyword.
        """
        self._refschema = schema

    @property
    def valid(self) -> bool:
        """Return the validity of the instance against the schema."""
        return self._valid

    @property
    def passed(self) -> bool:
        """Return the assertion result for the schema node.

        In the standard JSON Schema vocabulary, this can only differ
        from :attr:`valid` for the ``if`` keyword: validity may be false
        (triggering ``else``) while its assertion result is always true.

        For the root result node, :attr:`passed` will always equal :attr:`valid`.
        """
        return self._valid or not self._assert

    @property
    def absolute_uri(self) -> Optional[URI]:
        """Return the absolute URI of the current schema node."""
        if self._refschema is not None:
            return self._refschema.canonical_uri

        if (schema_uri := self.schema.canonical_uri) is not None:
            if fragment := schema_uri.fragment:
                relpath = JSONPointer.parse_uri_fragment(fragment) / self.relpath
            else:
                relpath = self.relpath
            return schema_uri.copy(fragment=relpath.uri_fragment())

    def collect_annotations(self, instance: JSON = None, key: str = None) -> Iterator[JSONCompatible]:
        """Return an iterator over annotations produced in this subtree,
        optionally filtered by instance and/or keyword."""
        if self._valid and not self._discard:
            if self.annotation is not None and \
                    (key is None or key == self.key) and \
                    (instance is None or instance.path == self.instance.path):
                yield self.annotation
            for child in self.children.values():
                yield from child.collect_annotations(instance, key)

    def collect_errors(self, instance: JSON = None, key: str = None) -> Iterator[JSONCompatible]:
        """Return an iterator over errors produced in this subtree,
        optionally filtered by instance and/or keyword."""
        if not self._valid and not self._discard:
            if self.error is not None and \
                    (key is None or key == self.key) and \
                    (instance is None or instance.path == self.instance.path):
                yield self.error
            for child in self.children.values():
                yield from child.collect_errors(instance, key)

    def output(self, format: str, **kwargs: Any) -> JSONCompatible:
        """Return the evaluation result in the specified `format`.

        :param format: One of the standard JSON Schema output formats --
            ``flag``, ``basic``, ``detailed`` or ``verbose`` -- or any
            format registered with the :func:`~jschon.output.output_formatter`
            decorator.
        :param kwargs: Keyword arguments to pass to the output formatter.
        """
        from jschon.output import create_output
        return create_output(self, format, **kwargs)

    def __str__(self) -> str:
        s = 'valid' if self.valid else 'invalid'
        if self.parent:
            s = f'{self.path}: {s}'
        return s
