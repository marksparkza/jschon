import ipaddress
import pprint

from jschon import JSON, JSONSchema, create_catalog
from jschon.vocabulary.format import format_validator


# register an 'ipv4' format validator
@format_validator('ipv4', instance_types=('string',))
def validate_ipv4(value: str) -> None:
    ipaddress.IPv4Address(value)  # raises ValueError for an invalid IPv4 address


# register an 'ipv6' format validator
@format_validator('ipv6', instance_types=('string',))
def validate_ipv6(value: str) -> None:
    ipaddress.IPv6Address(value)  # raises ValueError for an invalid IPv6 address


# initialize the catalog, with JSON Schema 2020-12 vocabulary support
catalog = create_catalog('2020-12')

# enable validation with the 'ipv4' and 'ipv6' format validators
catalog.enable_formats('ipv4', 'ipv6')

# create a schema for validating an array of IP addresses
schema = JSONSchema({
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://example.com/schema",
    "type": "array",
    "items": {
        "type": "string",
        "anyOf": [
            {"format": "ipv4"},
            {"format": "ipv6"}
        ]
    }
})

# evaluate a valid array
valid_result = schema.evaluate(JSON(['127.0.0.1', '::1']))

# evaluate an invalid array
invalid_result = schema.evaluate(JSON(['127.0.1', '::1']))

# print output for the valid case
print('Valid case output:')
pprint.pp(valid_result.output('basic'))

# print output for the invalid case
print('Invalid case output:')
pprint.pp(invalid_result.output('basic'))
