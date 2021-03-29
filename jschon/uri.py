from __future__ import annotations

import rfc3986
import rfc3986.exceptions
import rfc3986.misc
import rfc3986.validators

from jschon.exceptions import URIError

__all__ = [
    'URI',
]


class URI:
    def __init__(self, value: str) -> None:
        self._uriref = rfc3986.uri_reference(value)

    def __str__(self) -> str:
        return self._uriref.unsplit()

    def __repr__(self) -> str:
        return f"URI({str(self)!r})"

    def __len__(self) -> int:
        return len(str(self))

    def __hash__(self) -> int:
        return hash(self._uriref)

    def __eq__(self, other) -> bool:
        if isinstance(other, URI):
            return self._uriref == other._uriref
        if other is None:
            return False
        return self._uriref.__eq__(other)

    @property
    def scheme(self) -> str:
        return self._uriref.scheme

    @property
    def authority(self) -> str:
        return self._uriref.authority

    @property
    def path(self) -> str:
        return self._uriref.path

    @property
    def query(self) -> str:
        return self._uriref.query

    @property
    def fragment(self) -> str:
        return self._uriref.fragment

    def is_absolute(self) -> bool:
        return self._uriref.is_absolute()

    def has_absolute_base(self) -> bool:
        return self.copy(fragment=False).is_absolute()

    def resolve(self, base_uri: URI) -> URI:
        """Produce a new URI by resolving self against the given base URI."""
        uri = object.__new__(URI)
        uri._uriref = self._uriref.resolve_with(base_uri._uriref)
        return uri

    def copy(
            self,
            scheme=True,
            authority=True,
            path=True,
            query=True,
            fragment=True,
    ) -> URI:
        """Produce a new URI composed of the specified components of self.

        - True => use existing
        - False/None => remove
        - Otherwise => replace
        """
        uri = object.__new__(URI)
        uri._uriref = self._uriref.copy_with(
            scheme=rfc3986.misc.UseExisting if scheme is True else None if scheme is False else scheme,
            authority=rfc3986.misc.UseExisting if authority is True else None if authority is False else authority,
            path=rfc3986.misc.UseExisting if path is True else None if path is False else path,
            query=rfc3986.misc.UseExisting if query is True else None if query is False else query,
            fragment=rfc3986.misc.UseExisting if fragment is True else None if fragment is False else fragment,
        )
        return uri

    def validate(
            self,
            require_scheme: bool = False,
            require_normalized: bool = False,
            allow_fragment: bool = True,
            allow_non_empty_fragment: bool = True,
    ) -> None:
        """Validate self.

        :raise URIError: if self fails validation
        """
        validator = rfc3986.validators.Validator()
        if require_scheme:
            validator = validator.require_presence_of('scheme')
        try:
            validator.validate(self._uriref)
        except rfc3986.exceptions.ValidationError as e:
            msg = f"'{self}' is not a valid URI"
            if require_scheme:
                msg += " or does not contain a scheme"
            raise URIError(msg) from e

        if require_normalized and self._uriref != self._uriref.normalize():
            raise URIError(f"'{self}' is not normalized")

        if not allow_fragment and self._uriref.fragment is not None:
            raise URIError(f"'{self}' has a fragment")

        if not allow_non_empty_fragment and self._uriref.fragment:
            raise URIError(f"'{self}' has a non-empty fragment")
