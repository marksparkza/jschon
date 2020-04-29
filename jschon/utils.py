import rfc3986.exceptions
import rfc3986.validators


def validate_uri(uri: str) -> None:
    validator = rfc3986.validators.Validator()
    try:
        validator.validate(rfc3986.uri_reference(uri))
    except rfc3986.exceptions.ValidationError as e:
        raise ValueError(f"'{uri}' is not a valid URI") from e
