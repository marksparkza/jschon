import json
import pathlib
from os import PathLike
from typing import Dict

import rfc3986.exceptions
import rfc3986.validators
from rfc3986 import URIReference

from jschon.exceptions import CatalogueError
from jschon.types import AnyJSONCompatible

__all__ = [
    'Catalogue',
]


class Catalogue:
    _dirs: Dict[URIReference, PathLike] = {}

    @classmethod
    def add_local(cls, base_uri: URIReference, base_dir: PathLike) -> None:
        validator = rfc3986.validators.Validator().require_presence_of('scheme')
        try:
            validator.validate(base_uri)
        except rfc3986.exceptions.ValidationError as e:
            raise ValueError(f"{base_uri=} is not a valid URI or does not contain a scheme") from e

        if base_uri != base_uri.normalize():
            raise ValueError(f"{base_uri=} is not normalized")

        if not pathlib.Path(base_dir).is_dir():
            raise ValueError(f"{base_dir=} is not a directory")

        cls._dirs[base_uri] = base_dir

    @classmethod
    def load(cls, uri: URIReference) -> AnyJSONCompatible:
        uristr = uri.unsplit()
        for base_uri, base_dir in cls._dirs.items():
            if uristr.startswith((base_uristr := base_uri.unsplit())):
                filepath = pathlib.Path(base_dir) / uristr[len(base_uristr):]
                with open(filepath) as f:
                    return json.load(f)

        raise CatalogueError(f"File not found for '{uristr}'")
