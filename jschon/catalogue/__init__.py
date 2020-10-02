import json
import pathlib
from os import PathLike
from typing import Dict

from jschon.exceptions import CatalogueError
from jschon.types import AnyJSONCompatible
from jschon.uri import URI

__all__ = [
    'Catalogue',
]


class Catalogue:
    _dirs: Dict[URI, PathLike] = {}

    @classmethod
    def add_local(cls, base_uri: URI, base_dir: PathLike) -> None:
        if not pathlib.Path(base_dir).is_dir():
            raise CatalogueError(f"'{base_dir}' is not a directory")

        cls._dirs[base_uri] = base_dir

    @classmethod
    def load(cls, uri: URI) -> AnyJSONCompatible:
        uristr = str(uri)
        for base_uri, base_dir in cls._dirs.items():
            if uristr.startswith(str(base_uri)):
                filepath = pathlib.Path(base_dir) / uristr[len(base_uri):]
                with open(filepath) as f:
                    return json.load(f)

        raise CatalogueError(f"File not found for '{uri}'")
