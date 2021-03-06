# Copyright (C) 2011, 2014 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

# pylint: disable=too-many-public-methods

"""A testsuite for NEMO."""

import math
import unittest
import pandas as pd

import nemo
from nemo import regions
from nemo import polygons
from nemo import generators


class SuperGenerator(generators.Generator):

    """A synthetic generator that can always meet demand."""

    def __init__(self, capacity):
        """Create a super generator."""
        generators.Generator.__init__(self, polygons.wildcard, capacity, 'super')
        self.energy = 0
        self.runhours = 0

    def reset(self):
        """Reset context between tests."""
        self.energy = 0
        self.runhours = 0

    # pylint: disable=unused-argument
    def step(self, hr, demand):
        """Step the super generator."""
        self.runhours += 1
        self.energy += demand
        if self.capacity is None:
            # meet demand exactly
            return demand, 0
        # meet demand, spill surplus capacity
        surplus = max(0, self.capacity - demand)
        return demand, surplus


class TestSequenceFunctions(unittest.TestCase):

    """Basic tests for now."""

    def setUp(self):
        """Test harness setup."""
        self.context = nemo.Context()
        self.minload = math.floor(self.context.demand.sum(axis=1).min())

    def test_001(self):
        """Test that all regions are present."""
        self.assertEqual(self.context.regions, regions.All)

    def test_002(self):
        """Demand equals approx. 204 TWh."""
        self.context.generators = []
        nemo.run(self.context)
        self.assertEqual(math.trunc(self.context.total_demand() / pow(10., 6)), 204)

    def test_003(self):
        """Power system with no generators meets none of the demand."""
        self.context.generators = []
        nemo.run(self.context)
        self.assertEqual(math.trunc(self.context.unserved_energy()),
                         math.trunc(self.context.total_demand()))

    def test_004(self):
        """100 MW fossil plant generates exactly 876,000 MWh."""
        ccgt = generators.CCGT(polygons.wildcard, 100)
        self.context.generators = [ccgt]
        nemo.run(self.context)
        self.assertEqual(sum(ccgt.series_power.values()), self.context.timesteps * 100)

    # Create a super generator that always meets demand.
    # Check unserved_energy = 0

    def test_005(self):
        """Super generator runs every hour."""
        gen = SuperGenerator(None)
        self.context.generators = [gen]
        nemo.run(self.context)
        self.assertEqual(gen.runhours, self.context.timesteps)

    def test_006(self):
        """Generation to meet minimum load leads to no spills."""
        self.context.generators = [SuperGenerator(self.minload)]
        nemo.run(self.context)
        self.assertEqual(self.context.spill.values.sum(), 0)

    def test_007(self):
        """Generation to meet minimum load + 1GW produces some spills."""
        self.context.generators = [SuperGenerator(self.minload + 1000)]
        nemo.run(self.context)
        self.assertTrue(self.context.spill.values.sum() > 0)

    def test_008(self):
        """A NSW generator runs in NSW only."""
        for rgn in regions.All:
            self.context.regions = [rgn]
            gen = SuperGenerator(None)
            self.context.generators = [gen]
            nemo.run(self.context)
            if rgn == regions.nsw:
                self.assertEqual(gen.runhours, self.context.timesteps)
            else:
                self.assertEqual(gen.runhours, 0)

    def test_009(self):
        """A NSW generators runs in any set of regions that includes NSW."""
        rgnset = []
        for rgn in regions.All:
            rgnset.append(rgn)
            self.context.regions = rgnset
            gen = SuperGenerator(None)
            self.context.generators = [gen]
            nemo.run(self.context)
            self.assertEqual(gen.runhours, self.context.timesteps)

    def test_010(self):
        """Running in one region only produces no interstate exchanges."""
        for rgn in regions.All:
            if rgn is regions.snowy:
                continue
            self.context = nemo.Context()
            self.context.track_exchanges = True
            self.context.regions = [rgn]
            loadpoly = [k for k, v in list(rgn.polygons.items()) if v > 0][0]
            nswpoly = [k for k, v in list(regions.nsw.polygons.items()) if v > 0][0]
            qldpoly = [k for k, v in list(regions.qld.polygons.items()) if v > 0][0]
            sapoly = [k for k, v in list(regions.sa.polygons.items()) if v > 0][0]
            taspoly = [k for k, v in list(regions.tas.polygons.items()) if v > 0][0]
            vicpoly = [k for k, v in list(regions.vic.polygons.items()) if v > 0][0]

            self.context.generators = []
            for poly in [nswpoly, qldpoly, sapoly, taspoly, vicpoly]:
                self.context.generators.append(generators.OCGT(poly, 100))
            nemo.run(self.context, endhour=pd.Timestamp('2010-01-05'))
            self.assertEqual((self.context.exchanges[0] > 0).sum(), 1, 'Only one exchange > 0')
            # FXME: we need a numpy array that can be indexed from 1
            self.assertTrue(self.context.exchanges[0, loadpoly - 1, loadpoly - 1] > 0,
                            'Only rgn->rgn is > 0')

    def test_011(self):
        """Running in two regions only produces limited interstate exchanges."""
        for rgn1 in regions.All:
            for rgn2 in regions.All:
                if rgn1 is rgn2:
                    continue
                self.context.regions = [rgn1, rgn2]
                nemo.run(self.context, endhour=1)
                self.assertTrue(self.context.exchanges[0, rgn1, rgn1] >= 0)
                self.assertTrue(self.context.exchanges[0, rgn2, rgn2] >= 0)
                for i in regions.All:
                    for j in regions.All:
                        # Check that various elements of the exchanges matrix are 0.
                        # Ignore: diagonals, [RGN1,RGN2] and [RGN2,RGN1].
                        if i != j and (i, j) != (rgn1, rgn2) and (i, j) != (rgn2, rgn1):
                            self.assertEqual(self.context.exchanges[0, i, j], 0)

    def test_012(self):
        """A NSW generator does not run in other regions."""
        rgnset = []
        # Skip NSW (first in the list).
        for rgn in regions.All[1:]:
            rgnset.append(rgn)
            self.context.regions = rgnset
            gen = SuperGenerator(None)
            self.context.generators = [gen]
            nemo.run(self.context)
            self.assertEqual(gen.runhours, 0)

    def test_013(self):
        """Fossil plant records power generation history."""
        ccgt = generators.CCGT(polygons.wildcard, 100)
        self.context.generators = [ccgt]
        nemo.run(self.context)
        self.assertTrue(len(self.context.generators[0].series_power) > 0)
