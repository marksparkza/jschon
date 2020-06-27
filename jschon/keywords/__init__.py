import typing as _t

from jschon.json import JSON
from jschon.schema import Keyword, Schema, KeywordResult
from jschon.types import SchemaCompatible


class ApplicatorKeyword(Keyword):

    def __init__(
            self,
            superschema: Schema,
            value: _t.Union['SchemaCompatible', _t.Sequence['SchemaCompatible']],
    ) -> None:
        super().__init__(superschema, value)
        self.subschema: _t.Optional[Schema] = None
        self.subschemas: _t.Optional[_t.Sequence[Schema]] = None

        if isinstance(value, SchemaCompatible):
            self.subschema = Schema(
                value,
                location=self.location,
                superkeyword=self,
                metaschema_uri=superschema.metaschema.uri,
            )
        elif isinstance(value, _t.Sequence):
            self.subschemas = [
                Schema(
                    item,
                    location=self.location / str(index),
                    superkeyword=self,
                    metaschema_uri=superschema.metaschema.uri,
                )
                for index, item in enumerate(value)
            ]
        else:
            raise TypeError(f"Expecting one of {SchemaCompatible}, or a sequence thereof")

    def evaluate(self, instance: JSON) -> _t.Optional[KeywordResult]:
        raise NotImplementedError


class PropertyApplicatorKeyword(Keyword):

    def __init__(
            self,
            superschema: Schema,
            value: _t.Mapping[str, 'SchemaCompatible'],
    ) -> None:
        super().__init__(superschema, value)
        if not isinstance(value, _t.Mapping):
            raise TypeError("Expecting a mapping type")

        self.subschemas: _t.Mapping[str, Schema] = {
            name: Schema(
                item,
                location=self.location / name,
                superkeyword=self,
                metaschema_uri=superschema.metaschema.uri,
            )
            for name, item in value.items()
        }

    def evaluate(self, instance: JSON) -> _t.Optional[KeywordResult]:
        raise NotImplementedError
