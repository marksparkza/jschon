import pathlib
from jschon import create_catalog, JSON, JSONSchema, URI, LocalSource

data_dir = pathlib.Path(__file__).parent / 'data'

catalog = create_catalog('2020-12')
catalog.add_uri_source(URI.get('https://example.com/'), LocalSource(data_dir, suffix='.json'))

org_schema = JSONSchema.loadf(data_dir / 'org-schema.json')
org_data = JSON.loadf(data_dir / 'org-data.json')

result = org_schema.evaluate(org_data)
print(result.output('flag'))
