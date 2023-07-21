from jschon.jsonpointer import JSONPointer
from jschon.vocabulary.format import format_validator


@format_validator('json-pointer', instance_types=('string',))
def validate_json_pointer(value: str) -> None:
    if not JSONPointer._json_pointer_re.fullmatch(value):
        raise ValueError
