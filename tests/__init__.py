from rfc3986 import uri_reference

from jschon.catalogue import jsonschema_draft_2019_09

jsonschema_draft_2019_09.initialize()

metaschema_uri = uri_reference("https://json-schema.org/draft/2019-09/schema")
