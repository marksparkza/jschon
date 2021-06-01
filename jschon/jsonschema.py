from __future__ import annotations

from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from typing import (
    Mapping,
    Union,
    Optional,
    Dict,
    List,
    Iterator,
    ContextManager,
    TYPE_CHECKING,
)
from uuid import uuid4

from jschon.exceptions import JSONSchemaError
from jschon.json import JSON, AnyJSONCompatible
from jschon.jsonpointer import JSONPointer
from jschon.uri import URI
from jschon.utils import tuplify

if TYPE_CHECKING:
    from jschon.catalogue import Catalogue
    from jschon.vocabulary import Keyword, KeywordClass, Metaschema

__all__ = [
    'JSONSchema',
    'Scope',
    'Annotation',
    'Error',
    'OutputFormat',
]


class JSONSchema(JSON):
    """JSON schema document model."""

    def __init__(
            self,
            value: Union[bool, Mapping[str, AnyJSONCompatible]],
            *,
            catalogue: Catalogue = None,
            uri: URI = None,
            metaschema_uri: URI = None,
            parent: JSON = None,
            key: str = None,
    ):
        """Initialize a :class:`JSONSchema` instance from the given
        schema-compatible `value`.

        :param value: a schema-compatible Python object
        :param catalogue: the catalogue in which the schema will find its
            metaschema, and in which it will be cached; if not given, the
            default :class:`~jschon.catalogue.Catalogue` instance (created
            with :meth:`~jschon.catalogue.Catalogue.create_default_catalogue`)
            is used
        :param uri: the URI identifying the schema; an ``"$id"`` keyword
            appearing in `value` will override this
        :param metaschema_uri: the URI identifying the schema's metaschema;
            a ``"$schema"`` keyword appearing in `value` will override this
        :param parent: the parent node of the schema; used internally when
            creating a subschema
        :param key: the index of the schema within its parent; used internally
            when creating a subschema
        """
        from jschon.catalogue import Catalogue

        if catalogue is None:
            if (catalogue := Catalogue.get_default_catalogue()) is None:
                raise JSONSchemaError("catalogue not given and default catalogue not found")

        if uri is not None:
            catalogue.add_schema(uri, self)

        self.catalogue: Catalogue = catalogue
        """The catalogue in which the schema is cached."""

        self._uri: Optional[URI] = uri
        self._metaschema_uri: Optional[URI] = metaschema_uri

        self.keywords: Dict[str, Keyword] = {}
        """A dictionary of the schema's :class:`~jschon.vocabulary.Keyword`
        objects, indexed by keyword name."""

        # do not call super().__init__
        # all inherited attributes are initialized here:

        self.value: Union[bool, Mapping[str, JSON]]
        """The schema data.
        
        =========   ===============
        JSON type   value type
        =========   ===============
        boolean     bool
        object      dict[str, JSON]
        =========   ===============
        """

        self.type: str
        """The JSON type of the schema. One of ``"boolean"``, ``"object"``."""

        self.parent: Optional[JSON] = parent
        """The containing :class:`~jschon.json.JSON` or :class:`JSONSchema` node."""

        self.key: Optional[str] = key
        """The index of the schema within its parent."""

        if isinstance(value, bool):
            self.type = "boolean"
            self.value = value

        elif isinstance(value, Mapping) and all(isinstance(k, str) for k in value):
            self.type = "object"
            self.value = {}

            if self.parent is None and self.uri is None:
                self.uri = URI(f'urn:uuid:{uuid4()}')

            self._bootstrap(value)

            kwclasses = {
                key: kwclass for key in value
                if ((kwclass := self.metaschema.kwclasses.get(key)) and
                    # skip bootstrapped keywords
                    key not in self.keywords)
            }

            for kwclass in self._resolve_dependencies(kwclasses):
                kw = kwclass(self, value[(key := kwclass.key)])
                self.keywords[key] = kw
                self.value[key] = kw.json

            if self.parent is None:
                self._resolve_references()

        else:
            raise TypeError(f"{value=} is not JSONSchema-compatible")

    def _bootstrap(self, value: Mapping[str, AnyJSONCompatible]) -> None:
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
                self.value[key] = kw.json

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
            kwclass: [depclass for dep in tuplify(kwclass.depends)
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

    def validate(self) -> JSONSchema:
        """Validate the schema against its metaschema.
        
        This method returns `self`, so that schema instantiation and validation
        may be chained.

        :raise JSONSchemaError: if the schema is invalid against its metaschema
        """
        if not self.metaschema.evaluate(JSON(self.value)).valid:
            raise JSONSchemaError(f"The schema is invalid against its metaschema")

        return self

    def evaluate(self, instance: JSON, scope: Scope = None) -> Scope:
        """Evaluate a JSON document.
        
        The returned :class:`Scope` represents the complete evaluation
        result tree for this (sub)schema node.

        :param instance: the JSON document to evaluate
        :param scope: the dynamic evaluation scope; used by keywords
            when invoking this method recursively
        """
        if scope is None:
            scope = Scope(self)

        if self.value is True:
            pass

        elif self.value is False:
            scope.fail(instance, "The instance is disallowed by a boolean false schema")

        else:
            for key, keyword in self.keywords.items():
                if keyword.can_evaluate(instance):
                    with scope(instance, key, self) as subscope:
                        keyword.evaluate(instance, subscope)

            if any(
                    not child.valid
                    for child in scope.iter_children(instance)
            ):
                scope.fail(instance, "The instance failed validation against the schema")

        return scope

    @property
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

        if not isinstance(metaschema := self.catalogue.get_schema(uri), Metaschema):
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

        Used as the key for caching the schema in the catalogue.
        """
        return self._uri

    @uri.setter
    def uri(self, value: Optional[URI]) -> None:
        if self._uri != value:
            if self._uri is not None:
                self.catalogue.del_schema(self._uri)

            self._uri = value

            if self._uri is not None:
                self.catalogue.add_schema(self._uri, self)

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
            *,
            path: JSONPointer = None,
            relpath: JSONPointer = None,
            parent: Scope = None,
    ):
        self.schema: JSONSchema = schema
        self.path: JSONPointer = path or JSONPointer()
        self.relpath: JSONPointer = relpath or JSONPointer()
        self.parent: Optional[Scope] = parent
        self.children: Dict[JSONPointer, Dict[str, Scope]] = {}
        self.annotations: Dict[str, Annotation] = {}
        self.errors: List[Error] = []
        self._assert = True
        self._discard = False

    @contextmanager
    def __call__(self, instance: JSON, key: str, schema: JSONSchema = None) -> ContextManager[Scope]:
        """Yield a subscope of the current scope, for evaluating `instance`.
        Descend down the evaluation path by `key`, into `schema` if given, or
        within the schema of the current scope otherwise."""
        path = self.path / key
        schema = schema or self.schema
        if schema is self.schema:
            relpath = self.relpath / key
        else:
            relpath = JSONPointer((key,))

        self.children.setdefault(instance_path := instance.path, {})
        self.children[instance_path][key] = (child := Scope(
            schema,
            path=path,
            relpath=relpath,
            parent=self,
        ))

        try:
            yield child
        finally:
            if child._discard:
                del self.children[instance_path][key]

    def sibling(self, instance: JSON, key: str) -> Optional[Scope]:
        try:
            return self.parent.children[instance.path][key] if self.parent else None
        except KeyError:
            return None

    def annotate(self, instance: JSON, key: str, value: AnyJSONCompatible) -> None:
        if value is not None:
            self.annotations[key] = Annotation(
                instance_path=instance.path,
                evaluation_path=self.path,
                absolute_uri=self.absolute_uri,
                value=value,
            )

    def fail(self, instance: JSON, error: str) -> None:
        self.errors += [Error(
            instance_path=instance.path,
            evaluation_path=self.path,
            absolute_uri=self.absolute_uri,
            message=error,
        )]

    def noassert(self) -> None:
        """Indicate that the scope should be taken to be valid,
        regardless of errors."""
        self._assert = False

    def discard(self) -> None:
        """Indicate that the scope should be ignored and discarded."""
        self._discard = True

    @property
    def valid(self) -> bool:
        return not self._assert or not self.errors

    @property
    def absolute_uri(self) -> Optional[URI]:
        if (schema_uri := self.schema.canonical_uri) is not None:
            if fragment := schema_uri.fragment:
                relpath = JSONPointer.parse_uri_fragment(fragment) / self.relpath
            else:
                relpath = self.relpath
            return schema_uri.copy(fragment=relpath.uri_fragment())

    def iter_children(self, instance: JSON = None) -> Iterator[Scope]:
        """Return a flattened view of child scopes, optionally filtered
        by the instance to which they apply."""
        for instance_path, keyword_scopes in self.children.items():
            if instance is None or instance.path == instance_path:
                yield from keyword_scopes.values()

    def collect_annotations(self, instance: JSON = None, key: str = None) -> Iterator[Annotation]:
        """Return an iterator over annotations produced in this subtree,
        optionally filtered by instance and/or keyword."""
        if not self._discard and not self.errors:
            for annotation_key, annotation in self.annotations.items():
                if (key is None or key == annotation_key) and \
                        (instance is None or instance.path == annotation.instance_path):
                    yield annotation
            for child in self.iter_children():
                yield from child.collect_annotations(instance, key)

    def collect_errors(self) -> Iterator[Error]:
        """Return an iterator over errors produced in this subtree."""
        if not self._discard and self._assert and self.errors:
            yield from self.errors
            for child in self.iter_children():
                yield from child.collect_errors()

    def output(self, format: OutputFormat) -> Dict[str, AnyJSONCompatible]:
        """Return an output dictionary formatted in accordance with the
        JSON Schema specification of the given output `format`."""
        from jschon.output import OutputFormatter

        if format == OutputFormat.FLAG:
            return OutputFormatter.flag(self)

        if format == OutputFormat.BASIC:
            return OutputFormatter.basic(self)

        raise NotImplementedError

    def __str__(self) -> str:
        return str(self.path)


@dataclass
class Annotation:
    instance_path: JSONPointer
    evaluation_path: JSONPointer
    absolute_uri: URI
    value: AnyJSONCompatible


@dataclass
class Error:
    instance_path: JSONPointer
    evaluation_path: JSONPointer
    absolute_uri: URI
    message: str


class OutputFormat(str, Enum):
    FLAG = 'flag'
    BASIC = 'basic'
    DETAILED = 'detailed'
    VERBOSE = 'verbose'
