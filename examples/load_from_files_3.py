import pathlib
from jschon import Catalog, JSON, URI

data_dir = pathlib.Path(__file__).parent / 'data'

catalog = Catalog('2020-12')
catalog.add_directory(URI("https://example.com/"), data_dir)

org_schema = catalog.get_schema(URI("https://example.com/org-schema"))
org_data = JSON.loadf(data_dir / 'org-data.json')

result = org_schema.evaluate(org_data)
print(result.output('flag'))
