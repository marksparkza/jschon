import cProfile
import pstats

from jschon import create_catalog, JSONSchema, JSON
from tests import example_schema, example_valid, example_invalid

with cProfile.Profile() as pr:
    create_catalog('2020-12')
    schema = JSONSchema(example_schema)
    schema.evaluate(JSON(example_valid)).output('verbose')
    schema.evaluate(JSON(example_invalid)).output('verbose')

ps = pstats.Stats(pr)
ps.sort_stats('calls')
ps.print_stats('/jschon/jschon/', .5)
