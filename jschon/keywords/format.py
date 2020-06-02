import typing as _t

from jschon.json import JSON
from jschon.schema import Keyword, KeywordResult, Schema, Format, FormatVocabulary
from jschon.utils import tuplify

__all__ = [
    'FormatKeyword',
]


class FormatKeyword(Keyword):
    __keyword__ = "format"
    __schema__ = {"type": "string"}

    def __init__(
            self,
            superschema: Schema,
            value: str,
    ) -> None:
        super().__init__(superschema, value)
        vocabulary = FormatVocabulary.load(self.vocabulary_uri)
        self.format_: _t.Optional[Format] = vocabulary.formats.get(self.value)

    @property
    def assert_(self) -> bool:
        return self.format_.assert_ if self.format_ else False

    def evaluate(self, instance: JSON) -> KeywordResult:
        result = KeywordResult(
            valid=True,
            annotation=self.value,
        )
        if self.format_ and isinstance(instance, tuple(JSON.typemap[t] for t in tuplify(self.format_.__types__))):
            fmtresult = self.format_.evaluate(instance)
            if not fmtresult.valid:
                result.valid = False
                result.error = f'The text does not conform to the "{self.value}" format: {fmtresult.error}'

        return result
