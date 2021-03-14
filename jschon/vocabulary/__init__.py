from typing import Dict

from jschon.jsonschema import KeywordClass
from jschon.uri import URI

__all__ = [
    'Vocabulary',
]


class Vocabulary:

    def __init__(self, uri: URI, *kwclasses: KeywordClass):
        self.uri: URI = uri
        self.kwclasses: Dict[str, KeywordClass] = {
            kwclass.__keyword__: kwclass for kwclass in kwclasses
        }
