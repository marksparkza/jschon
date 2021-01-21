import ipaddress
import re

import dateutil.parser
import email_validator
import idna

from jschon.exceptions import JSONPointerError, URIError
from jschon.json import JSONString
from jschon.jsonpointer import JSONPointer
from jschon.jsonschema import Format, FormatResult
from jschon.uri import URI

__all__ = [
    'DateTimeFormat',
    'DateFormat',
    'TimeFormat',
    'DurationFormat',
    'EmailFormat',
    'IDNEmailFormat',
    'HostnameFormat',
    'IDNHostnameFormat',
    'IPv4Format',
    'IPv6Format',
    'URIFormat',
    'URIReferenceFormat',
    'IRIFormat',
    'IRIReferenceFormat',
    'UUIDFormat',
    'URITemplateFormat',
    'JSONPointerFormat',
    'RelativeJSONPointerFormat',
    'RegexFormat',
]


class DateTimeFormat(Format):
    __attr__ = "date-time"

    def evaluate(self, instance: JSONString) -> FormatResult:
        try:
            dateutil.parser.isoparse(instance.value)
        except ValueError as e:
            return FormatResult(valid=False, error=str(e))

        return FormatResult(valid=True)


class DateFormat(Format):
    __attr__ = "date"

    def evaluate(self, instance: JSONString) -> FormatResult:
        try:
            dateutil.parser.isoparser().parse_isodate(instance.value)
        except ValueError as e:
            return FormatResult(valid=False, error=str(e))

        return FormatResult(valid=True)


class TimeFormat(Format):
    __attr__ = "time"

    def evaluate(self, instance: JSONString) -> FormatResult:
        try:
            dateutil.parser.isoparser().parse_isotime(instance.value)
        except ValueError as e:
            return FormatResult(valid=False, error=str(e))

        return FormatResult(valid=True)


class DurationFormat(Format):
    __attr__ = "duration"

    def evaluate(self, instance: JSONString) -> FormatResult:
        raise NotImplementedError


class EmailFormat(Format):
    __attr__ = "email"

    def evaluate(self, instance: JSONString) -> FormatResult:
        try:
            email_validator.validate_email(
                instance.value,
                allow_smtputf8=False,
                check_deliverability=False,
            )
        except email_validator.EmailNotValidError as e:
            return FormatResult(valid=False, error=str(e))

        return FormatResult(valid=True)


class IDNEmailFormat(Format):
    __attr__ = "idn-email"

    def evaluate(self, instance: JSONString) -> FormatResult:
        try:
            email_validator.validate_email(
                instance.value,
                allow_smtputf8=True,
                check_deliverability=False,
            )
        except email_validator.EmailNotValidError as e:
            return FormatResult(valid=False, error=str(e))

        return FormatResult(valid=True)


class HostnameFormat(Format):
    __attr__ = "hostname"

    def evaluate(self, instance: JSONString) -> FormatResult:
        try:
            instance.value.encode('ascii')
            idna.encode(instance.value)
        except (UnicodeEncodeError, idna.IDNAError) as e:
            return FormatResult(valid=False, error=str(e))

        return FormatResult(valid=True)


class IDNHostnameFormat(Format):
    __attr__ = "idn-hostname"

    def evaluate(self, instance: JSONString) -> FormatResult:
        try:
            idna.encode(instance.value)
        except idna.IDNAError as e:
            return FormatResult(valid=False, error=str(e))

        return FormatResult(valid=True)


class IPv4Format(Format):
    __attr__ = "ipv4"

    def evaluate(self, instance: JSONString) -> FormatResult:
        try:
            ipaddress.IPv4Address(instance.value)
        except ipaddress.AddressValueError as e:
            return FormatResult(valid=False, error=str(e))

        return FormatResult(valid=True)


class IPv6Format(Format):
    __attr__ = "ipv6"

    def evaluate(self, instance: JSONString) -> FormatResult:
        try:
            ipaddress.IPv6Address(instance.value)
        except ipaddress.AddressValueError as e:
            return FormatResult(valid=False, error=str(e))

        return FormatResult(valid=True)


class URIFormat(Format):
    __attr__ = "uri"

    def evaluate(self, instance: JSONString) -> FormatResult:
        uri = URI(instance.value)
        try:
            uri.validate(require_scheme=True)
        except URIError as e:
            return FormatResult(valid=False, error=str(e))

        return FormatResult(valid=True)


class URIReferenceFormat(Format):
    __attr__ = "uri-reference"

    def evaluate(self, instance: JSONString) -> FormatResult:
        uri = URI(instance.value)
        try:
            uri.validate()
        except URIError as e:
            return FormatResult(valid=False, error=str(e))

        return FormatResult(valid=True)


class IRIFormat(Format):
    __attr__ = "iri"

    def evaluate(self, instance: JSONString) -> FormatResult:
        raise NotImplementedError


class IRIReferenceFormat(Format):
    __attr__ = "iri-reference"

    def evaluate(self, instance: JSONString) -> FormatResult:
        raise NotImplementedError


class UUIDFormat(Format):
    __attr__ = "uuid"

    def evaluate(self, instance: JSONString) -> FormatResult:
        raise NotImplementedError


class URITemplateFormat(Format):
    __attr__ = "uri-template"

    def evaluate(self, instance: JSONString) -> FormatResult:
        raise NotImplementedError


class JSONPointerFormat(Format):
    __attr__ = "json-pointer"

    def evaluate(self, instance: JSONString) -> FormatResult:
        try:
            JSONPointer(instance.value)
        except JSONPointerError as e:
            return FormatResult(valid=False, error=str(e))

        return FormatResult(valid=True)


class RelativeJSONPointerFormat(Format):
    __attr__ = "relative-json-pointer"

    def evaluate(self, instance: JSONString) -> FormatResult:
        raise NotImplementedError


class RegexFormat(Format):
    __attr__ = "regex"

    def evaluate(self, instance: JSONString) -> FormatResult:
        try:
            re.compile(instance.value)
        except re.error as e:
            return FormatResult(valid=False, error=str(e))

        return FormatResult(valid=True)
