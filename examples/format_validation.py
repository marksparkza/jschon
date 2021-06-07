import ipaddress
import re

from jschon import Catalogue, JSON, JSONSchema


# define a "hostname" format validation function
def validate_hostname(value):
    hostname_regex = re.compile(
        r"^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$")
    if not hostname_regex.match(value):
        raise ValueError(f"'{value}' is not a valid hostname")


# create a catalogue, initialized with the JSON Schema 2020-12 metaschema,
# and register IP address and hostname format validators
Catalogue.create_default_catalogue('2020-12').add_format_validators({
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

# a host record array containing valid IP addresses and hostnames
valid_host_records = JSON([
    {"ipaddress": "127.0.0.1", "hostname": "localhost"},
    {"ipaddress": "10.0.0.8", "hostname": "server.local"},
])

# a host record array containing some values that are invalid
# per the registered format validators
invalid_host_records = JSON([
    {"ipaddress": "127.0.0.1", "hostname": "~localhost"},
    {"ipaddress": "10.0.0", "hostname": "server.local"},
])

print(hosts_schema.evaluate(valid_host_records).valid)
# True

print(hosts_schema.evaluate(invalid_host_records).valid)
# False
