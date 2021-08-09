import pathlib
from jschon import create_catalog, JSON, JSONSchema

data_dir = pathlib.Path(__file__).parent / 'data'

catalog = create_catalog('2020-12', default=True)

person_schema = JSONSchema.loadf(data_dir / 'person-schema.json')
org_schema = JSONSchema.loadf(data_dir / 'org-schema.json')
org_data = JSON.loadf(data_dir / 'org-data.json')

result = org_schema.evaluate(org_data)
print(result.output('flag'))
