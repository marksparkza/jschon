import pprint

from jschon import create_catalog, JSON, JSONSchema

# initialize the catalog, with JSON Schema 2020-12 vocabulary support
create_catalog('2020-12', default=True)

# create a schema to validate a JSON greeting object
schema = JSONSchema({
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://example.com/greeting",
    "type": "object",
    "properties": {
        "greeting": {"$ref": "#/$defs/greetingDefinition"}
    },
    "$defs": {
        "greetingDefinition": {
            "type": "string",
            "pattern": "^Hello, .+!$"
        }
    }
})

# validate the schema against its metaschema
schema_validity = schema.validate()
print(f'Schema validity check: {schema_validity.valid}')

# declare a valid JSON instance
valid_json = JSON({
    "greeting": "Hello, World!"
})

# declare an invalid JSON instance
invalid_json = JSON({
    "greeting": "Hi, World"
})

# evaluate the valid instance
valid_result = schema.evaluate(valid_json)

# evaluate the invalid instance
invalid_result = schema.evaluate(invalid_json)

# print output for the valid case
print(f'Valid JSON result: {valid_result.valid}')
print('Valid JSON basic output:')
pprint.pp(valid_result.output('basic'))

# print output for the invalid case
print(f'Invalid JSON result: {invalid_result.valid}')
print('Invalid JSON detailed output:')
pprint.pp(invalid_result.output('detailed'))
