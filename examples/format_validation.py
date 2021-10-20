import ipaddress
import pprint
import re

from jschon import create_catalog, JSON, JSONSchema


# define a "hostname" format validation function
def validate_hostname(value):
    hostname_regex = re.compile(
        r"^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$")
    if not hostname_regex.match(value):
        raise ValueError(f"'{value}' is not a valid hostname")


# create a catalog with support for JSON Schema version 2020-12
catalog = create_catalog('2020-12')

# register IP address and hostname format validators
catalog.add_format_validators({
    "ipv4": ipaddress.IPv4Address,
    "ipv6": ipaddress.IPv6Address,
    "hostname": validate_hostname,
})

# create a schema for validating an array of host records
hosts_schema = JSONSchema({
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://example.com/hosts-schema",
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "ipaddress": {
                "type": "string",
                "oneOf": [
                    {"format": "ipv4"},
                    {"format": "ipv6"}
                ]
            },
            "hostname": {
                "type": "string",
                "format": "hostname"
            }
        },
        "required": ["ipaddress", "hostname"]
    }
})

# declare a host record array containing valid IP addresses and hostnames
valid_host_records = JSON([
    {"ipaddress": "127.0.0.1", "hostname": "localhost"},
    {"ipaddress": "10.0.0.8", "hostname": "server.local"},
])

# declare a host record array containing some values that are invalid
# per the registered format validators
invalid_host_records = JSON([
    {"ipaddress": "127.0.0.1", "hostname": "~localhost"},
    {"ipaddress": "10.0.0", "hostname": "server.local"},
])

# evaluate the valid array
valid_result = hosts_schema.evaluate(valid_host_records)

# evaluate the invalid array
invalid_result = hosts_schema.evaluate(invalid_host_records)

# print output for the valid case
print(f'Valid array result: {valid_result.valid}')
print('Valid array basic output:')
pprint.pp(valid_result.output('basic'))

# print output for the invalid case
print(f'Invalid array result: {invalid_result.valid}')
print('Invalid array detailed output:')
pprint.pp(invalid_result.output('detailed'))
