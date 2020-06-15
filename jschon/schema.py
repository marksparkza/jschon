from __future__ import annotations

import dataclasses
import json
import pathlib
import typing as _t

from jschon.exceptions import SchemaError, MetaschemaError, VocabularyError
from jschon.json import JSON, JSONPointer
from jschon.types import JSONCompatible, SchemaCompatible
from jschon.utils import validate_uri, tuplify


__all__ = [
    'Schema',
    'SchemaResult',
    'Keyword',
    'KeywordClass',
    'KeywordResult',
    'Metaschema',
    'Vocabulary',
    'VocabularyClass',
    'FormatVocabulary',
    'Format',
    'FormatClass',
    'FormatResult',
]


class Schema:

    def __init__(
            self,
            value: SchemaCompatible,
            *,
            location: JSONPointer = None,
            metaschema_uri: str = None,
            validate: bool = True,
    ) -> None:
        if not isinstance(value, SchemaCompatible):
            raise TypeError(f"{value=} is not one of {SchemaCompatible}")

        self.value: SchemaCompatible = value
        self.location: JSONPointer = location or JSONPointer('')
        self.is_root: bool = self.location.is_root()
        self.metaschema: _t.Optional[Metaschema] = None
        self.keywords: _t.Dict[str, Keyword] = {}

        if isinstance(value, _t.Mapping):
            if metaschema_uri is None and self.is_root:
                metaschema_uri = value.get("$schema")
            if metaschema_uri is None:
                raise SchemaError("Metaschema URI not specified")

            self.metaschema = Metaschema.load(metaschema_uri)
            if self.is_root and validate:
                if not (result := Schema(self.metaschema.value, validate=False).evaluate(JSON(value))).valid:
                    errors = "\n".join(result.errors())
                    raise SchemaError(f"The schema is invalid against its metaschema:\n{errors}")

            kwclasses = {
                kw: kwclass for kw in value
                if (kwclass := self.metaschema.kwclasses.get(kw))
            }
            self.keywords = {
                kwclass.__keyword__: kwclass(self, value[kwclass.__keyword__])
                for kwclass in self._resolve_keyword_dependencies(kwclasses)
            }

    @staticmethod
    def _resolve_keyword_dependencies(kwclasses: _t.Dict[str, KeywordClass]) -> _t.Iterator[KeywordClass]:
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

    def evaluate(self, instance: JSON) -> SchemaResult:
        result = SchemaResult(
            valid=self.value if isinstance(self.value, bool) else True,
            annotation=None,
            error=None,
            subresults=[],
            keyword_location=self.location,
            instance_location=instance.location,
        )
        for keyword in self.keywords.values():
            if not keyword.__types__ or \
                    isinstance(instance, tuple(JSON.typemap[t] for t in tuplify(keyword.__types__))):
                keyword.result = keyword.evaluate(instance)
                if keyword.result is not None:
                    result.subresults += [SchemaResult(
                        valid=(valid := not keyword.assert_ or keyword.result.valid),
                        annotation=keyword.result.annotation if valid else None,
                        error=keyword.result.error if not valid else None,
                        subresults=keyword.result.subresults,
                        keyword_location=keyword.location,
                        instance_location=instance.location,
                    )]
                    if not valid:
                        result.valid = False
        return result


@dataclasses.dataclass
class SchemaResult:
    valid: bool
    annotation: _t.Optional['JSONCompatible']
    error: _t.Optional[str]
    subresults: _t.Optional[_t.List[SchemaResult]]
    keyword_location: JSONPointer
    instance_location: JSONPointer

    def errors(self) -> _t.Iterator[str]:
        if self.error:
            yield f"{self.keyword_location=}, {self.instance_location=}, {self.error=}"
        if self.subresults:
            for subresult in self.subresults:
                yield from subresult.errors()


class Keyword:

    __keyword__: str = ...
    __schema__: _t.Union[bool, dict] = ...
    __types__: _t.Optional[_t.Union[str, _t.Tuple[str]]] = None
    __depends__: _t.Optional[_t.Union[str, _t.Tuple[str]]] = None

    vocabulary_uri: str

    def __init__(
            self,
            superschema: Schema,
            value: JSONCompatible,
    ) -> None:
        if not isinstance(value, JSONCompatible):
            raise TypeError(f"value must be one of {JSONCompatible}")

        self.superschema: Schema = superschema
        self.location: JSONPointer = superschema.location / self.__keyword__
        self.value: JSONCompatible = value
        self.result: _t.Optional[KeywordResult] = None

    @property
    def assert_(self) -> bool:
        return True

    def evaluate(self, instance: JSON) -> _t.Optional[KeywordResult]:
        raise NotImplementedError

    def __repr__(self) -> str:
        return f'Keyword("{self.__keyword__}")'


@dataclasses.dataclass
class KeywordResult:
    valid: bool
    annotation: _t.Optional['JSONCompatible'] = None
    error: _t.Optional[str] = None
    subresults: _t.Optional[_t.List[SchemaResult]] = None


KeywordClass = _t.Type[Keyword]


class Metaschema:

    _catalogue: _t.Dict[str, str] = {}
    _cache: _t.Dict[str, Metaschema] = {}

    @classmethod
    def register(cls, uri: str, filepath: str) -> None:
        validate_uri(uri)
        if not pathlib.Path(filepath).is_file():
            raise ValueError(f"File '{filepath}' not found")
        cls._catalogue[uri] = filepath

    @classmethod
    def load(cls, uri: str) -> Metaschema:
        if uri not in cls._cache:
            try:
                with open(cls._catalogue[uri]) as f:
                    cls._cache[uri] = Metaschema(uri, json.load(f))
            except KeyError as e:
                raise MetaschemaError("Unrecognised metaschema URI") from e
        return cls._cache[uri]

    def __init__(self, uri: str, value: SchemaCompatible) -> None:
        if not isinstance(value, SchemaCompatible):
            raise TypeError(f"value must be one of {SchemaCompatible}")

        self.uri: str = uri
        self.value: SchemaCompatible = value
        self.kwclasses: _t.Dict[str, KeywordClass] = {}

        if isinstance(value, _t.Mapping):
            try:
                if uri != value["$schema"]:
                    raise MetaschemaError('uri does not match the value of the "$schema" keyword')
            except KeyError as e:
                raise MetaschemaError('Missing "$schema" keyword') from e

            try:
                for vocab_uri, vocab_required in value["$vocabulary"].items():
                    if not isinstance(vocab_required, bool):
                        raise TypeError('"$vocabulary" values must be booleans')
                    try:
                        vocabulary = Vocabulary(vocab_uri, vocab_required)
                        self.kwclasses.update(vocabulary.kwclasses)
                    except VocabularyError as e:
                        if vocab_required:
                            raise MetaschemaError(f'The metaschema requires an unrecognised vocabulary "{vocab_uri}"') \
                                from e
            except (KeyError, AttributeError, TypeError) as e:
                raise MetaschemaError('Missing or invalid "$vocabulary" keyword') from e


class Vocabulary:

    _kwclasses: _t.Dict[str, _t.List[KeywordClass]] = {}
    _vcclass: _t.Dict[str, VocabularyClass] = {}
    _cache: _t.Dict[str, Vocabulary] = {}

    @classmethod
    def register(
            cls,
            uri: str,
            kwclasses: _t.Iterable[KeywordClass],
    ) -> None:
        validate_uri(uri)
        cls._kwclasses[uri] = []
        cls._vcclass[uri] = cls
        for kwclass in kwclasses:
            if issubclass(kwclass, Keyword):
                kwclass.vocabulary_uri = uri
                cls._kwclasses[uri] += [kwclass]

    @classmethod
    def load(cls, uri: str) -> Vocabulary:
        try:
            return cls._cache[uri]
        except KeyError as e:
            raise VocabularyError("Unrecognised vocabulary URI") from e

    def __new__(cls, uri: str, required: bool) -> Vocabulary:
        try:
            return object.__new__(Vocabulary._vcclass[uri])
        except KeyError as e:
            raise VocabularyError("Unrecognised vocabulary URI") from e

    def __init__(self, uri: str, required: bool) -> None:
        self.uri: str = uri
        self.required: bool = required
        self.kwclasses: _t.Dict[str, KeywordClass] = {
            kwclass.__keyword__: kwclass for kwclass in self._kwclasses[uri]
        }
        self._cache[uri] = self


VocabularyClass = _t.Type[Vocabulary]


class FormatVocabulary(Vocabulary):

    _fmtclasses: _t.Dict[str, _t.List[FormatClass]] = {}
    _assertfmt: _t.Dict[str, _t.Optional[bool]] = {}

    @classmethod
    def register(
            cls,
            uri: str,
            kwclasses: _t.Iterable[KeywordClass],
            fmtclasses: _t.Iterable[FormatClass] = (),
            assert_: bool = None,
    ) -> None:
        super().register(uri, kwclasses)
        cls._fmtclasses[uri] = []
        cls._assertfmt[uri] = assert_
        for fmtclass in fmtclasses:
            if issubclass(fmtclass, Format):
                cls._fmtclasses[uri] += [fmtclass]

    @classmethod
    def load(cls, uri: str) -> FormatVocabulary:
        vocab = super().load(uri)
        if isinstance(vocab, FormatVocabulary):
            return vocab
        raise VocabularyError(f'The vocabulary identified by "{uri}" does not support formats')

    def __init__(self, uri: str, required: bool) -> None:
        super().__init__(uri, required)
        assert_ = force_assert if (force_assert := self._assertfmt[uri]) is not None else required
        self.formats: _t.Dict[str, Format] = {
            fmtclass.__attr__: fmtclass(assert_)
            for fmtclass in self._fmtclasses[uri]
        }


class Format:

    __attr__: str = ...
    __types__: _t.Union[str, _t.Tuple[str]] = "string"

    def __init__(self, assert_: bool) -> None:
        self.assert_: bool = assert_

    def evaluate(self, instance: JSON) -> FormatResult:
        raise NotImplementedError


@dataclasses.dataclass
class FormatResult:
    valid: bool
    error: _t.Optional[str] = None


FormatClass = _t.Type[Format]
