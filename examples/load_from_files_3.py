import pathlib
from jschon import create_catalog, JSON, URI, LocalSource

data_dir = pathlib.Path(__file__).parent / 'data'

catalog = create_catalog('2020-12')
catalog.add_uri_source(URI('https://example.com/'), LocalSource(data_dir, suffix='.json'))

org_schema = catalog.get_schema(URI('https://example.com/org-schema'))
org_data = JSON.loadf(data_dir / 'org-data.json')

result = org_schema.evaluate(org_data)
print(result.output('flag'))
