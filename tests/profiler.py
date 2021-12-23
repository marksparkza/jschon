import cProfile
import pstats

import pytest

with cProfile.Profile() as pr:
    pytest.main(['-k', 'test_suite'])

ps = pstats.Stats(pr)
ps.sort_stats('calls')
ps.print_stats('/jschon/jschon/', 50)
