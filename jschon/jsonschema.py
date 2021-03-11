from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import *
from uuid import uuid4

from jschon.catalogue import Catalogue
from jschon.exceptions import *
from jschon.json import *
from jschon.jsonpointer import JSONPointer
from jschon.uri import URI
from jschon.utils import tuplify

__all__ = [
    'JSONSchema',
    'Keyword',
    'KeywordClass',
    'Applicator',
    'ArrayApplicator',
    'PropertyApplicator',
    'ApplicatorClass',
    'Vocabulary',
    'Annotation',
    'Error',
    'Scope',
]


class JSONSchema(JSON):
    _cache: Dict[URI, JSONSchema] = {}
    _bootstrap_kwclasses: Tuple[KeywordClass, ...] = ...

    @classmethod
    def bootstrap(cls, *kwclasses: KeywordClass) -> None:
        cls._bootstrap_kwclasses = kwclasses

    @classmethod
    def load(cls, uri: URI, **kwargs: Any) -> JSONSchema:
        """Load a (sub)schema identified by uri from the cache, or from the
        catalogue if not already cached.

        Additional kwargs are passed to the JSONSchema constructor for
        catalogue-loaded instances.
        """
        try:
            return cls._cache[uri]
        except KeyError:
            pass

        schema = None
        base_uri = uri.copy(fragment=False)

        if uri.fragment is not None:
            try:
                schema = cls._cache[base_uri]
            except KeyError:
                pass

        if schema is None:
            doc = Catalogue.load(base_uri)
            schema = JSONSchema(doc, uri=base_uri, **kwargs)

        if uri.fragment:
            ptr = JSONPointer.parse_uri_fragment(f'#{uri.fragment}')
            schema = ptr.evaluate(schema)

        if not isinstance(schema, JSONSchema):
            raise JSONSchemaError(f"The object referenced by {uri} is not a JSON Schema")

        return schema

    @classmethod
    def store(cls, uri: URI, schema: JSONSchema) -> None:
        """Store the schema identified by uri to the cache."""
        cls._encache(uri, schema)

    @classmethod
    def clear(cls) -> None:
        """Clear the JSONSchema cache."""
        cls._cache.clear()

    @classmethod
    def _encache(cls, uri: Optional[URI], schema: JSONSchema) -> None:
        if uri is not None:
            cls._cache[uri] = schema

    @classmethod
    def _decache(cls, uri: Optional[URI]) -> None:
        cls._cache.pop(uri, None)

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
        self._encache(uri, self)
        self._uri: Optional[URI] = uri
        self._metaschema_uri: Optional[URI] = metaschema_uri
        self.keywords: Dict[str, Keyword] = {}
        self.kwclasses: Dict[str, KeywordClass] = {}  # used by metaschemas

        # don't call super().__init__
        self.value: AnyJSONValue
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

            for kwclass in self._bootstrap_kwclasses:
                if (key := kwclass.__keyword__) in value:
                    kw = kwclass(self, value[key])
                    self.keywords[key] = kw
                    self.value[key] = kw.json

            kwclasses = {
                key: kwclass for key in value
                if (kwclass := self.metaschema.kwclasses.get(key)) and
                   kwclass not in self._bootstrap_kwclasses
            }

            for kwclass in self._resolve_keyword_dependencies(kwclasses):
                kw = kwclass(self, value[(key := kwclass.__keyword__)])
                self.keywords[key] = kw
                self.value[key] = kw.json

        else:
            raise TypeError(f"{value=} is not JSONSchema-compatible")

    @staticmethod
    def _resolve_keyword_dependencies(kwclasses: Dict[str, KeywordClass]) -> Iterator[KeywordClass]:
        dependencies = {
            kwclass: [depclass for dep in tuplify(kwclass.__depends__)
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
                    with scope(self, key) as subscope:
                        keyword.evaluate(instance, subscope)

            if any(child.assert_ and not child.valid for child in scope.children.values()):
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
    def metaschema(self) -> JSONSchema:
        if (uri := self.metaschema_uri) is None:
            raise JSONSchemaError("The schema's metaschema URI has not been set")

        return JSONSchema.load(uri, metaschema_uri=uri)

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
        if self._uri != value:
            self._decache(self._uri)
            self._encache(value, self)
            self._uri = value


class Keyword:
    __keyword__: str = ...
    __schema__: Union[bool, dict] = ...
    __types__: Optional[Union[str, Tuple[str, ...]]] = None
    __depends__: Optional[Union[str, Tuple[str, ...]]] = None

    applicators: Tuple[ApplicatorClass, ...] = ()
    vocabulary_uri: URI

    def __init__(self, parentschema: JSONSchema, value: AnyJSONCompatible):
        # there may be several possible ways in which to set up subschemas for
        # an applicator keyword; we try a series of applicator classes in turn
        # until one is found that works for the keyword's value, else we fall
        # through to the default behaviour of simply JSON-ifying the value
        for applicator in self.applicators:
            if (kwjson := applicator(parentschema, self.__keyword__)(value)) is not None:
                break
        else:
            kwjson = JSON(value, parent=parentschema, key=self.__keyword__)

        self.json: JSON = kwjson
        self.parentschema: JSONSchema = parentschema

    def can_evaluate(self, instance: JSON) -> bool:
        if self.__types__ is None:
            return True

        types = tuplify(self.__types__)
        if instance.type in types:
            return True

        if instance.type == "number" and "integer" in types:
            return instance.value == int(instance.value)

        return False

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        pass

    def __str__(self) -> str:
        return f'{self.json.path}: {self.json}'


KeywordClass = Type[Keyword]


class Applicator:
    """Sets up a subschema for an applicator keyword."""

    def __init__(self, parent: JSONSchema, key: str):
        self.parent = parent
        self.key = key

    def __call__(self, value: AnyJSONCompatible) -> Optional[JSONSchema]:
        if JSONSchema.iscompatible(value):
            return JSONSchema(value, parent=self.parent, key=self.key)


ApplicatorClass = Type[Applicator]


class ArrayApplicator(Applicator):
    """Sets up an array of subschemas for an applicator keyword."""

    def __call__(self, value: AnyJSONCompatible) -> Optional[JSON[Array[JSONSchema]]]:
        if isinstance(value, Sequence) and all(JSONSchema.iscompatible(v) for v in value):
            return JSON(value, parent=self.parent, key=self.key, itemclass=JSONSchema)


class PropertyApplicator(Applicator):
    """Sets up property-based subschemas for an applicator keyword."""

    def __call__(self, value: AnyJSONCompatible) -> Optional[JSON[Object[JSONSchema]]]:
        if isinstance(value, Mapping) and all(
                isinstance(k, str) and JSONSchema.iscompatible(v)
                for k, v in value.items()
        ):
            return JSON(value, parent=self.parent, key=self.key, itemclass=JSONSchema)


class Vocabulary:
    _kwclasses: Dict[URI, List[KeywordClass]] = {}
    _cache: Dict[URI, Vocabulary] = {}

    @classmethod
    def register(
            cls,
            uri: URI,
            kwclasses: Iterable[KeywordClass],
    ) -> None:
        cls._kwclasses[uri] = []
        for kwclass in kwclasses:
            if issubclass(kwclass, Keyword):
                kwclass.vocabulary_uri = uri
                cls._kwclasses[uri] += [kwclass]

    @classmethod
    def get(cls, uri: URI) -> Vocabulary:
        try:
            return cls._cache[uri]
        except KeyError as e:
            raise VocabularyError(f"'{uri}' is not a recognized vocabulary URI") from e

    def __init__(self, uri: URI, required: bool):
        self.uri: URI = uri
        self.required: bool = required
        try:
            self.kwclasses: Dict[str, KeywordClass] = {
                kwclass.__keyword__: kwclass for kwclass in self._kwclasses[uri]
            }
        except KeyError as e:
            raise VocabularyError(f"'{uri}' is not a recognized vocabulary URI") from e

        self._cache[uri] = self


@dataclass
class Annotation:
    instance_path: JSONPointer
    evaluation_path: JSONPointer
    schema_uri: URI
    value: AnyJSONCompatible


@dataclass
class Error:
    instance_path: JSONPointer
    evaluation_path: JSONPointer
    schema_uri: URI
    message: str


class Scope:
    def __init__(
            self,
            schema: JSONSchema,
            path: JSONPointer = None,
            parent: Scope = None,
    ):
        self.schema: JSONSchema = schema
        self.path: JSONPointer = path or JSONPointer()
        self.parent: Optional[Scope] = parent
        self.children: Dict[str, Scope] = {}
        self.annotations: Dict[str, Annotation] = {}
        self.errors: List[Error] = []
        self.assert_: bool = True  # False => parent schema ignores validity
        self.keep: bool = False  # True => don't discard the scope if it has no results or children

    @contextmanager
    def __call__(self, schema: JSONSchema, key: str) -> Scope:
        self.children[key] = (child := Scope(schema, self.path / key, self))
        try:
            yield child
        finally:
            if not child.children and not child.annotations and not child.errors and not child.keep:
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
                schema_uri=None,
                value=value,
            )

    def fail(self, instance: JSON, error: str) -> None:
        self.errors += [Error(
            instance_path=instance.path,
            evaluation_path=self.path,
            schema_uri=None,
            message=error,
        )]

    @property
    def valid(self) -> bool:
        return not self.errors

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
