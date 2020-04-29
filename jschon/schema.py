from __future__ import annotations

import dataclasses
import json
import pathlib
import typing as _t

from jschon.exceptions import SchemaError, MetaschemaError
from jschon.json import JSON
from jschon.pointer import Pointer
from jschon.types import JSONCompatible, SchemaCompatible
from jschon.utils import validate_uri


class Schema:

    def __init__(
            self,
            value: SchemaCompatible,
            *,
            location: Pointer = None,
            metaschema_uri: str = None,
            is_metaschema: bool = False,
    ) -> None:
        if not isinstance(value, SchemaCompatible):
            raise TypeError(f"value must be one of {SchemaCompatible}")

        self.value: SchemaCompatible = value
        self.location: Pointer = location or Pointer('')
        self.is_root: bool = self.location.is_root()
        self.metaschema: _t.Optional[Metaschema] = None
        self.keywords: _t.List[Keyword] = []

        if metaschema_uri is not None:
            validate_uri(metaschema_uri)

        if isinstance(value, _t.Mapping):
            if metaschema_uri is None and self.is_root:
                metaschema_uri = value.get("$schema")
            if metaschema_uri is None:
                raise SchemaError("Metaschema URI not specified")

            self.metaschema = Metaschema.load(metaschema_uri)
            if self.is_root and not is_metaschema:
                if not (result := Schema(self.metaschema.value, is_metaschema=True).evaluate(JSON(value))).valid:
                    errors = "\n".join(result.errors())
                    raise SchemaError(f"The schema is invalid against its metaschema:\n{errors}")

            self.keywords = [
                kwclass(self, kwvalue)
                for kw, kwvalue in value.items()
                if (kwclass := self.metaschema.kwclasses.get(kw))
            ]

    def evaluate(self, instance: JSON) -> SchemaResult:
        result = SchemaResult(
            valid=self.value if isinstance(self.value, bool) else True,
            annotation=None,
            error=None,
            subresults=[],
            keyword_location=self.location,
            instance_location=instance.location,
        )
        for keyword in self.keywords:
            if isinstance(instance, keyword.__types__):
                if not (kwresult := keyword.evaluate(instance)).valid:
                    result.valid = False
                result.subresults += [SchemaResult(
                    valid=kwresult.valid,
                    annotation=kwresult.annotation if kwresult.valid else None,
                    error=kwresult.error if not kwresult.valid else None,
                    subresults=kwresult.subresults,
                    keyword_location=keyword.location,
                    instance_location=instance.location,
                )]
        return result


@dataclasses.dataclass
class SchemaResult:
    valid: bool
    annotation: _t.Optional['JSONCompatible']
    error: _t.Optional[str]
    subresults: _t.Optional[_t.List[SchemaResult]]
    keyword_location: Pointer
    instance_location: Pointer

    def errors(self) -> _t.Iterator[str]:
        if self.error:
            yield f"{self.keyword_location=}, {self.instance_location=}, {self.error=}"
        if self.subresults:
            for subresult in self.subresults:
                yield from subresult.errors()


JSONClass = _t.Type[JSON]


class Keyword:

    __keyword__: str = ...
    __schema__: _t.Union[bool, dict] = ...
    __types__: _t.Union[JSONClass, _t.Tuple[JSONClass]] = ...

    def __init__(
            self,
            superschema: Schema,
            value: JSONCompatible,
    ) -> None:
        if not isinstance(value, JSONCompatible):
            raise TypeError(f"value must be one of {JSONCompatible}")

        self.superschema: Schema = superschema
        self.location: Pointer = superschema.location + Pointer(f'/{self.__keyword__}')
        self.value: JSONCompatible = value

        self.subschema: _t.Optional[Schema] = None
        self.subschemas: _t.Optional[_t.Union[_t.Sequence[Schema], _t.Mapping[str, Schema]]] = None

    def evaluate(self, instance: JSON) -> KeywordResult:
        raise NotImplementedError


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
        validate_uri(uri)
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
                    validate_uri(vocab_uri)
                    if not isinstance(vocab_required, bool):
                        raise ValueError
                    if (kwclasses := Vocabulary.registry.get(vocab_uri)) is None and vocab_required:
                        raise MetaschemaError(f'The metaschema requires an unrecognised vocabulary "{vocab_uri}"')

                    self.kwclasses.update(kwclasses or {})

            except (KeyError, AttributeError, TypeError, ValueError) as e:
                raise MetaschemaError('Missing or invalid "$vocabulary" keyword') from e


class Vocabulary:

    registry: _t.Dict[str, _t.Dict[str, KeywordClass]] = {}

    @classmethod
    def register(cls, uri: str, kwclasses: _t.Iterable[KeywordClass]) -> None:
        validate_uri(uri)
        cls.registry[uri] = {c.__keyword__: c for c in kwclasses if issubclass(c, Keyword)}
