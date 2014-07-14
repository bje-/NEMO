# Copyright (C) 2011, 2014 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

# pylint: disable=too-many-public-methods

"""A testsuite for NEMO."""

import math
import nem
import regions
import generators
import unittest


class SuperGenerator(generators.Generator):

    """A synthetic generator that can always meet demand."""

    def __init__(self, capacity):
        """Create a super generator."""
        generators.Generator.__init__(self, regions.nsw, capacity, 'super')
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
        else:
            # meet demand, spill surplus capacity
            surplus = max(0, self.capacity - demand)
            return demand, surplus


class TestSequenceFunctions(unittest.TestCase):

    """Basic tests for now."""

    def setUp(self):
        """Test harness setup."""
        self.context = nem.Context()
        self.minload = math.floor(self.context.demand.sum(axis=0).min())

    def test_001(self):
        """Test that all regions are present."""
        self.assertEqual(self.context.regions, regions.All)

    def test_002(self):
        """Demand equals approx. 204 TWh."""
        self.context.generators = []
        nem.run(self.context)
        self.assertEqual(math.trunc(self.context.demand.sum() / pow(10, 6)), 204)

    def test_003(self):
        """Power system with no generators meets none of the demand."""
        self.context.generators = []
        nem.run(self.context)
        self.assertEqual(math.trunc(self.context.unserved_energy), math.trunc(self.context.demand.sum()))

    def test_004(self):
        """100 MW fossil plant generates exactly 876,000 MWh."""
        ccgt = generators.CCGT(regions.nsw, 100)
        self.context.generators = [ccgt]
        nem.run(self.context)
        self.assertEqual(ccgt.hourly_power.sum(), nem.hours * 100)

    # Create a super generator that always meets demand.
    # Check unserved_energy = 0

    def test_005(self):
        """Super generator runs every hour."""
        gen = SuperGenerator(None)
        self.context.generators = [gen]
        nem.run(self.context)
        self.assertEqual(gen.runhours, nem.hours)

    def test_006(self):
        """Generation to meet minimum load leads to no spills."""
        self.context.generators = [SuperGenerator(self.minload)]
        nem.run(self.context)
        self.assertEqual(self.context.spilled_energy, 0)

    def test_007(self):
        """Generation to meet minimum load + 1GW produces some spills."""
        self.context.generators = [SuperGenerator(self.minload + 1000)]
        nem.run(self.context)
        self.assertTrue(self.context.spilled_energy > 0)

    def test_008(self):
        """A NSW generator runs in NSW only."""
        for rgn in regions.All:
            self.context.regions = [rgn]
            gen = SuperGenerator(None)
            self.context.generators = [gen]
            nem.run(self.context)
            if rgn == regions.nsw:
                self.assertEqual(gen.runhours, nem.hours)
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
            nem.run(self.context)
            self.assertEqual(gen.runhours, nem.hours)

    def test_010(self):
        """Running in one region only produces no interstate exchanges."""
        self.context.track_exchanges = True
        for rgn in regions.All:
            self.context.regions = [rgn]
            nem.run(self.context, endhour=1)
            self.assertEqual((self.context.exchanges[0] > 0).sum(), 1)
            self.assertTrue(self.context.exchanges[0, rgn, rgn] > 0, 'Only one exchange > 0')

    def test_011(self):
        """Running in two regions only produces limited interstate exchanges."""
        for rgn1 in regions.All:
            for rgn2 in regions.All:
                if rgn1 is rgn2:
                    continue
                self.context.regions = [rgn1, rgn2]
                nem.run(self.context, endhour=1)
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
            nem.run(self.context)
            self.assertEqual(gen.runhours, 0)

    def test_013(self):
        """Fossil plant records power generation history."""
        ccgt = generators.CCGT(regions.nsw, 100)
        self.context.generators = [ccgt]
        nem.run(self.context)
        self.assertTrue((self.context.generators[0].hourly_power > 0).sum())
