# Copyright (C) 2022 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

# pylint: disable=too-many-public-methods

"""A testsuite for the Context class."""

import unittest
import numpy as np
import pandas as pd

import nemo


class TestContextMethods(unittest.TestCase):
    """Tests for Context methods."""

    def setUp(self):
        """Test harness setup."""
        self.context = nemo.Context()

    def test_total_demand(self):
        """Test total_demand() method."""
        self.assertTrue(self.context.total_demand() > 0)
        self.assertEqual(self.context.total_demand(),
                         self.context.demand.values.sum())

    def test_unserved_energy(self):
        """Test unserved_energy method."""
        self.assertEqual(self.context.unserved_energy(), 0)
        self.assertEqual(self.context.unserved_energy(),
                         self.context.unserved.values.sum())

    def test_surplus_energy(self):
        """Test surplus_energy method."""
        self.assertEqual(self.context.surplus_energy(), 0)
        self.assertEqual(self.context.surplus_energy(),
                         self.context.spill.values.sum())

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
