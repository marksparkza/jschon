import cProfile
import pstats

from jschon import create_catalog

with cProfile.Profile() as pr:
    create_catalog('2020-12')

ps = pstats.Stats(pr)
ps.sort_stats('calls')
ps.print_stats('/jschon/jschon/', .1)
