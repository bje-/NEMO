# Copyright (C) 2022 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""A testsuite for the Context class."""

import unittest

import nemo
import numpy as np
import pandas as pd
from nemo import regions


class TestContextMethods(unittest.TestCase):
    """Tests for Context methods."""

    def setUp(self):
        """Test harness setup."""
        self.context = nemo.Context()

    def test_total_demand(self):
        """Test total_demand() method."""
        self.assertTrue(self.context.total_demand() > 0)
        self.assertEqual(self.context.total_demand(),
                         self.context.demand.to_numpy().sum())

    def test_unserved_energy(self):
        """Test unserved_energy method."""
        self.assertEqual(self.context.unserved_energy(), 0)
        self.assertEqual(self.context.unserved_energy(),
                         self.context.unserved.to_numpy().sum())

    def test_surplus_energy(self):
        """Test surplus_energy method."""
        self.assertEqual(self.context.surplus_energy(), 0)
        self.assertEqual(self.context.surplus_energy(),
                         self.context.spill.to_numpy().sum())

    def test_unserved_percent(self):
        """Test unserved_percent method."""
        self.assertEqual(self.context.unserved_percent(), 0)

        # Special handling required for zero demand
        self.context.demand = pd.DataFrame()
        self.assertTrue(np.isnan(self.context.unserved_percent()))

    def test_set_capacities(self):
        """Test set_capacities method."""
        self.context.set_capacities([0.1, 0.2])
        self.assertEqual(self.context.generators[0].capacity, 100)
        self.assertEqual(self.context.generators[1].capacity, 200)

    def test_str_no_unserved(self):
        """Test __str__ method (no unserved energy)."""
        output = str(self.context)
        self.assertIn('No unserved energy', output)

    def test_str_with_regions_subset(self):
        """Test __str__ method with only two regions."""
        self.context.regions = [regions.nsw, regions.sa]
        output = str(self.context)
        self.assertIn('Regions: [NSW1, SA1]', output)

    def test_str_no_summary(self):
        """Test __str__ method with a generator that has no summary."""
        self.context.generators[1].summary = lambda _: None
        self.context.verbose = True
        output = str(self.context)
        self.assertIn('OCGT (NSW1:31), 20000.00 MW\nTimesteps:', output)

    def test_str_with_unserved(self):
        """Test __str__ method (with some unserved energy)."""
        self.context.verbose = True
        # Dummy lambda functions for testing
        self.context.surplus_energy = lambda: 300
        self.context.unserved_percent = lambda: 0.5
        rng = pd.date_range(start='2022-01-01', end='2022-01-02', freq='h')
        self.context.unserved = pd.Series(index=rng, data=range(len(rng)))
        output = str(self.context)

        self.assertIn('Generators:', output)
        self.assertIn(f'Timesteps: {self.context.timesteps()} h', output)
        self.assertIn('Demand energy:', output)
        self.assertIn('Unstored surplus energy: 300.00 MWh', output)
        self.assertIn('WARNING: reliability standard exceeded', output)
        self.assertIn('Unserved total hours: 25', output)
        self.assertIn('Number of unserved energy events: 1', output)
        self.assertIn('Shortfalls (min, max): (0.00 MW, 24.00 MW)', output)
