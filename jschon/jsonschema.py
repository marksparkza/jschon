from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import *
from uuid import uuid4

from jschon.catalogue import Catalogue
from jschon.exceptions import *
from jschon.json import JSON, JSONObject, JSONArray, AnyJSON, JSONCompatible, AnyJSONCompatible
from jschon.jsonpointer import JSONPointer
from jschon.uri import URI
from jschon.utils import tuplify

__all__ = [
    'JSONSchema',
    'JSONBooleanSchema',
    'JSONObjectSchema',
    'Keyword',
    'KeywordClass',
    'Applicator',
    'ArrayApplicator',
    'PropertyApplicator',
    'ApplicatorClass',
    'Vocabulary',
    'VocabularyClass',
    'FormatVocabulary',
    'Format',
    'FormatClass',
    'FormatResult',
    'Annotation',
    'Error',
    'Scope',
]


class JSONSchema(JSON):
    _cache: Dict[URI, JSONSchema] = {}

    @classmethod
    def iscompatible(cls, value: Any) -> bool:
        return JSONBooleanSchema.iscompatible(value) or JSONObjectSchema.iscompatible(value)

    @classmethod
    def get(cls, uri: URI, metaschema_uri: URI = None) -> JSONSchema:
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
            schema = JSONSchema(doc, uri=base_uri, metaschema_uri=metaschema_uri)

        if uri.fragment:
            ptr = JSONPointer.parse_uri_fragment(f'#{uri.fragment}')
            schema = ptr.evaluate(schema)

        if not isinstance(schema, JSONSchema):
            raise JSONSchemaError(f"The object referenced by {uri} is not a JSON Schema")

        return schema

    @classmethod
    def set(cls, uri: URI, schema: JSONSchema) -> None:
        cls._encache(uri, schema)

    @classmethod
    def clear(cls) -> None:
        cls._cache.clear()

    @classmethod
    def _encache(cls, uri: Optional[URI], schema: JSONSchema) -> None:
        if uri is not None:
            cls._cache[uri] = schema

    @classmethod
    def _decache(cls, uri: Optional[URI]) -> None:
        cls._cache.pop(uri, None)

    def __new__(
            cls,
            value: Union[bool, Mapping[str, AnyJSONCompatible]],
            **kwargs: Any,
    ) -> JSONSchema:
        for c in (JSONBooleanSchema, JSONObjectSchema):
            if c.iscompatible(value):
                return object.__new__(c)

        raise TypeError(f"{value=} is not JSONSchema-compatible")

    def __init__(
            self,
            value: Union[bool, Mapping[str, AnyJSONCompatible]],
            *,
            uri: URI = None,
            metaschema_uri: URI = None,
            path: JSONPointer = None,
            superkeyword: Keyword = None,
    ) -> None:
        super().__init__(value, path=path)

        self._encache(uri, self)
        self._uri: Optional[URI] = uri
        self._metaschema_uri: Optional[URI] = metaschema_uri
        self.superkeyword: Optional[Keyword] = superkeyword
        self.keywords: Dict[str, Keyword] = {}
        self.kwclasses: Dict[str, KeywordClass] = {}  # used by metaschemas

    def validate(self) -> None:
        if not self.metaschema.evaluate(JSON(self.value)):
            raise JSONSchemaError("The schema is invalid against its metaschema")

    def evaluate(self, instance: JSON, scope: Scope = None) -> bool:
        raise NotImplementedError

    @property
    def metaschema(self) -> JSONSchema:
        if (uri := self.metaschema_uri) is None:
            raise JSONSchemaError("The schema's metaschema URI has not been set")

        return JSONSchema.get(uri, uri)

    @property
    def metaschema_uri(self) -> Optional[URI]:
        if self._metaschema_uri is not None:
            return self._metaschema_uri
        if self.superkeyword is not None:
            return self.superkeyword.superschema.metaschema_uri

    @metaschema_uri.setter
    def metaschema_uri(self, value: Optional[URI]) -> None:
        self._metaschema_uri = value

    @property
    def base_uri(self) -> Optional[URI]:
        if self._uri is not None:
            return self._uri.copy(fragment=False)
        if self.superkeyword is not None:
            return self.superkeyword.superschema.base_uri

    @property
    def uri(self) -> Optional[URI]:
        return self._uri

    @uri.setter
    def uri(self, value: Optional[URI]) -> None:
        if self._uri != value:
            self._decache(self._uri)
            self._encache(value, self)
            self._uri = value


class JSONBooleanSchema(JSONSchema):
    __type__ = "boolean"

    @classmethod
    def iscompatible(cls, value: Any) -> bool:
        return isinstance(value, bool)

    def evaluate(self, instance: JSON, scope: Scope = None) -> bool:
        if scope is None:
            scope = Scope(self)

        if not self.value:
            scope.fail(instance, "The instance is disallowed by a boolean false schema")

        return self.value


class JSONObjectSchema(JSONSchema, Mapping[str, AnyJSON]):
    __type__ = "object"

    _bootstrap_kwclasses: Tuple[KeywordClass, ...] = ...

    @classmethod
    def iscompatible(cls, value: Any) -> bool:
        return isinstance(value, Mapping) and \
               all(isinstance(k, str) and isinstance(v, JSONCompatible)
                   for k, v in value.items())

    @classmethod
    def bootstrap(cls, *kwclasses: KeywordClass) -> None:
        cls._bootstrap_kwclasses = kwclasses

    def __init__(
            self,
            value: Mapping[str, AnyJSONCompatible],
            **kwargs: Any,
    ) -> None:
        super().__init__(value, **kwargs)

        if self.superkeyword is None and self.uri is None:
            self.uri = URI(f'mem:{uuid4()}')

        self.keywords: Dict[str, Keyword] = {
            kw: kwclass(value[kw], superschema=self)
            for kwclass in self._bootstrap_kwclasses
            if (kw := kwclass.__keyword__) in value
        }
        kwclasses = {
            kw: kwclass for kw in value
            if (kwclass := self.metaschema.kwclasses.get(kw)) and kwclass not in self._bootstrap_kwclasses
        }
        self.keywords.update({
            kwclass.__keyword__: kwclass(value[kwclass.__keyword__], superschema=self)
            for kwclass in self._resolve_keyword_dependencies(kwclasses)
        })

    @staticmethod
    def _resolve_keyword_dependencies(kwclasses: Dict[str, KeywordClass]) -> Iterator[KeywordClass]:
        dependencies = {
            kwclass: [depclass for dep in tuplify(kwclass.__depends__) if (depclass := kwclasses.get(dep))]
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

    def evaluate(self, instance: JSON, scope: Scope = None) -> bool:
        if scope is None:
            scope = Scope(self)

        for keyword in self.keywords.values():
            if keyword.__types__ is None or isinstance(
                    instance, tuple(JSON.classfor(t) for t in tuplify(keyword.__types__))
            ):
                with scope(self, keyword.__keyword__) as subscope:
                    keyword.evaluate(instance, subscope)

        if any(child.assert_ and not child.valid for child in scope.children.values()):
            scope.fail(instance, "The instance failed validation against the schema")
            return False

        return True

    def __getitem__(self, key: str) -> JSON:
        return self.keywords[key].json

    def __iter__(self) -> Iterator[str]:
        yield from self.keywords

    def __len__(self) -> int:
        return len(self.keywords)


class Keyword:
    __keyword__: str = ...
    __schema__: Union[bool, dict] = ...
    __types__: Optional[Union[str, Tuple[str, ...]]] = None
    __depends__: Optional[Union[str, Tuple[str, ...]]] = None

    applicators: Tuple[ApplicatorClass, ...] = ()
    vocabulary_uri: URI

    def __init__(
            self,
            value: AnyJSONCompatible,
            *,
            superschema: JSONSchema = JSONSchema(True),
    ) -> None:
        self.json: JSON
        self.path: JSONPointer = superschema.path / self.__keyword__
        self.superschema: JSONSchema = superschema

        # there may be several possible ways in which to set up subschemas for
        # an applicator keyword; we try a series of applicator classes in turn
        # until one is found that works for the keyword's value, else we fall
        # through to the default behaviour of simply JSON-ifying the value
        for applicator in self.applicators:
            if (jsonified := applicator(self)(value)) is not None:
                self.json = jsonified
                break
        else:
            self.json = JSON(value, path=self.path)

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        pass

    def __str__(self) -> str:
        return f'"{self.__keyword__}": {self.json}'

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.json.value!r})'


KeywordClass = Type[Keyword]


class Applicator:
    """Sets up a subschema for an applicator keyword."""

    def __init__(self, keyword: Keyword):
        self.keyword = keyword

    def __call__(self, value: AnyJSONCompatible) -> Optional[JSONSchema]:
        if JSONSchema.iscompatible(value):
            return JSONSchema(
                value,
                path=self.keyword.path,
                superkeyword=self.keyword,
            )


ApplicatorClass = Type[Applicator]


class ArrayApplicator(Applicator):
    """Sets up an array of subschemas for an applicator keyword."""

    def __call__(self, value: AnyJSONCompatible) -> Optional[JSONArray[JSONSchema]]:
        if isinstance(value, Sequence) and all(JSONSchema.iscompatible(v) for v in value):
            return JSONArray(
                [
                    JSONSchema(
                        item,
                        path=self.keyword.path / str(index),
                        superkeyword=self.keyword,
                    )
                    for index, item in enumerate(value)
                ],
                path=self.keyword.path,
            )


class PropertyApplicator(Applicator):
    """Sets up property-based subschemas for an applicator keyword."""

    def __call__(self, value: AnyJSONCompatible) -> Optional[JSONObject[JSONSchema]]:
        if isinstance(value, Mapping) and all(
                isinstance(k, str) and JSONSchema.iscompatible(v)
                for k, v in value.items()
        ):
            return JSONObject(
                {
                    name: JSONSchema(
                        item,
                        path=self.keyword.path / name,
                        superkeyword=self.keyword,
                    )
                    for name, item in value.items()
                },
                path=self.keyword.path,
            )


class Vocabulary:
    _kwclasses: Dict[URI, List[KeywordClass]] = {}
    _vcclass: Dict[URI, VocabularyClass] = {}
    _cache: Dict[URI, Vocabulary] = {}

    @classmethod
    def register(
            cls,
            uri: URI,
            kwclasses: Iterable[KeywordClass],
    ) -> None:
        cls._kwclasses[uri] = []
        cls._vcclass[uri] = cls
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

    def __new__(cls, uri: URI, required: bool) -> Vocabulary:
        try:
            return object.__new__(Vocabulary._vcclass[uri])
        except KeyError as e:
            raise VocabularyError(f"'{uri}' is not a recognized vocabulary URI") from e

    def __init__(self, uri: URI, required: bool) -> None:
        self.uri: URI = uri
        self.required: bool = required
        self.kwclasses: Dict[str, KeywordClass] = {
            kwclass.__keyword__: kwclass for kwclass in self._kwclasses[uri]
        }
        self._cache[uri] = self


VocabularyClass = Type[Vocabulary]


class FormatVocabulary(Vocabulary):
    _fmtclasses: Dict[URI, List[FormatClass]] = {}
    _assertfmt: Dict[URI, Optional[bool]] = {}

    @classmethod
    def register(
            cls,
            uri: URI,
            kwclasses: Iterable[KeywordClass],
            fmtclasses: Iterable[FormatClass] = (),
            assert_: bool = None,
    ) -> None:
        super().register(uri, kwclasses)
        cls._fmtclasses[uri] = []
        cls._assertfmt[uri] = assert_
        for fmtclass in fmtclasses:
            if issubclass(fmtclass, Format):
                cls._fmtclasses[uri] += [fmtclass]

    @classmethod
    def get(cls, uri: URI) -> FormatVocabulary:
        vocab = super().get(uri)
        if isinstance(vocab, FormatVocabulary):
            return vocab
        raise VocabularyError(f"The vocabulary identified by '{uri}' does not support formats")

    def __init__(self, uri: URI, required: bool) -> None:
        super().__init__(uri, required)
        assert_ = force_assert if (force_assert := self._assertfmt[uri]) is not None else required
        self.formats: Dict[str, Format] = {
            fmtclass.__attr__: fmtclass(assert_)
            for fmtclass in self._fmtclasses[uri]
        }


class Format:
    __attr__: str = ...
    __types__: Union[str, Tuple[str, ...]] = "string"

    def __init__(self, assert_: bool) -> None:
        self.assert_: bool = assert_

    def evaluate(self, instance: JSON) -> FormatResult:
        raise NotImplementedError


FormatClass = Type[Format]


@dataclass
class FormatResult:
    valid: bool
    error: Optional[str] = None


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
        self.parent: Scope = parent
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

    def __str__(self) -> str:
        return str(self.path)
