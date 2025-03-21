# Copyright (C) 2022 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""A testsuite for the Context class."""

import unittest

import numpy as np
import pandas as pd

import nemo
from nemo import regions


class TestContextMethods(unittest.TestCase):
    """Tests for Context methods."""

    def setUp(self):
        """Test harness setup."""
        self.context = nemo.Context()

    def test_total_demand(self):
        """Test total_demand() method."""
        assert self.context.total_demand() > 0
        assert self.context.total_demand() == \
            self.context.demand.to_numpy().sum()

    def test_unserved_energy(self):
        """Test unserved_energy method."""
        assert self.context.unserved_energy() == 0
        assert self.context.unserved_energy() == \
            self.context.unserved.to_numpy().sum()

    def test_surplus_energy(self):
        """Test surplus_energy method."""
        assert self.context.surplus_energy() == 0
        assert self.context.surplus_energy() == \
            self.context.spill.to_numpy().sum()

    def test_unserved_percent(self):
        """Test unserved_percent method."""
        assert self.context.unserved_percent() == 0

        # Special handling required for zero demand
        self.context.demand = pd.DataFrame()
        assert np.isnan(self.context.unserved_percent())

    def test_set_capacities(self):
        """Test set_capacities method."""
        self.context.set_capacities([0.1, 0.2])
        assert self.context.generators[0].capacity == 100
        assert self.context.generators[1].capacity == 200

    def test_set_capacities_exception(self):
        """Test error handling in set_capacities."""
        with self.assertRaises(ValueError):
            self.context.set_capacities([0.1] * 10)

    def test_str_no_unserved(self):
        """Test __str__ method (no unserved energy)."""
        output = str(self.context)
        assert 'No unserved energy' in output

    def test_str_with_regions_subset(self):
        """Test __str__ method with only two regions."""
        self.context.regions = [regions.nsw, regions.sa]
        output = str(self.context)
        assert 'Regions: [NSW1, SA1]' in output

    def test_str_no_summary(self):
        """Test __str__ method with a generator that has no summary."""
        self.context.generators[1].summary = lambda _: None
        self.context.verbose = True
        output = str(self.context)
        assert 'OCGT (NSW1:31), 20000.00 MW\nTimesteps:' in output

    def test_str_with_unserved(self):
        """Test __str__ method (with some unserved energy)."""
        self.context.verbose = True
        # Dummy lambda functions for testing
        self.context.surplus_energy = lambda: 300
        self.context.unserved_percent = lambda: 0.5
        rng = pd.date_range(start='2022-01-01', end='2022-01-02', freq='h')
        self.context.unserved = pd.Series(index=rng, data=range(len(rng)))
        output = str(self.context)

        assert 'Generators:' in output
        assert f'Timesteps: {self.context.timesteps()} h' in output
        assert 'Demand energy:' in output
        assert 'Unstored surplus energy: 300.00 MWh' in output
        assert 'WARNING: reliability standard exceeded' in output
        assert 'Unserved total hours: 25' in output
        assert 'Number of unserved energy events: 1' in output
        assert 'Shortfalls (min, max): (0.00 MW, 24.00 MW)' in output
