import pathlib
import pprint

from jschon import create_catalog, URI, JSON, JSONSchema, JSONSchemaError
from jschon.jsonschema import Scope
from jschon.vocabulary import Keyword

data_dir = pathlib.Path(__file__).parent / 'data'

# create a simple mapping to emulate a remote enumeration service
remote_enum_cache = {
    "https://example.com/remote-enum-colours": [
        "red",
        "orange",
        "yellow",
        "green",
        "blue",
        "indigo",
        "violet",
    ]
}


# define a class that implements the "enumRef" keyword
class EnumRefKeyword(Keyword):
    key = "enumRef"

    # if "enumRef" is only intended for use with string instances, then its
    # applicability may be constrained with `types`, in which case any non-
    # string instances are ignored by this keyword
    types = "string"

    def __init__(self, parentschema: JSONSchema, value: str):
        super().__init__(parentschema, value)

        # get the keyword's value as it appears in the JSON schema
        self.enum_id = self.json.data
        try:
            # retrieve the enumeration from the remote enumeration service
            self.enum = remote_enum_cache[self.enum_id]
        except KeyError:
            raise JSONSchemaError(f"Unknown remote enumeration {self.enum_id}")

    def evaluate(self, instance: JSON, scope: Scope) -> None:
        # test the value of the current JSON instance node against the enumeration
        if instance.data in self.enum:
            # (optionally) on success, set an annotation on the current scope node
            scope.annotate(self.enum_id)
        else:
            # on failure, flag the scope as failed, with an (optional) error message
            scope.fail(f"The instance is not a member of the {self.enum_id} enumeration")


# initialize the catalog, with JSON Schema 2020-12 vocabulary support
catalog = create_catalog('2020-12', default=True)

# add a base URI-to-directory mapping to enable loading of the
# enumRef metaschema and vocabulary definition files
catalog.add_directory(
    URI("https://example.com/enumRef/"),
    data_dir,
)

# implement the enumRef vocabulary using the EnumRefKeyword class
catalog.create_vocabulary(
    URI("https://example.com/enumRef"),
    EnumRefKeyword,
)

# compile the enumRef metaschema, which enables any referencing schema
# to use the keyword implementations provided by its vocabularies
catalog.create_metaschema(
    URI("https://example.com/enumRef/enumRef-metaschema"),
    URI("https://json-schema.org/draft/2020-12/vocab/core"),
    URI("https://json-schema.org/draft/2020-12/vocab/applicator"),
    URI("https://json-schema.org/draft/2020-12/vocab/unevaluated"),
    URI("https://json-schema.org/draft/2020-12/vocab/validation"),
    URI("https://json-schema.org/draft/2020-12/vocab/format-annotation"),
    URI("https://json-schema.org/draft/2020-12/vocab/meta-data"),
    URI("https://json-schema.org/draft/2020-12/vocab/content"),
    URI("https://example.com/enumRef"),
)

# create a schema for validating that a string is a member of a remote enumeration
schema = JSONSchema({
    "$schema": "https://example.com/enumRef/enumRef-metaschema",
    "$id": "https://example.com/remote-enum-test-schema",
    "type": "string",
    "enumRef": "https://example.com/remote-enum-colours",
})

# validate the schema against its metaschema
schema_validity = schema.validate()
print(f'Schema validity check: {schema_validity.valid}')

# declare a valid JSON instance
valid_json = JSON("green")

# declare an invalid JSON instance
invalid_json = JSON("purple")

# evaluate the valid instance
valid_result = schema.evaluate(valid_json)

# evaluate the invalid instance
invalid_result = schema.evaluate(invalid_json)

# print output for the valid case
print(f'Valid JSON result: {valid_result.valid}')
print('Valid JSON detailed output:')
pprint.pp(valid_result.output('detailed'))

# print output for the invalid case
print(f'Invalid JSON result: {invalid_result.valid}')
print('Invalid JSON detailed output:')
pprint.pp(invalid_result.output('detailed'))
