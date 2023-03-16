from __future__ import annotations

import inspect
from typing import Any, Dict, Mapping, Optional, Sequence, TYPE_CHECKING, Tuple, Type

from jschon.json import JSON, JSONCompatible
from jschon.jsonschema import JSONSchema, Result
from jschon.uri import URI

if TYPE_CHECKING:
    from jschon.catalog import Catalog

__all__ = [
    'Metaschema',
    'Vocabulary',
    'Keyword',
    'KeywordClass',
    'SubschemaMixin',
    'Subschema',
    'ArrayOfSubschemas',
    'ObjectOfSubschemas',
]


class Metaschema(JSONSchema):
    """A metaschema declares the set of vocabularies that are available
    to any schema which references it, and provides any such schema with
    its :class:`Keyword` classes.
    
    :class:`Metaschema` is itself a subclass of :class:`~jschon.jsonschema.JSONSchema`,
    and may be used to validate any referencing schema.
    """

    def __init__(
            self,
            catalog: Catalog,
            value: Mapping[str, JSONCompatible],
            core_vocabulary: Vocabulary,
            *default_vocabularies: Vocabulary,
            **kwargs: Any,
    ):
        self.core_vocabulary: Vocabulary = core_vocabulary
        self.default_vocabularies: Tuple[Vocabulary, ...] = default_vocabularies
        self.kwclasses: Dict[str, KeywordClass] = {}
        super().__init__(value, catalog=catalog, cacheid='__meta__', **kwargs)

    def _bootstrap(self, value: Mapping[str, JSONCompatible]) -> None:
        super()._bootstrap(value)
        self.kwclasses.update(self.core_vocabulary.kwclasses)
        if "$vocabulary" not in value:
            for vocabulary in self.default_vocabularies:
                self.kwclasses.update(vocabulary.kwclasses)

    def get_kwclass(self, key: str) -> KeywordClass:
        """Return the :class:`Keyword` class this metaschema uses for the given key.
        If the key is not recognized, a subclass of an internal :class:`Keyword`
        subclass that treats the keyword as a simple annotation is automatically
        created, associated with the key, and returned."""

        try:
            return self.kwclasses[key]
        except KeyError:
            unknown_class = type(
                f'UnknownKeyword{key[0].upper() + key[1:]}',
                (_UnknownKeyword,),
                dict(key=key),
            )
            self.kwclasses[key] = unknown_class
            return unknown_class


class Vocabulary:
    """A vocabulary declares a set of keywords that may be used in the
    evaluation of JSON documents, and provides a runtime implementation
    (in the form of a :class:`Keyword` class) for each of those keywords."""

    def __init__(self, uri: URI, *kwclasses: KeywordClass):
        self.uri: URI = uri
        self.kwclasses: Dict[str, KeywordClass] = {
            kwclass.key: kwclass for kwclass in kwclasses
        }


class Keyword:
    key: str = ...

    instance_types: Tuple[str, ...] = "null", "boolean", "integer", "number", "string", "array", "object",
    """The types of instance that the keyword can evaluate."""

    depends_on: Tuple[str, ...] = ()
    """Keywords that must be evaluated before this keyword can be evaluated."""

    static: bool = False

    def __init__(self, parentschema: JSONSchema, value: JSONCompatible):
        for base_cls in inspect.getmro(self.__class__):
            if issubclass(base_cls, SubschemaMixin):
                if (kwjson := base_cls.jsonify(parentschema, self.key, value)) is not None:
                    break
        else:
            kwjson = JSON(value, parent=parentschema, key=self.key)

        self.json: JSON = kwjson
        self.parentschema: JSONSchema = parentschema

    def can_evaluate(self, instance: JSON) -> bool:
        if instance.type in self.instance_types:
            return True

        if instance.type == "number" and "integer" in self.instance_types:
            return instance.data == int(instance.data)

        return False

    def evaluate(self, instance: JSON, result: Result) -> None:
        pass

    def __str__(self) -> str:
        return f'{self.json.path}: {self.json}'


KeywordClass = Type[Keyword]


class _UnknownKeyword(Keyword):
    def evaluate(self, instance: JSON, result: Result) -> None:
        result.annotate(self.json.data)
        result.noassert()


class SubschemaMixin:
    @classmethod
    def jsonify(cls, parentschema: JSONSchema, key: str, value: JSONCompatible) -> Optional[JSON]:
        raise NotImplementedError


class Subschema(SubschemaMixin):
    """A :class:`~Keyword` class mixin that sets up a subschema for
    a keyword."""

    @classmethod
    def jsonify(cls, parentschema: JSONSchema, key: str, value: JSONCompatible) -> Optional[JSON]:
        if isinstance(value, (bool, Mapping)):
            return JSONSchema(
                value,
                parent=parentschema,
                key=key,
                catalog=parentschema.catalog,
                cacheid=parentschema.cacheid,
            )


class ArrayOfSubschemas(SubschemaMixin):
    """A :class:`~Keyword` class mixin that sets up an array of subschemas
    for a keyword."""

    @classmethod
    def jsonify(cls, parentschema: JSONSchema, key: str, value: JSONCompatible) -> Optional[JSON]:
        if isinstance(value, Sequence):
            return JSON(
                value,
                parent=parentschema,
                key=key,
                itemclass=JSONSchema,
                catalog=parentschema.catalog,
                cacheid=parentschema.cacheid,
            )


class ObjectOfSubschemas(SubschemaMixin):
    """A :class:`~Keyword` class mixin that sets up property-based subschemas
    for a keyword."""

    @classmethod
    def jsonify(cls, parentschema: JSONSchema, key: str, value: JSONCompatible) -> Optional[JSON]:
        if isinstance(value, Mapping):
            return JSON(
                value,
                parent=parentschema,
                key=key,
                itemclass=JSONSchema,
                catalog=parentschema.catalog,
                cacheid=parentschema.cacheid,
            )
