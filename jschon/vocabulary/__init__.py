from __future__ import annotations

import re
import inspect
from typing import Any, Dict, Mapping, Optional, Sequence, TYPE_CHECKING, Tuple, Type

from jschon.json import JSON, JSONCompatible
from jschon.jsonschema import JSONSchema, Result
from jschon.exceptions import JSONSchemaError
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
    _CORE_VOCAB_RE = r'https://json-schema\.org/draft/[^/]+/vocab/core$'

    def __init__(
            self,
            catalog: Catalog,
            value: Mapping[str, JSONCompatible],
            default_core_vocabulary: Vocabulary = None,
            *default_vocabularies: Vocabulary,
            **kwargs: Any,
    ):
        """Initialize a :class:`Metaschema` instance from the given
        schema-compatible `value`.

        :param catalog: catalog instance
        :param value: a schema-compatible Python object
        :param default_core_vocabulary: the metaschema's
            core :class:`~jschon.vocabulary.Vocabulary`, used in the absence
            of a ``"$vocabulary"`` keyword in the metaschema JSON file, or
            if a known core vocabulary is not present under ``"$vocabulary"``
        :param default_vocabulary: default :class:`~jschon.vocabulary.Vocabulary`
            instances, used in the absence of a ``"$vocabulary"`` keyword in the
            metaschema JSON file
        :param kwargs: additional keyword arguments to pass through to the
            :class:`~jschon.jsonschema.JSONSchema` constructor

        :raise JSONSchemaError: if no core vocabulary can be determined
        :raise CatalogError: if the created metaschema is not valid
        """
        self.default_vocabularies: Tuple[Vocabulary, ...] = default_vocabularies
        self.core_vocabulary: Vocabulary = default_core_vocabulary

        if vocabularies := value.get("$vocabulary"):
            possible_cores = list(filter(
                lambda v: re.match(self._CORE_VOCAB_RE, v),
                vocabularies,
            ))
            if len(possible_cores) == 1:
                self.core_vocabulary = catalog.get_vocabulary(URI(possible_cores[0]))
            else:
                raise JSONSchemaError(
                    'Cannot determine unique known core vocabulary from '
                    f'candidates "{vocabularies.keys()}"'
                )
        if self.core_vocabulary is None:
            raise JSONSchemaError(
                f'No core vocabulary in "$vocabulary": {value}, and no default provided'
            )

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

    def __repr__(self) -> str:
        """Return `repr(self)`."""
        return f'{self.__class__.__name__}({self.uri!r})'


class Keyword:
    key: str = ...
    """The keyword name as it appears in a schema object."""

    instance_types: Tuple[str, ...] = "null", "boolean", "number", "string", "array", "object",
    """The types of instance that the keyword can evaluate."""

    depends_on: Tuple[str, ...] = ()
    """Keywords that must be evaluated before this keyword can be evaluated."""

    static: bool = False
    """`static = True` (equivalent to `instance_types = ()`) indicates that the keyword
    does not ever evaluate any instance."""

    def __init__(self, parentschema: JSONSchema, value: JSONCompatible):
        for base_cls in inspect.getmro(self.__class__):
            if issubclass(base_cls, SubschemaMixin):
                if (kwjson := base_cls.jsonify(parentschema, self.key, value)) is not None:
                    break
        else:
            kwjson = JSON(value, parent=parentschema, key=self.key)

        self.json: JSON = kwjson
        self.parentschema: JSONSchema = parentschema

    def evaluate(self, instance: JSON, result: Result) -> None:
        pass

    def __str__(self) -> str:
        return f'{self.json.path}: {self.json}'


KeywordClass = Type[Keyword]


class _UnknownKeyword(Keyword):
    def evaluate(self, instance: JSON, result: Result) -> None:
        result.annotate(self.json.value)
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
