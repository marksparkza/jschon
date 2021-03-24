from __future__ import annotations

from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass
from typing import *
from uuid import uuid4

from jschon.exceptions import *
from jschon.json import *
from jschon.jsonpointer import JSONPointer
from jschon.uri import URI
from jschon.utils import tuplify

__all__ = [
    'JSONSchema',
    'Metaschema',
    'Vocabulary',
    'KeywordDef',
    'Keyword',
    'Applicator',
    'ArrayApplicator',
    'PropertyApplicator',
    'Annotation',
    'Error',
    'Scope',
]


class JSONSchema(JSON):

    @staticmethod
    def iscompatible(value: Any) -> bool:
        return isinstance(value, bool) or \
               isinstance(value, Mapping) and all(isinstance(k, str) for k in value)

    def __init__(
            self,
            value: Union[bool, Mapping[str, AnyJSONCompatible]],
            *,
            uri: URI = None,
            metaschema_uri: URI = None,
            parent: JSON = None,
            key: str = None,
    ):
        from jschon.catalogue import Catalogue
        if uri is not None:
            Catalogue.add_schema(uri, self)

        self._uri: Optional[URI] = uri
        self._metaschema_uri: Optional[URI] = metaschema_uri
        self.keywords: Dict[str, Keyword] = {}

        # don't call super().__init__
        self.value: Union[bool, Mapping[str, AnyJSONCompatible]]
        self.type: str
        self.parent: Optional[JSON] = parent
        self.key: Optional[str] = key

        if isinstance(value, bool):
            self.type = "boolean"
            self.value = value

        elif isinstance(value, Mapping) and all(isinstance(k, str) for k in value):
            self.type = "object"
            self.value = {}

            if self.parent is None and self.uri is None:
                self.uri = URI(f'mem:{uuid4()}')

            self._bootstrap(value)

            kwdefs = {
                key: kwdef for key in value
                if ((kwdef := self.metaschema.kwdefs.get(key)) and
                    # skip bootstrapped keywords
                    key not in self.keywords)
            }

            for kwdef in self._resolve_dependencies(kwdefs):
                kw = kwdef.kwclass(self, kwdef.key, value[kwdef.key], *tuplify(kwdef.instance_types))
                self.keywords[kwdef.key] = kw
                self.value[kwdef.key] = kw.json

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
                kw = kwclass(self, key, value[key], ())
                self.keywords[key] = kw
                self.value[key] = kw.json

    def _resolve_references(self) -> None:
        if ref_kw := self.keywords.get("$ref"):
            ref_kw.resolve()

        for kw in self.keywords.values():
            if kw.applicator_cls is Applicator:
                kw.json._resolve_references()
            elif kw.applicator_cls is ArrayApplicator:
                for schema in kw.json:
                    schema._resolve_references()
            elif kw.applicator_cls is PropertyApplicator:
                for schema in kw.json.values():
                    schema._resolve_references()

    @staticmethod
    def _resolve_dependencies(kwdefs: Dict[str, KeywordDef]) -> Iterator[KeywordDef]:
        dependencies = {
            key: [depkey for depkey in tuplify(kwdef.depends_on)
                  if kwdefs.get(depkey)]
            for key, kwdef in kwdefs.items()
        }
        while dependencies:
            for key, depkeys in dependencies.items():
                if not depkeys:
                    del dependencies[key]
                    for deps in dependencies.values():
                        try:
                            deps.remove(key)
                        except ValueError:
                            pass
                    yield kwdefs[key]
                    break

    def validate(self) -> None:
        if not (scope := self.metaschema.evaluate(JSON(self.value))).valid:
            messages = ''
            for error in scope.collect_errors():
                messages += f"\ninstance path={error.instance_path};" \
                            f" evaluation path={error.evaluation_path};" \
                            f" error={error.message=}"
            raise JSONSchemaError(f"The schema is invalid against its metaschema:{messages}")

    def evaluate(self, instance: JSON, scope: Scope = None) -> Scope:
        if scope is None:
            scope = Scope(self)

        if self.value is True:
            pass

        elif self.value is False:
            scope.fail(instance, "The instance is disallowed by a boolean false schema")

        else:
            for key, keyword in self.keywords.items():
                if keyword.can_evaluate(instance):
                    with scope(key, self) as subscope:
                        keyword.evaluate(instance, subscope)

            if any(child._assert and not child.valid for child in scope.children.values()):
                scope.fail(instance, "The instance failed validation against the schema")

        return scope

    @property
    def parentschema(self) -> Optional[JSONSchema]:
        parent = self.parent
        while parent is not None:
            if isinstance(parent, JSONSchema):
                return parent
            parent = parent.parent

    @property
    def metaschema(self) -> Metaschema:
        from jschon.catalogue import Catalogue

        if (uri := self.metaschema_uri) is None:
            raise JSONSchemaError("The schema's metaschema URI has not been set")

        if not isinstance(metaschema := Catalogue.get_schema(uri), Metaschema):
            raise JSONSchemaError(f"The schema referenced by {uri} is not a metachema")

        return metaschema

    @property
    def metaschema_uri(self) -> Optional[URI]:
        if self._metaschema_uri is not None:
            return self._metaschema_uri
        if self.parentschema is not None:
            return self.parentschema.metaschema_uri

    @metaschema_uri.setter
    def metaschema_uri(self, value: Optional[URI]) -> None:
        self._metaschema_uri = value

    @property
    def base_uri(self) -> Optional[URI]:
        if self._uri is not None:
            return self._uri.copy(fragment=False)
        if self.parentschema is not None:
            return self.parentschema.base_uri

    @property
    def uri(self) -> Optional[URI]:
        return self._uri

    @uri.setter
    def uri(self, value: Optional[URI]) -> None:
        from jschon.catalogue import Catalogue

        if self._uri != value:
            if self._uri is not None:
                Catalogue.del_schema(self._uri)

            self._uri = value

            if self._uri is not None:
                Catalogue.add_schema(self._uri, self)

    @property
    def canonical_uri(self) -> Optional[URI]:
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


class Metaschema(JSONSchema):

    def __init__(
            self,
            value: Mapping[str, AnyJSONCompatible],
            core_vocabulary: Vocabulary,
            *default_vocabularies: Vocabulary,
            **kwargs,
    ):
        self.core_vocabulary: Vocabulary = core_vocabulary
        self.default_vocabularies: Tuple[Vocabulary, ...] = default_vocabularies
        self.kwdefs: Dict[str, KeywordDef] = {}
        super().__init__(value, **kwargs)

    def _bootstrap(self, value: Mapping[str, AnyJSONCompatible]) -> None:
        super()._bootstrap(value)
        self.kwdefs.update(self.core_vocabulary.kwdefs)
        if "$vocabulary" not in value:
            for vocabulary in self.default_vocabularies:
                self.kwdefs.update(vocabulary.kwdefs)


class Vocabulary:

    def __init__(self, uri: URI, *kwdefs: KeywordDef):
        self.uri: URI = uri
        self.kwdefs: Dict[str, KeywordDef] = {
            kwdef.key: kwdef for kwdef in kwdefs
        }


@dataclass
class KeywordDef:
    kwclass: Type[Keyword]
    key: str
    instance_types: Union[str, Tuple[str, ...]] = None
    depends_on: Union[str, Tuple[str, ...]] = None


class Keyword:
    def __init__(
            self,
            parentschema: JSONSchema,
            key: str,
            value: AnyJSONCompatible,
            *instance_types: str,
    ):
        self.applicator_cls = None
        for applicator_cls in (Applicator, ArrayApplicator, PropertyApplicator):
            if isinstance(self, applicator_cls):
                if (kwjson := applicator_cls.jsonify(parentschema, key, value)) is not None:
                    self.applicator_cls = applicator_cls
                    break
        else:
            kwjson = JSON(value, parent=parentschema, key=key)

        self.parentschema: JSONSchema = parentschema
        self.key: str = key
        self.json: JSON = kwjson
        self.instance_types: Tuple[str, ...] = instance_types

    def can_evaluate(self, instance: JSON) -> bool:
        if not self.instance_types or instance.type in self.instance_types:
            return True

        if instance.type == "number" and "integer" in self.instance_types:
            return instance.value == int(instance.value)

        return False

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        pass

    def __str__(self) -> str:
        return f'{self.json.path}: {self.json}'


class Applicator:
    """Sets up a subschema for an applicator keyword."""

    @staticmethod
    def jsonify(parentschema: JSONSchema, key: str, value: AnyJSONCompatible) -> Optional[JSONSchema]:
        if JSONSchema.iscompatible(value):
            return JSONSchema(value, parent=parentschema, key=key)


class ArrayApplicator:
    """Sets up an array of subschemas for an applicator keyword."""

    @staticmethod
    def jsonify(parentschema: JSONSchema, key: str, value: AnyJSONCompatible) -> Optional[JSON]:
        if isinstance(value, Sequence) and all(JSONSchema.iscompatible(v) for v in value):
            return JSON(value, parent=parentschema, key=key, itemclass=JSONSchema)


class PropertyApplicator:
    """Sets up property-based subschemas for an applicator keyword."""

    @staticmethod
    def jsonify(parentschema: JSONSchema, key: str, value: AnyJSONCompatible) -> Optional[JSON]:
        if isinstance(value, Mapping) and all(
                isinstance(k, str) and JSONSchema.iscompatible(v)
                for k, v in value.items()
        ):
            return JSON(value, parent=parentschema, key=key, itemclass=JSONSchema)


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
        self.children: Dict[str, Scope] = {}
        self.annotations: Dict[str, Annotation] = {}
        self.errors: List[Error] = []
        self._assert = True
        self._discard = False

    @contextmanager
    def __call__(self, key: str, schema: JSONSchema = None) -> ContextManager[Scope]:
        """Yield a subscope of the current scope by descending down the
        evaluation path by ``key``, into ``schema`` if given, or within
        the schema of the current scope otherwise."""
        path = self.path / key
        schema = schema or self.schema
        if schema is self.schema:
            relpath = self.relpath / key
        else:
            relpath = JSONPointer((key,))

        self.children[key] = (child := Scope(
            schema,
            path=path,
            relpath=relpath,
            parent=self,
        ))
        try:
            yield child
        finally:
            if child._discard:
                del self.children[key]

    @property
    def root(self) -> Scope:
        scope = self
        while scope.parent is not None:
            scope = scope.parent
        return scope

    def sibling(self, key: str) -> Optional[Scope]:
        return self.parent.children.get(key) if self.parent else None

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
        """Indicate that the scope's validity should not affect its
        assertion result."""
        self._assert = False

    def discard(self) -> None:
        """Indicate that the scope should be ignored and discarded."""
        self._discard = True

    @property
    def valid(self) -> bool:
        return not self.errors

    @property
    def absolute_uri(self) -> Optional[URI]:
        if (schema_uri := self.schema.canonical_uri) is not None:
            if fragment := schema_uri.fragment:
                relpath = JSONPointer.parse_uri_fragment(fragment) / self.relpath
            else:
                relpath = self.relpath
            return schema_uri.copy(fragment=relpath.uri_fragment())

    def collect_annotations(self, instance: JSON, key: str = None) -> Iterator[Annotation]:
        """Return an iterator over annotations produced in this subtree
        for the given instance, optionally filtered by keyword."""
        if self.valid:
            for annotation_key, annotation in self.annotations.items():
                if (key is None or key == annotation_key) and annotation.instance_path == instance.path:
                    yield annotation
            for child in self.children.values():
                yield from child.collect_annotations(instance, key)

    def collect_errors(self) -> Iterator[Error]:
        """Return an iterator over errors produced in this subtree."""
        if not self.valid:
            yield from self.errors
            for child in self.children.values():
                yield from child.collect_errors()

    def __str__(self) -> str:
        return str(self.path)
