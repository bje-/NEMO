# Copyright (C) 2022 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""A testsuite for generators that have storage."""

import unittest
from nemo import configfile
from nemo import generators
from nemo.polygons import WILDCARD


class TestPumpedHydro(unittest.TestCase):
    """Test pumped hydro class in detail."""
    def setUp(self):
        self.psh = generators.PumpedHydro(WILDCARD, 100, 1000, rte=1)

    def test_initialisation(self):
        self.assertTrue(self.psh.storage_p)
        self.assertEqual(self.psh.last_run, None)
        self.assertEqual(self.psh.stored, 0.5 * self.psh.maxstorage)
        self.assertEqual(self.psh.rte, 1.0)
        self.assertEqual(self.psh.maxstorage, 1000)

    def test_pump_and_generate(self):
        """Test that pumping and generating cannot happen at the same time."""
        result = self.psh.store(hour=0, power=100)
        self.assertEqual(result, 100)
        result = self.psh.step(hour=0, demand=50)
        self.assertEqual(result, (0, 0))

    def test_step(self):
        """Test step() method."""
        for i in range(10):
            result = self.psh.step(hour=i, demand=50)
            self.assertEqual(result, (50, 0))
        self.assertEqual(self.psh.stored, 0)

    def test_store(self):
        """Test store() method."""
        result = self.psh.step(hour=0, demand=100)
        self.assertEqual(result, (100, 0))
        # Can't pump and generate in the same hour.
        result = self.psh.store(hour=0, power=250)
        self.assertEqual(result, 0)

        self.psh.stored = 800
        result = self.psh.store(hour=1, power=200)
        self.assertEqual(result, 100)
        self.assertEqual(self.psh.stored, 900)
        result = self.psh.store(hour=2, power=200)
        self.assertEqual(result, 100)
        self.assertEqual(self.psh.stored, 1000)
        result = self.psh.store(hour=3, power=200)
        self.assertEqual(result, 0)
        self.assertEqual(self.psh.stored, 1000)

    def test_store_multiple(self):
        """Test store() called multiple times."""
        # For now.

    def test_reset(self):
        """Test reset() method."""
        self.psh.stored = 0
        self.psh.last_run = 123
        self.psh.reset()
        self.assertEqual(self.psh.stored, 0.5 * self.psh.maxstorage)
        self.assertEqual(self.psh.last_run, None)


class TestCST(unittest.TestCase):
    """Test CST class in detail."""
    def setUp(self):
        trace_file = configfile.get('generation', 'cst-trace')
        self.cst = generators.CentralReceiver(WILDCARD, 100, 2.5, 8,
                                              trace_file, 0)

    def test_initialisation(self):
        self.assertEqual(self.cst.capacity, 100)
        self.assertEqual(self.cst.shours, 8)
        self.assertEqual(self.cst.maxstorage,
                         self.cst.capacity * self.cst.shours)
        self.assertEqual(self.cst.stored, 0.5 * self.cst.maxstorage)
        self.assertEqual(self.cst.solarmult, 2.5)

    def test_set_capacity(self):
        self.cst.set_capacity(0.2)
        self.assertEqual(self.cst.capacity, 200)
        self.assertEqual(self.cst.maxstorage, 200 * self.cst.shours)

    def test_set_multiple(self):
        self.cst.set_multiple(3)
        self.assertEqual(self.cst.solarmult, 3)

    def test_set_storage(self):
        self.cst.set_storage(6)
        self.assertEqual(self.cst.maxstorage,
                         self.cst.capacity * self.cst.shours)
        self.assertEqual(self.cst.stored, 0.5 * self.cst.maxstorage)

    def test_reset(self):
        self.cst.stored = 0
        self.cst.reset()
        self.assertEqual(self.cst.stored, 0.5 * self.cst.maxstorage)


class TestBattery(unittest.TestCase):
    """Test Battery class in detail."""

    def test_initialisation(self):
        """Test Battery constructor."""
        batt = generators.Battery(WILDCARD, 400, 2, rte=1)
        self.assertEqual(batt.maxstorage, 800)
        self.assertEqual(batt.discharge_hours, range(18, 24))
        self.assertTrue(batt.empty_p())
        self.assertTrue(batt.storage_p)
        self.assertEqual(batt.rte, 1)
        self.assertEqual(batt.stored, 0)
        self.assertEqual(batt.runhours, 0)
        self.assertEqual(len(batt.chargehours), 0)

    def test_empty_p(self):
        """Test the empty_p() method."""
        batt = generators.Battery(WILDCARD, 800, 1, rte=1)
        self.assertEqual(batt.stored, 0)
        self.assertTrue(batt.empty_p())

    def test_full_p(self):
        """Test the full_p() method."""
        batt = generators.Battery(WILDCARD, 800, 1, rte=1)
        self.assertFalse(batt.full_p())
        batt.stored = 800
        self.assertTrue(batt.full_p())

    def test_discharge(self):
        """Test discharging outside of discharge hours."""
        # Test discontiguous hour range
        hrs = [0, 1] + list(range(18, 24))
        batt = generators.Battery(WILDCARD, 400, 8, discharge_hours=hrs, rte=1)
        batt.stored = 400
        for hour in range(24):
            result = batt.step(hour=hour, demand=50)
            # 0,0 if no discharging permitted, 50,0 otherwise
            self.assertEqual(result, (50, 0) if hour in hrs else (0, 0),
                             f'discharge failed in hour {hour}')
        self.assertTrue(batt.empty_p())

    def test_charge(self):
        """Test (normal) charging inside and outside of discharge hours."""
        # Test discontiguous hour range
        hrs = [0, 1] + list(range(18, 24))
        batt = generators.Battery(WILDCARD, 400, 8, discharge_hours=hrs, rte=1)
        for hour in range(24):
            result = batt.store(hour=hour, power=50)
            # 0 if no charging permitted, 50 otherwise
            self.assertEqual(result, 0 if hour in hrs else 50)
        self.assertEqual(batt.stored, 50 * (24 - len(hrs)))

    def test_charge_multiple(self):
        # 125 MW x 8h = 1000 MWh
        batt = generators.Battery(WILDCARD, 125, 8, discharge_hours=[], rte=1)
        result = batt.store(hour=12, power=100)
        self.assertEqual(result, 100)
        result = batt.store(hour=12, power=100)
        self.assertEqual(result, 25)
        result = batt.store(hour=12, power=100)
        self.assertEqual(result, 0)
        self.assertEqual(batt.store, 125)

    def test_to_full(self):
        """Test charging to full."""
        batt = generators.Battery(WILDCARD, 400, 2, rte=1)
        batt.stored = 700
        result = batt.store(hour=1, power=200)
        self.assertEqual(result, 100)
        self.assertEqual(batt.stored, 800)

    def test_zero_power(self):
        """Test a battery with zero capacity."""
        batt = generators.Battery(WILDCARD, 0, 1)
        result = batt.store(hour=0, power=400)
        self.assertEqual(result, 0)
        result = batt.step(hour=0, demand=400)
        self.assertEqual(result, (0, 0))
        self.assertEqual(len(batt.chargehours), 0)
        self.assertEqual(batt.runhours, 0)

    def test_round_trip_efficiency(self):
        """Test a battery with 50% round trip efficiency."""
        batt = generators.Battery(WILDCARD, 100, 4, rte=0.5)
        self.assertEqual(batt.stored, 0)
        result = batt.store(hour=0, power=100)
        self.assertEqual(result, 100)
        self.assertEqual(batt.stored, 100)
        result = batt.step(hour=18, demand=1000)
        self.assertEqual(result, (50, 0))
        self.assertEqual(batt.stored, 50)
