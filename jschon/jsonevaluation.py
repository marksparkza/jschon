from typing import Dict, Any

from jschon.json import JSON
from jschon.jsonschema import JSONSchema, Scope

__all__ = [
    'JSONEvaluation',
]


class JSONEvaluation:
    """The JSONEvaluation class represents the result of evaluating
    a JSON instance against a JSON schema. It encapsulates the schema
    evaluation and scope processing logic and provides output formatting.

    Instantiating JSONEvaluation causes evaluation to run; the evaluation
    result may then be retrieved in various formats from the instance
    properties.
    """

    def __init__(self, instance: JSON, schema: JSONSchema):
        self.instance: JSON = instance
        self.schema: JSONSchema = schema
        self.scope: Scope = self.schema.evaluate(self.instance)
        self._flag = None
        self._basic = None
        self._detailed = None
        self._verbose = None

    @property
    def flag(self) -> Dict[str, Any]:
        if self._flag is None:
            self._flag = {
                "valid": self.scope.valid
            }

        return self._flag

    @property
    def basic(self) -> Dict[str, Any]:
        if self._basic is None:
            self._basic = {
                "valid": self.scope.valid
            }
            if self._basic["valid"]:
                self._basic["annotations"] = []
                for annotation in self.scope.collect_annotations(self.instance):
                    self._basic["annotations"] += [{
                        "instanceLocation": str(annotation.instance_path),
                        "keywordLocation": str(annotation.evaluation_path),
                        "absoluteKeywordLocation": str(annotation.absolute_uri),
                        "annotation": annotation.value,
                    }]
            else:
                self._basic["errors"] = []
                for error in self.scope.collect_errors():
                    self._basic["errors"] += [{
                        "instanceLocation": str(error.instance_path),
                        "keywordLocation": str(error.evaluation_path),
                        "absoluteKeywordLocation": str(error.absolute_uri),
                        "error": error.message,
                    }]

        return self._basic

    @property
    def detailed(self) -> Dict[str, Any]:
        raise NotImplementedError

    @property
    def verbose(self) -> Dict[str, Any]:
        raise NotImplementedError
