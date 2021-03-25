from jschon.json import JSON
from jschon.jsonschema import Keyword, Scope

__all__ = [
    'AnnotationKeyword',
]


class AnnotationKeyword(Keyword):

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        scope.annotate(instance, self.key, self.json.value)
        scope.noassert()
