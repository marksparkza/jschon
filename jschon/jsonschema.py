from __future__ import annotations

import dataclasses
from typing import *

from jschon.catalogue import Catalogue
from jschon.exceptions import *
from jschon.json import JSON, JSONObject, JSONArray, AnyJSON
from jschon.jsoninstance import JSONInstance
from jschon.jsonpointer import JSONPointer
from jschon.types import AnyJSONCompatible, tuplify, is_schema_compatible
from jschon.uri import URI

__all__ = [
    'evaluate',
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
]


def evaluate(schema: JSONSchema, document: JSON) -> JSONInstance:
    instance = JSONInstance(
        json=document,
        path=schema.location,
        parent=None,
    )
    schema.evaluate(instance)
    return instance


class JSONSchema(JSON):
    _cache: Dict[URI, JSONSchema] = {}

    @classmethod
    def get(cls, uri: URI) -> JSONSchema:
        try:
            return cls._cache[uri]
        except KeyError:
            pass

        doc = Catalogue.load(uri.copy(fragment=False))
        if uri.fragment:
            ref = JSONPointer.parse_uri_fragment(f'#{uri.fragment}')
            doc = ref.evaluate(doc)
        return JSONSchema(doc)

    def __new__(
            cls,
            value: Union[bool, Mapping[str, AnyJSONCompatible]],
            **kwargs: Any,
    ) -> JSONSchema:
        if isinstance(value, bool):
            return object.__new__(JSONBooleanSchema)
        if is_schema_compatible(value, allowbool=False):
            return object.__new__(JSONObjectSchema)
        raise TypeError("Expecting bool or Mapping[str, AnyJSONCompatible]")

    def __init__(
            self,
            value: Union[bool, Mapping[str, AnyJSONCompatible]],
            *,
            base_uri: URI = None,
            metaschema_uri: URI = None,
            location: JSONPointer = None,
            superkeyword: Keyword = None,
    ) -> None:
        super().__init__(value, location=location)

        self._base_uri: Optional[URI] = base_uri
        self._metaschema_uri: Optional[URI] = metaschema_uri
        self.superkeyword: Optional[Keyword] = superkeyword
        self.keywords: Dict[str, Keyword] = {}
        self.kwclasses: Dict[str, KeywordClass] = {}  # used by metaschemas

        if base_uri is not None:
            JSONSchema._cache[base_uri] = self

        # ensure the metaschema is loaded, if specified
        if metaschema_uri is not None:
            JSONSchema.get(metaschema_uri)

        if self.location and not superkeyword:
            raise JSONSchemaError("superkeyword must be specified for a subschema")

    @property
    def metaschema(self) -> Optional[JSONSchema]:
        if (uri := self.metaschema_uri) is not None:
            return JSONSchema.get(uri)

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
        if self._base_uri is not None:
            return self._base_uri
        if self.superkeyword is not None:
            return self.superkeyword.superschema.base_uri

    @base_uri.setter
    def base_uri(self, value: Optional[URI]) -> None:
        self._base_uri = value
        if value is not None:
            JSONSchema._cache[value] = self

    @property
    def rootschema(self):
        return self if not self.superkeyword else self.superkeyword.superschema.rootschema

    def evaluate(self, instance: JSONInstance) -> None:
        raise NotImplementedError


class JSONBooleanSchema(JSONSchema):
    __type__ = "boolean"

    def __new__(
            cls,
            value: bool,
            **kwargs: Any,
    ) -> JSONBooleanSchema:
        if isinstance(value, bool):
            return object.__new__(cls)
        raise TypeError("Expecting bool")

    def evaluate(self, instance: JSONInstance) -> None:
        if self.value:
            instance.pass_()
        else:
            instance.fail()


class JSONObjectSchema(JSONSchema, Mapping[str, AnyJSON]):
    __type__ = "object"

    _bootstrap_kwclasses: Tuple[KeywordClass, ...] = ...

    @classmethod
    def bootstrap(cls, *kwclasses: KeywordClass) -> None:
        cls._bootstrap_kwclasses = kwclasses

    def __new__(
            cls,
            value: Mapping[str, AnyJSONCompatible],
            **kwargs: Any,
    ) -> JSONObjectSchema:
        if is_schema_compatible(value, allowbool=False):
            return object.__new__(cls)
        raise TypeError("Expecting Mapping[str, AnyJSONCompatible]")

    def __init__(
            self,
            value: Mapping[str, AnyJSONCompatible],
            **kwargs: Any,
    ) -> None:
        super().__init__(value, **kwargs)
        self.keywords: Dict[str, Keyword] = {
            kw: kwclass(self, value[kw])
            for kwclass in self._bootstrap_kwclasses
            if (kw := kwclass.__keyword__) in value
        }

        if (metaschema := self.metaschema) is not None:
            kwclasses = {
                kw: kwclass for kw in value
                if (kwclass := metaschema.kwclasses.get(kw)) and kwclass not in self._bootstrap_kwclasses
            }
            self.keywords.update({
                kwclass.__keyword__: kwclass(self, value[kwclass.__keyword__])
                for kwclass in self._resolve_keyword_dependencies(kwclasses)
            })
            if not self.location:
                metaschema.evaluate(instance := JSONInstance(JSON(value), JSONPointer(), None))
                if not instance.valid:
                    raise JSONSchemaError("The schema is invalid against its metaschema")

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

    def evaluate(self, instance: JSONInstance) -> None:
        for keyword in self.keywords.values():
            if keyword.__types__ is None or isinstance(
                    instance.json, tuple(JSON.classfor(t) for t in tuplify(keyword.__types__))
            ):
                instance.descend(keyword.__keyword__, instance.json, keyword.evaluate)

        if all(child.valid or not child.assert_
               for child in instance.children.values()):
            instance.pass_()
        else:
            instance.fail()

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
            superschema: JSONSchema,
            value: AnyJSONCompatible,
    ) -> None:
        self.superschema: JSONSchema = superschema
        self.location: JSONPointer = superschema.location / self.__keyword__
        self.json: JSON

        # there may be several possible ways in which to set up subschemas for
        # an applicator keyword; we try a series of applicator classes in turn
        # until one is found that works for the keyword's value, else we fall
        # through to the default behaviour of simply JSON-ifying the value
        for applicator in self.applicators:
            if jsonified := applicator(self)(value):
                self.json = jsonified
                break
        else:
            self.json = JSON(value, location=self.location)

    def evaluate(self, instance: JSONInstance) -> None:
        pass

    def __str__(self) -> str:
        return f'"{self.__keyword__}": {self.json}'

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self})'


KeywordClass = Type[Keyword]


class Applicator:
    """ Sets up a subschema for an applicator keyword. """

    def __init__(self, keyword: Keyword):
        self.keyword = keyword

    def __call__(self, value: AnyJSONCompatible) -> Optional[JSONSchema]:
        if is_schema_compatible(value):
            return JSONSchema(
                value,
                location=self.keyword.location,
                superkeyword=self.keyword,
            )


ApplicatorClass = Type[Applicator]


class ArrayApplicator(Applicator):
    """ Sets up an array of subschemas for an applicator keyword. """

    def __call__(self, value: AnyJSONCompatible) -> Optional[JSONArray[JSONSchema]]:
        if isinstance(value, Sequence) and all(is_schema_compatible(v) for v in value):
            return JSONArray(
                [
                    JSONSchema(
                        item,
                        location=self.keyword.location / str(index),
                        superkeyword=self.keyword,
                    )
                    for index, item in enumerate(value)
                ],
                location=self.keyword.location,
            )


class PropertyApplicator(Applicator):
    """ Sets up property-based subschemas for an applicator keyword. """

    def __call__(self, value: AnyJSONCompatible) -> Optional[JSONObject[JSONSchema]]:
        if isinstance(value, Mapping) and all(
                isinstance(k, str) and is_schema_compatible(v)
                for k, v in value.items()
        ):
            return JSONObject(
                {
                    name: JSONSchema(
                        item,
                        location=self.keyword.location / name,
                        superkeyword=self.keyword,
                    )
                    for name, item in value.items()
                },
                location=self.keyword.location,
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
        uri.validate(require_scheme=True, require_normalized=True)

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


@dataclasses.dataclass
class FormatResult:
    valid: bool
    error: Optional[str] = None
