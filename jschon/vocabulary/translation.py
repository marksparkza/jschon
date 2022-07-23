from typing import Mapping, Optional, Sequence

from jschon.exceptions import JSONSchemaError
from jschon.json import JSON, JSONCompatible
from jschon.jsonpointer import JSONPointer, RelativeJSONPointer
from jschon.jsonschema import JSONSchema, Result
from jschon.translation import JSONTranslationSchema, TranslationResult
from jschon.vocabulary import Applicator, ApplicatorMixin, Keyword

__all__ = [
    'TranslationsKeyword',
    'T9nSchemeKeyword',
    'T9nTargetKeyword',
    'T9nConditionKeyword',
    'T9nConstKeyword',
    'T9nSourceKeyword',
    'T9nConcatKeyword',
    'T9nSepKeyword',
    'T9nFilterKeyword',
    'T9nCastKeyword',
    'T9nArrayKeyword',
    'T9nObjectKeyword',
]


class TranslationsKeyword(Keyword, ApplicatorMixin):
    key = "translations"

    @classmethod
    def jsonify(
            cls,
            parentschema: JSONSchema,
            key: str,
            value: Sequence[Mapping[str, JSONCompatible]],
    ) -> Optional[JSON]:
        return JSON(
            value,
            parent=parentschema,
            key=key,
            itemclass=JSONTranslationSchema,
            catalog=parentschema.catalog,
            session=parentschema.session,
        )

    def evaluate(self, instance: JSON, result: Result) -> None:
        for index, subschema in enumerate(self.json):
            with result(instance, str(index), cls=TranslationResult) as subresult:
                subschema.evaluate(instance, subresult)


class T9nSchemeKeyword(Keyword):
    key = "t9nScheme"
    static = True

    def __init__(self, parentschema: JSONTranslationSchema, value: str):
        super().__init__(parentschema, value)
        parentschema.t9n_scheme = value


class T9nTargetKeyword(Keyword):
    key = "t9nTarget"

    def evaluate(self, instance: JSON, result: TranslationResult) -> None:
        result.parent.t9n_target = JSONPointer(self.json.value)


class T9nConditionKeyword(Keyword, Applicator):
    key = "t9nCondition"

    def evaluate(self, instance: JSON, result: TranslationResult) -> None:
        self.json.evaluate(instance, result)
        if not result.valid:
            result.parent.fail()


class T9nConstKeyword(Keyword):
    key = "t9nConst"
    static = True

    def __init__(self, parentschema: JSONTranslationSchema, value: JSONCompatible):
        super().__init__(parentschema, value)
        parentschema.t9n_const = value


class T9nSourceKeyword(Keyword):
    key = "t9nSource"
    static = True

    def __init__(self, parentschema: JSONTranslationSchema, value: str):
        super().__init__(parentschema, value)
        if (source := RelativeJSONPointer(value)).index:
            raise JSONSchemaError('"t9nSource" must reference an instance, not an index')
        parentschema.t9n_source = source


class T9nConcatKeyword(Keyword):
    key = "t9nConcat"
    static = True

    def __init__(self, parentschema: JSONTranslationSchema, value: Sequence[str]):
        super().__init__(parentschema, value)
        parentschema.t9n_concat = tuple(RelativeJSONPointer(v) for v in value)


class T9nSepKeyword(Keyword):
    key = "t9nSep"
    static = True

    def __init__(self, parentschema: JSONTranslationSchema, value: str):
        super().__init__(parentschema, value)
        parentschema.t9n_sep = value


class T9nFilterKeyword(Keyword):
    key = "t9nFilter"
    static = True

    def __init__(self, parentschema: JSONTranslationSchema, value: str):
        super().__init__(parentschema, value)
        parentschema.t9n_filter = value


class T9nCastKeyword(Keyword):
    key = "t9nCast"
    static = True

    def __init__(self, parentschema: JSONTranslationSchema, value: str):
        super().__init__(parentschema, value)
        parentschema.t9n_cast = value


class T9nArrayKeyword(Keyword, ApplicatorMixin):
    key = "t9nArray"
    depends_on = "t9nCondition",

    def __init__(self, parentschema: JSONTranslationSchema, value: Mapping[str, JSONCompatible]):
        super().__init__(parentschema, value)
        parentschema.t9n_leaf = False

    @classmethod
    def jsonify(
            cls,
            parentschema: JSONTranslationSchema,
            key: str,
            value: Mapping[str, JSONCompatible],
    ) -> Optional[JSON]:
        return JSONTranslationSchema(
            value,
            parent=parentschema,
            key=key,
            catalog=parentschema.catalog,
            session=parentschema.session,
            scheme=parentschema.t9n_scheme,
        )

    def evaluate(self, instance: JSON, result: TranslationResult) -> None:
        if (condition := result.sibling(instance, "t9nCondition")) and not condition.valid:
            return

        scheme = self.parentschema.t9n_scheme
        array_path = result.parent.t9n_target
        result.init_array(scheme, array_path)

        if instance.type == 'array':
            for item in instance:
                index = result.next_array_index(scheme, array_path)
                result.t9n_target = array_path / str(index)
                self.json.evaluate(item, result)
        else:
            index = result.next_array_index(scheme, array_path)
            result.t9n_target = array_path / str(index)
            self.json.evaluate(instance, result)


class T9nObjectKeyword(Keyword, ApplicatorMixin):
    key = "t9nObject"
    depends_on = "t9nCondition",

    def __init__(self, parentschema: JSONTranslationSchema, value: Mapping[str, JSONCompatible]):
        super().__init__(parentschema, value)
        parentschema.t9n_leaf = False

    @classmethod
    def jsonify(
            cls,
            parentschema: JSONTranslationSchema,
            key: str,
            value: Mapping[str, JSONCompatible],
    ) -> Optional[JSON]:
        return JSON(
            value,
            parent=parentschema,
            key=key,
            itemclass=JSONTranslationSchema,
            catalog=parentschema.catalog,
            session=parentschema.session,
            scheme=parentschema.t9n_scheme,
        )

    def evaluate(self, instance: JSON, result: TranslationResult) -> None:
        if (condition := result.sibling(instance, "t9nCondition")) and not condition.valid:
            return

        scheme = self.parentschema.t9n_scheme
        object_path = result.parent.t9n_target
        result.init_object(scheme, object_path)

        for name, subschema in self.json.items():
            with result(instance, name) as subresult:
                subresult.t9n_target = object_path / name
                subschema.evaluate(instance, subresult)
