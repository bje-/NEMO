# Copyright (C) 2011, 2014 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""A testsuite for NEMO."""

import math
import unittest

import nemo
from nemo import generators, polygons, regions


class SuperGenerator(generators.Generator):
    """A synthetic generator that can always meet demand."""

    def __init__(self, capacity):
        """Create a super generator."""
        generators.Generator.__init__(self, polygons.WILDCARD, capacity)
        self.energy = 0
        self.runhours = 0

    def reset(self):
        """Reset context between tests."""
        self.energy = 0
        self.runhours = 0

    def step(self, _, demand):
        """Step the super generator."""
        self.runhours += 1
        self.energy += demand
        if self.capacity == 0:
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
        total_demand = math.trunc(self.context.total_demand() / pow(10., 6))
        self.assertEqual(total_demand, 204)

    def test_003(self):
        """Power system with no generators meets none of the demand."""
        self.context.generators = []
        nemo.run(self.context)
        self.assertEqual(math.trunc(self.context.unserved_energy()),
                         math.trunc(self.context.total_demand()))

    def test_004(self):
        """100 MW fossil plant generates exactly 876,000 MWh."""
        ccgt = generators.CCGT(polygons.WILDCARD, 100)
        self.context.generators = [ccgt]
        nemo.run(self.context)
        total_generation = sum(ccgt.series_power.values())
        expected_generation = self.context.timesteps * 100
        self.assertEqual(total_generation, expected_generation)

    # Create a super generator that always meets demand.
    # Check unserved_energy = 0

    def test_005(self):
        """Super generator runs every hour."""
        gen = SuperGenerator(0)
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
            gen = SuperGenerator(0)
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
            gen = SuperGenerator(0)
            self.context.generators = [gen]
            nemo.run(self.context)
            self.assertEqual(gen.runhours, self.context.timesteps)

    def test_012(self):
        """A NSW generator does not run in other regions."""
        rgnset = []
        # Skip NSW (first in the list).
        for rgn in regions.All[1:]:
            rgnset.append(rgn)
            self.context.regions = rgnset
            gen = SuperGenerator(0)
            self.context.generators = [gen]
            nemo.run(self.context)
            self.assertEqual(gen.runhours, 0)

    def test_013(self):
        """Fossil plant records power generation history."""
        ccgt = generators.CCGT(polygons.WILDCARD, 100)
        self.context.generators = [ccgt]
        nemo.run(self.context)
        self.assertTrue(len(self.context.generators[0].series_power) > 0)
