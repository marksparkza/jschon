from __future__ import annotations

import dataclasses
from typing import *

import rfc3986.exceptions
import rfc3986.validators
from rfc3986 import URIReference

from jschon.catalogue import Catalogue
from jschon.exceptions import *
from jschon.json import JSON, JSONObject, JSONArray, AnyJSON
from jschon.jsonpointer import JSONPointer
from jschon.types import AnyJSONCompatible, tuplify, is_schema_compatible

__all__ = [
    'JSONSchema',
    'JSONBooleanSchema',
    'JSONObjectSchema',
    'JSONSchemaResult',
    'Keyword',
    'KeywordClass',
    'KeywordResult',
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


class JSONSchema(JSON):
    _cache: Dict[URIReference, JSONSchema] = {}

    @classmethod
    def get(cls, uri: URIReference) -> JSONSchema:
        try:
            return cls._cache[uri]
        except KeyError:
            pass

        base, _, fragment = uri.unsplit().partition('#')
        doc = Catalogue.load(rfc3986.uri_reference(base))
        if fragment:
            ref = JSONPointer.parse_uri_fragment(f'#{fragment}')
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
            base_uri: URIReference = None,
            metaschema_uri: URIReference = None,
            location: JSONPointer = None,
            superkeyword: Keyword = None,
    ) -> None:
        super().__init__(value, location=location)

        self._base_uri: Optional[URIReference] = base_uri
        self._metaschema_uri: Optional[URIReference] = metaschema_uri
        self.superkeyword: Optional[Keyword] = superkeyword
        self.keywords: Dict[str, Keyword] = {}
        self.kwclasses: Dict[str, KeywordClass] = {}  # used by metaschemas

        if base_uri is not None:
            JSONSchema._cache[base_uri] = self

        # ensure the metaschema is loaded, if specified
        if metaschema_uri is not None:
            JSONSchema.get(metaschema_uri)

        if self.location and not superkeyword:
            raise SchemaError("superkeyword must be specified for a subschema")

    @property
    def metaschema(self) -> Optional[JSONSchema]:
        if (uri := self.metaschema_uri) is not None:
            return JSONSchema.get(uri)

    @property
    def metaschema_uri(self) -> Optional[URIReference]:
        if self._metaschema_uri is not None:
            return self._metaschema_uri
        if self.superkeyword is not None:
            return self.superkeyword.superschema.metaschema_uri

    @metaschema_uri.setter
    def metaschema_uri(self, value: Optional[URIReference]) -> None:
        self._metaschema_uri = value

    @property
    def base_uri(self) -> Optional[URIReference]:
        if self._base_uri is not None:
            return self._base_uri
        if self.superkeyword is not None:
            return self.superkeyword.superschema.base_uri

    @base_uri.setter
    def base_uri(self, value: Optional[URIReference]) -> None:
        self._base_uri = value
        if value is not None:
            JSONSchema._cache[value] = self

    @property
    def rootschema(self):
        return self if not self.superkeyword else self.superkeyword.superschema.rootschema

    def evaluate(self, instance: JSON) -> JSONSchemaResult:
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"JSONSchema({self})"


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

    def evaluate(self, instance: JSON) -> JSONSchemaResult:
        return JSONSchemaResult(
            keyword=self.superkeyword,
            instance=instance,
            valid=self.value,
            annotation=None,
            error=None,
            subresults=None,
        )


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
        self.keywords = {
            kw: kwclass(self, value[kw])
            for kwclass in self._bootstrap_kwclasses
            if (kw := kwclass.__keyword__) in value
        }

        if (metaschema := self.metaschema) is not None:
            if not self.location and not (result := metaschema.evaluate(JSON(value))).valid:
                raise SchemaError(f"The schema is invalid against its metaschema: {list(result.errors())}")

            kwclasses = {
                kw: kwclass for kw in value
                if (kwclass := metaschema.kwclasses.get(kw)) and kwclass not in self._bootstrap_kwclasses
            }
            self.keywords.update({
                kwclass.__keyword__: kwclass(self, value[kwclass.__keyword__])
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

    def evaluate(self, instance: JSON) -> JSONSchemaResult:
        result = JSONSchemaResult(
            keyword=self.superkeyword,
            instance=instance,
            valid=True,
            annotation=None,
            error=None,
            subresults=[],
        )
        for keyword in self.keywords.values():
            if keyword.__types__ is None or \
                    isinstance(instance, tuple(JSON.classfor(t) for t in tuplify(keyword.__types__))):
                keyword.result = keyword.evaluate(instance)
                if keyword.result is not None:
                    result.subresults += [JSONSchemaResult(
                        keyword=keyword,
                        instance=instance,
                        valid=(valid := not keyword.assert_ or keyword.result.valid),
                        annotation=keyword.result.annotation if valid else None,
                        error=keyword.result.error if not valid else None,
                        subresults=keyword.result.subresults,
                    )]
                    if not valid:
                        result.valid = False
        return result

    def __getitem__(self, key: str) -> JSON:
        return self.keywords[key].json

    def __iter__(self) -> Iterator[str]:
        yield from self.keywords

    def __len__(self) -> int:
        return len(self.keywords)


@dataclasses.dataclass
class JSONSchemaResult:
    keyword: Optional[Keyword]
    instance: JSON
    valid: bool
    annotation: Optional[AnyJSONCompatible]
    error: Optional[str]
    subresults: Optional[List[JSONSchemaResult]]

    def errors(self) -> Iterator[str]:
        if error := self.error:
            keyword_location = str(self.keyword.location) if self.keyword else ''
            instance_location = str(self.instance.location)
            yield f"{keyword_location=}, {instance_location=}, {error=}"
        if self.subresults:
            for subresult in self.subresults:
                yield from subresult.errors()


class Keyword:
    __keyword__: str = ...
    __schema__: Union[bool, dict] = ...
    __types__: Optional[Union[str, Tuple[str, ...]]] = None
    __depends__: Optional[Union[str, Tuple[str, ...]]] = None

    applicators: Tuple[ApplicatorClass, ...] = ()
    vocabulary_uri: str

    def __init__(
            self,
            superschema: JSONSchema,
            value: AnyJSONCompatible,
    ) -> None:
        self.superschema: JSONSchema = superschema
        self.location: JSONPointer = superschema.location / self.__keyword__
        self.json: JSON
        self.result: Optional[KeywordResult] = None

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

    @property
    def assert_(self) -> bool:
        return True

    def evaluate(self, instance: JSON) -> Optional[KeywordResult]:
        pass

    def __repr__(self) -> str:
        return f'Keyword("{self.__keyword__}")'


KeywordClass = Type[Keyword]


@dataclasses.dataclass
class KeywordResult:
    valid: bool
    annotation: Optional[AnyJSONCompatible] = None
    error: Optional[str] = None
    subresults: Optional[List[JSONSchemaResult]] = None


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
    _kwclasses: Dict[str, List[KeywordClass]] = {}
    _vcclass: Dict[str, VocabularyClass] = {}
    _cache: Dict[str, Vocabulary] = {}

    @classmethod
    def register(
            cls,
            uri: str,
            kwclasses: Iterable[KeywordClass],
    ) -> None:
        validator = rfc3986.validators.Validator().require_presence_of('scheme')
        try:
            validator.validate(uri_ref := rfc3986.uri_reference(uri))
        except rfc3986.exceptions.ValidationError as e:
            raise ValueError(f"{uri=} is not a valid URI or does not contain a scheme") from e

        if uri_ref != uri_ref.normalize():
            raise ValueError(f"{uri=} is not normalized")

        cls._kwclasses[uri] = []
        cls._vcclass[uri] = cls
        for kwclass in kwclasses:
            if issubclass(kwclass, Keyword):
                kwclass.vocabulary_uri = uri
                cls._kwclasses[uri] += [kwclass]

    @classmethod
    def get(cls, uri: str) -> Vocabulary:
        try:
            return cls._cache[uri]
        except KeyError as e:
            raise VocabularyError(f"{uri=} is not a recognized vocabulary URI") from e

    def __new__(cls, uri: str, required: bool) -> Vocabulary:
        try:
            return object.__new__(Vocabulary._vcclass[uri])
        except KeyError as e:
            raise VocabularyError(f"{uri=} is not a recognized vocabulary URI") from e

    def __init__(self, uri: str, required: bool) -> None:
        self.uri: str = uri
        self.required: bool = required
        self.kwclasses: Dict[str, KeywordClass] = {
            kwclass.__keyword__: kwclass for kwclass in self._kwclasses[uri]
        }
        self._cache[uri] = self


VocabularyClass = Type[Vocabulary]


class FormatVocabulary(Vocabulary):
    _fmtclasses: Dict[str, List[FormatClass]] = {}
    _assertfmt: Dict[str, Optional[bool]] = {}

    @classmethod
    def register(
            cls,
            uri: str,
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
    def get(cls, uri: str) -> FormatVocabulary:
        vocab = super().get(uri)
        if isinstance(vocab, FormatVocabulary):
            return vocab
        raise VocabularyError(f"The vocabulary identified by '{uri}' does not support formats")

    def __init__(self, uri: str, required: bool) -> None:
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
