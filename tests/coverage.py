"""A stub for profiling tools to run one basic simulation."""

import os
import unittest
import types
from datetime import datetime

import nemo
from nemo import costs
from nemo import generators
from nemo import regions
from nemo import polygons
from nemo import utils

# pylint: disable=no-self-use


class TestCoverage(unittest.TestCase):
    """A handful of miscellaneous tests to ensure good coverage."""

    def test_001(self):
        """Test 1."""
        ctx = nemo.Context()
        ctx.regions = [regions.nsw, regions.vic, regions.sa]
        ctx.verbose = 1
        nemo.run(ctx)

    def test_002(self):
        """Test 2."""
        ctx = nemo.Context()
        # Make sure there is unserved energy by setting 2nd and
        # subsequent generator capacity to 0.
        for gen in ctx.generators[1:]:
            gen.set_capacity(0)
        nemo.run(ctx)
        utils.plot(ctx, filename='foo.png')
        os.unlink('foo.png')
        utils.plot(ctx, filename='foo.png', spills=True)
        os.unlink('foo.png')

        # Test limiting the x-range.
        xlim = [datetime(2010, 1, 1), datetime(2010, 1, 10)]
        utils.plot(ctx, filename='foo.png', xlim=xlim)
        os.unlink('foo.png')

    def test_003(self):
        """Test 3."""
        ctx = nemo.Context()
        # Add 25 DR generators so that the abbreviated legend is used.
        for _ in range(25):
            demresp = generators.DemandResponse(polygons.WILDCARD, 100, 0)
            ctx.generators += [demresp]
        print(len(ctx.generators))
        nemo.run(ctx)
        utils.plot(ctx, filename='foo.png')
        os.unlink('foo.png')

    def test_004(self):
        """Test Context.__str__ method."""
        ctx = nemo.Context()
        print(str(ctx))
        ctx.regions = [regions.nsw]
        print(str(ctx))

    def test_005(self):
        """Test Context summary with no cost generator."""
        ctx = nemo.Context()
        ctx.costs = costs.NullCosts()
        print(str(ctx))
        ctx.verbose = True
        print(str(ctx))
        ctx.regions = [regions.nsw]
        print(str(ctx))

        func = types.MethodType(lambda self, costs: None, ctx.generators[0])
        print(func)
        ctx.generators[0].summary = func
        print(ctx.generators[0].summary(None))
        print(str(ctx))
