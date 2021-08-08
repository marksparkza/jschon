from __future__ import annotations

from typing import Dict, Optional, Union, Tuple, Sequence, Mapping, Type, Any, TYPE_CHECKING

from jschon.json import JSON, AnyJSONCompatible
from jschon.jsonschema import JSONSchema, Scope
from jschon.uri import URI
from jschon.utils import tuplify

if TYPE_CHECKING:
    from jschon.catalog import Catalog

__all__ = [
    'Metaschema',
    'Vocabulary',
    'Keyword',
    'KeywordClass',
    'Applicator',
    'ArrayApplicator',
    'PropertyApplicator',
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
            value: Mapping[str, AnyJSONCompatible],
            core_vocabulary: Vocabulary,
            *default_vocabularies: Vocabulary,
    ):
        self.core_vocabulary: Vocabulary = core_vocabulary
        self.default_vocabularies: Tuple[Vocabulary, ...] = default_vocabularies
        self.kwclasses: Dict[str, KeywordClass] = {}
        super().__init__(value, catalog=catalog, session='__meta__')

    def _bootstrap(self, value: Mapping[str, AnyJSONCompatible]) -> None:
        super()._bootstrap(value)
        self.kwclasses.update(self.core_vocabulary.kwclasses)
        if "$vocabulary" not in value:
            for vocabulary in self.default_vocabularies:
                self.kwclasses.update(vocabulary.kwclasses)


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
    types: Optional[Union[str, Tuple[str, ...]]] = None
    depends: Optional[Union[str, Tuple[str, ...]]] = None

    def __init__(self, parentschema: JSONSchema, value: AnyJSONCompatible):
        self.applicator_cls = None
        for applicator_cls in (Applicator, ArrayApplicator, PropertyApplicator):
            if isinstance(self, applicator_cls):
                if (kwjson := applicator_cls.jsonify(parentschema, self.key, value)) is not None:
                    self.applicator_cls = applicator_cls
                    break
        else:
            kwjson = JSON(value, parent=parentschema, key=self.key)

        self.json: JSON = kwjson
        self.parentschema: JSONSchema = parentschema

    def can_evaluate(self, instance: JSON) -> bool:
        if self.types is None or instance.type in (types := tuplify(self.types)):
            return True

        if instance.type == "number" and "integer" in types:
            return instance.value == int(instance.value)

        return False

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        pass

    def __str__(self) -> str:
        return f'{self.json.path}: {self.json}'


KeywordClass = Type[Keyword]


def _is_schema_compatible(value: Any) -> bool:
    return (isinstance(value, bool) or
            isinstance(value, Mapping) and all(isinstance(k, str) for k in value))


class Applicator:
    """A :class:`~Keyword` class mixin that sets up a subschema for
    an applicator keyword."""

    @classmethod
    def jsonify(cls, parentschema: JSONSchema, key: str, value: AnyJSONCompatible) -> Optional[JSONSchema]:
        if _is_schema_compatible(value):
            return JSONSchema(
                value,
                parent=parentschema,
                key=key,
                catalog=parentschema.catalog,
                session=parentschema.session,
            )


class ArrayApplicator:
    """A :class:`~Keyword` class mixin that sets up an array of subschemas
    for an applicator keyword."""

    @classmethod
    def jsonify(cls, parentschema: JSONSchema, key: str, value: AnyJSONCompatible) -> Optional[JSON]:
        if isinstance(value, Sequence) and all(_is_schema_compatible(v) for v in value):
            return JSON(
                value,
                parent=parentschema,
                key=key,
                itemclass=JSONSchema,
                catalog=parentschema.catalog,
                session=parentschema.session,
            )


class PropertyApplicator:
    """A :class:`~Keyword` class mixin that sets up property-based subschemas
    for an applicator keyword."""

    @classmethod
    def jsonify(cls, parentschema: JSONSchema, key: str, value: AnyJSONCompatible) -> Optional[JSON]:
        if isinstance(value, Mapping) and all(
                isinstance(k, str) and _is_schema_compatible(v)
                for k, v in value.items()
        ):
            return JSON(
                value,
                parent=parentschema,
                key=key,
                itemclass=JSONSchema,
                catalog=parentschema.catalog,
                session=parentschema.session,
            )
