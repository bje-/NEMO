# Copyright (C) 2022 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

# pylint: disable=protected-access

"""A testsuite for the penalties module."""

import unittest

import nemo
import numpy as np
from nemo import generators, penalties, regions, storage
from nemo.penalties import reasons
from nemo.polygons import WILDCARD


class Args:
    """Faked up command line options."""

    emissions_limit = 0
    fossil_limit = 0.5  # 50%
    bioenergy_limit = 1e-6  # 1 MWh
    hydro_limit = 1e-6  # 1 MWh
    reserves = 50  # MW


args = Args()


class TestPenalties(unittest.TestCase):
    """Test functions in penalties.py."""

    def setUp(self):
        """Test harness setup."""
        self.context = nemo.Context()
        # Override standard attributes and methods for testing
        self.context.demand = np.ones((43, 100))
        self.context.total_demand = lambda: 100
        self.context.unserved_energy = lambda: 0.01
        self.context.relstd = 0

    def test_unserved(self):
        """Test unserved() function."""
        self.assertEqual(penalties.unserved(self.context, 0),
                         (pow(0.01, 3), reasons['unserved']))

    def test_calculate_reserve(self):
        """Test _calculate_reserve() function."""
        self.context.generators[0].series_power = {n: 1 for n in range(1000)}
        generator = self.context.generators[0]
        capacity = generator.capacity
        self.assertEqual(penalties._calculate_reserve(generator, 0),
                         capacity - 1)
        psh_storage = storage.PumpedHydroStorage(0)
        psh_turbine = generators.PumpedHydroTurbine(WILDCARD, 0, psh_storage)
        self.assertEqual(penalties._calculate_reserve(psh_turbine, 0), 0)

    def test_reserves(self):
        """Test reserves() function."""
        self.context.timesteps = lambda: 100
        del self.context.generators[1:]
        # 55 MW x 100 hours, 5 MW over reserve level
        self.context.generators[0].series_power = {n: 55 for n in range(100)}
        self.context.generators[0].capacity = 100
        self.assertEqual(penalties.reserves(self.context, args),
                         (pow(5, 3) * 100, reasons['reserves']))

    def test_regional_generation(self):
        """Test _regional_generation() function."""
        # Gen 1: 1,000 MWh, Gen 2: 1,000 MWh, total 2,000 MWh
        self.context.generators[0].series_power = {n: 1 for n in range(1000)}
        self.context.generators[1].series_power = {n: 1 for n in range(1000)}
        # both generators are in NSW
        self.assertEqual(
            penalties._regional_generation(regions.nsw,
                                           self.context.generators), 2000)
        self.assertEqual(
            penalties._regional_generation(regions.sa,
                                           self.context.generators), 0)

    def test_regional_demand(self):
        """Test _regional_demand() function."""
        for rgn in regions.All:
            # Check that there is X00 MWh of demand per region,
            # 100 MWh per polygon
            polycount = len(rgn.polygons) * 100
            self.assertEqual(penalties._regional_demand(rgn,
                                                        self.context.demand),
                             polycount)

    def test_min_regional_0(self):
        """Test min_regional() function at 0%."""
        self.context.min_regional_generation = 0
        self.assertEqual(penalties.min_regional(self.context, args), (0, 0))

    def test_min_regional_50(self):
        """Test min_regional() function at 50%."""
        self.context.min_regional_generation = 0.5
        # just two regions: NSW and SA
        self.context.regions = [regions.nsw, regions.sa]
        self.assertEqual(penalties.min_regional(self.context, args),
                         (pow(1050, 3), reasons['min-regional-gen']))

    def test_emissions(self):
        """Test emissions() function."""
        # Gen 1: 1,000 MWh (1 GWh) at 0.8 tonnes/MWh = 800 t
        # Gen 2: 1,000 MWh (1 GWh) at 0.5 tonnes/MWh = 500 t
        # Total: 1,300 tonnes
        self.context.generators[0].series_power = {n: 1 for n in range(1000)}
        self.context.generators[0].intensity = 0.800
        self.context.generators[1].series_power = {n: 1 for n in range(1000)}
        self.context.generators[1].intensity = 0.500

        self.assertEqual(penalties.emissions(self.context, args),
                         (pow(1300, 3), reasons['emissions']))

    def test_fossil(self):
        """Test fossil() function."""
        # Gen 1: 10 MWh, Gen 2: 10 MWh (Total 20MWh or 20% of demand)
        self.context.generators[0].series_power = {n: 1 for n in range(10)}
        self.context.generators[1].series_power = {n: 1 for n in range(10)}
        self.assertEqual(penalties.fossil(self.context, args), (0, 0))

        # Gen 1: 50 MWh, Gen 2: 50 MWh (Total 100MWh or 100% of demand)
        self.assertEqual(args.fossil_limit, 0.5)
        self.context.generators[0].series_power = {n: 5 for n in range(10)}
        self.context.generators[1].series_power = {n: 5 for n in range(10)}
        self.assertEqual(penalties.fossil(self.context, args),
                         (pow(50, 3), reasons['fossil']))

    def test_bioenergy(self):
        """Test bioenerge() function."""
        bio = generators.Biofuel(WILDCARD, 0)
        self.context.generators += [bio]
        # bioenergy: 0 MWh
        bio.series_power = {}
        self.assertEqual(penalties.bioenergy(self.context, args), (0, 0))
        # bioenergy: 5 MWh
        bio.series_power = {n: 1 for n in range(5)}
        self.assertEqual(penalties.bioenergy(self.context, args),
                         (pow(4, 3), reasons['bioenergy']))

    def test_hydro(self):
        """Test hydro() function."""
        hydro = generators.Hydro(WILDCARD, 0)
        self.context.generators += [hydro]
        # hydro: 0 MWh
        hydro.series_power = {}
        self.assertEqual(penalties.hydro(self.context, args), (0, 0))
        # hydro: 5 MWh
        hydro.series_power = {n: 1 for n in range(5)}
        self.assertEqual(penalties.hydro(self.context, args),
                         (pow(4, 3), reasons['hydro']))
