"""A stub for profiling tools to run one basic simulation."""

import os
import types
import unittest
from datetime import datetime

import nemo
from nemo import (configfile, costs, generators, polygons, regions, scenarios,
                  utils)
from nemo.generators import (CCGT, CCGT_CCS, OCGT, Battery, Behind_Meter_PV,
                             Biomass, Black_Coal, Coal_CCS, DemandResponse,
                             Diesel, Electrolyser, Geothermal_EGS,
                             Geothermal_HSA, GreenPower, HydrogenGT,
                             HydrogenStorage, ParabolicTrough, WindOffshore)
from nemo.polygons import WILDCARD

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

    def test_006(self):
        """Test the works (all technologies)."""
        ctx = nemo.Context()
        ctx.costs = costs.NullCosts()

        # Set up the scenario.
        scenarios.re100(ctx)

        wind_trace = configfile.get('generation', 'wind-trace')
        esg_trace = configfile.get('generation', 'egs-geothermal-trace')
        hsa_trace = configfile.get('generation', 'hsa-geothermal-trace')
        cst_trace = configfile.get('generation', 'cst-trace')
        rooftop_trace = configfile.get('generation', 'rooftop-pv-trace')

        # hydrogen electrolyser and gas turbine w/ shared tank
        tank = HydrogenStorage(1000)

        ctx.generators += \
            [Geothermal_EGS(WILDCARD, 0, esg_trace, 38),
             Geothermal_HSA(WILDCARD, 0, hsa_trace, 38),
             ParabolicTrough(WILDCARD, 0, 2, 6, cst_trace, 12),
             Black_Coal(WILDCARD, 0),
             Coal_CCS(WILDCARD, 0),
             CCGT(WILDCARD, 0),
             CCGT_CCS(WILDCARD, 0),
             WindOffshore(WILDCARD, 0, wind_trace, WILDCARD - 1),
             Behind_Meter_PV(WILDCARD, 0, rooftop_trace, 0),
             OCGT(WILDCARD, 0),
             Diesel(WILDCARD, 0),
             Battery(WILDCARD, 0, 0),
             DemandResponse(WILDCARD, 0, 300),
             Biomass(WILDCARD, 0),
             Electrolyser(tank, WILDCARD, 100),
             HydrogenGT(tank, 1, 100, efficiency=0.5),
             GreenPower(WILDCARD, 0)]

        nemo.run(ctx)
