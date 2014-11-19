"""A stub for profiling tools to run one basic simulation."""

import os
import generators
import nem
import regions
import unittest


class TestCoverage(unittest.TestCase):

    """A handful of miscellaneous tests to ensure good coverage."""

    def test_001(self):
        c = nem.Context()
        c.regions = [regions.nsw, regions.vic, regions.sa]
        c.track_exchanges = True
        c.verbose = 1
        nem.run(c)

    def test_002(self):
        c = nem.Context()
        nem.run(c)
        nem.plot(c, filename='foo.png')
        os.unlink('foo.png')
        nem.plot(c, filename='foo.png', spills=True)
        os.unlink('foo.png')

    def test_003(self):
        c = nem.Context()
        for g in c.generators:
            if isinstance(g, generators.CST):
                g.dispHour = 16
        nem.run(c)
