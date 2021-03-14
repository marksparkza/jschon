import pathlib
from os import PathLike
from typing import Dict, Optional

from jschon.exceptions import CatalogueError
from jschon.json import AnyJSONCompatible
from jschon.jsonschema import KeywordClass
from jschon.uri import URI
from jschon.utils import load_json
from jschon.vocabulary import Vocabulary

__all__ = [
    'Catalogue',
]


class Catalogue:
    _directories: Dict[URI, PathLike] = {}
    _vocabularies: Dict[URI, Vocabulary] = {}

    @classmethod
    def add_directory(cls, base_uri: URI, base_dir: PathLike) -> None:
        if not pathlib.Path(base_dir).is_dir():
            raise CatalogueError(f"'{base_dir}' is not a directory")

        cls._directories[base_uri] = base_dir

    @classmethod
    def load_json(cls, uri: URI) -> AnyJSONCompatible:
        uristr = str(uri)
        for base_uri, base_dir in cls._directories.items():
            if uristr.startswith(str(base_uri)):
                filepath = pathlib.Path(base_dir) / uristr[len(base_uri):]
                try:
                    return load_json(filepath)
                except FileNotFoundError:
                    return load_json(filepath.with_suffix('.json'))

        raise CatalogueError(f"File not found for '{uri}'")

    @classmethod
    def create_vocabulary(cls, uri: URI, *kwclasses: KeywordClass) -> None:
        cls._vocabularies[uri] = Vocabulary(uri, *kwclasses)

    @classmethod
    def get_vocabulary(cls, uri: URI) -> Optional[Vocabulary]:
        return cls._vocabularies.get(uri)

    @classmethod
    def create_metaschema(cls, core_vocabulary: URI, *vocabularies: URI):
        pass
