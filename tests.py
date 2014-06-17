# testsuite.py: a testsuite for the National Electricity Market sim.
#
# -*- Python -*-
# Copyright (C) 2011 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

import math
import nem
import regions
import generators
import unittest


class SuperGenerator(generators.Generator):
    "A synthetic generator that can always meet demand."
    def __init__(self, capacity):
        generators.Generator.__init__(self, regions.nsw, capacity, 'super')
        self.energy = 0
        self.runhours = 0

    def reset(self):
        self.energy = 0
        self.runhours = 0

    def step(self, hr, demand):
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
    def setUp(self):
        self.context = nem.Context()

    def test_001(self):
        'Test that all regions are present'
        self.assertEqual(self.context.regions, regions.all)

    def test_002(self):
        'Demand equals approx. 204 TWh'
        self.context.generators = []
        nem.run(self.context)
        self.assertEqual(math.trunc(self.context.demand.sum() / pow(10, 6)), 204)

    def test_003(self):
        'Power system with no generators meets none of the demand'
        self.context.generators = []
        nem.run(self.context)
        self.assertEqual(self.context.unserved_energy, self.context.demand.sum())

    def test_004(self):
        '100 MW fossil plant generates exactly 8760*100 MWh'
        fossil = generators.Fossil(regions.nsw, 100)
        self.context.generators = [fossil]
        nem.run(self.context)
        self.assertEqual(fossil.hourly_power.sum(), 8760 * 100)

    # Create a super generator that always meets demand.
    # Check unserved_energy = 0

    def test_005(self):
        'Super generator runs every hour'
        gen = SuperGenerator(None)
        self.context.generators = [gen]
        nem.run(self.context)
        self.assertEqual(gen.runhours, 8760)

    def test_006(self):
        'Generation to meet minimum load leads to no spills'
        minload = math.floor(nem.aggregate_demand.min())
        self.context.generators = [SuperGenerator(minload)]
        nem.run(self.context)
        self.assertEqual(self.context.spilled_energy, 0)

    def test_007(self):
        'Generation to meet minimum load + 1GW produces some spills'
        minload = math.floor(nem.aggregate_demand.min())
        self.context.generators = [SuperGenerator(minload + 1000)]
        nem.run(self.context)
        self.assertTrue(self.context.spilled_energy > 0)

    def test_008(self):
        'A NSW generator runs in NSW only'
        for rgn in regions.all:
            self.context.regions = [rgn]
            gen = SuperGenerator(None)
            self.context.generators = [gen]
            nem.run(self.context)
            if rgn == regions.nsw:
                self.assertEqual(gen.runhours, 8760)
            else:
                self.assertEqual(gen.runhours, 0)

    def test_009(self):
        'A NSW generators runs in any set of regions that includes NSW'
        rgnset = []
        for rgn in regions.all:
            rgnset.append(rgn)
            self.context.regions = rgnset
            gen = SuperGenerator(None)
            self.context.generators = [gen]
            nem.run(self.context)
            self.assertEqual(gen.runhours, 8760)

    def test_010(self):
        'Running in one region only produces no interstate exchanges'
        for rgn in regions.all:
            self.context.regions = [rgn]
            nem.run(self.context, endhour=1)
            self.assertEqual((self.context.exchanges[0] > 0).sum(), 1)
            self.assertTrue(self.context.exchanges[0, rgn, rgn] > 0, 'Only one exchange > 0')

    def test_011(self):
        'Running in two regions only produces limited interstate exchanges'
        for rgn1 in regions.all:
            for rgn2 in regions.all:
                if rgn1 is rgn2:
                    continue
                self.context.regions = [rgn1, rgn2]
                nem.run(self.context, endhour=1)
                self.assertTrue(self.context.exchanges[0, rgn1, rgn1] >= 0)
                self.assertTrue(self.context.exchanges[0, rgn2, rgn2] >= 0)
                for i in regions.all:
                    for j in regions.all:
                        # Check that various elements of the exchanges matrix are 0.
                        # Ignore: diagonals, [RGN1,RGN2] and [RGN2,RGN1].
                        if i != j and (i, j) != (rgn1, rgn2) and (i, j) != (rgn2, rgn1):
                            self.assertEqual(self.context.exchanges[0, i, j], 0)

    def test_012(self):
        'A NSW generator does not run in other regions'
        rgnset = []
        # Skip NSW (first in the list).
        for rgn in regions.all[1:]:
            rgnset.append(rgn)
            self.context.regions = rgnset
            gen = SuperGenerator(None)
            self.context.generators = [gen]
            nem.run(self.context)
            self.assertEqual(gen.runhours, 0)

    def test_013(self):
        'Fossil plant records power generation history'
        fossil = generators.Fossil(regions.nsw, 100)
        self.context.generators = [fossil]
        nem.run(self.context)
        self.assertTrue((self.context.generators[0].hourly_power > 0).sum())

if __name__ == '__main__':
    unittest.main()
