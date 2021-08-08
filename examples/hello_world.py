from jschon import create_catalog, JSON, JSONSchema
from pprint import pp

create_catalog('2020-12', default=True)

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
            "minLength": 10
        }
    }
})

valid_instance = JSON({
    "greeting": "Hello, World!"
})

invalid_instance = JSON({
    "greeting": "Hi, World"
})

pp(schema.evaluate(valid_instance).valid)
# True

pp(schema.evaluate(invalid_instance).output('detailed'))
# {'valid': False,
#  'instanceLocation': '',
#  'keywordLocation': '',
#  'absoluteKeywordLocation': 'https://example.com/greeting#',
#  'errors': [{'instanceLocation': '/greeting',
#              'keywordLocation': '/properties/greeting/$ref/minLength',
#              'absoluteKeywordLocation': 'https://example.com/greeting#/$defs/greetingDefinition/minLength',
#              'error': 'The text is too short (minimum 10 characters)'}]}
