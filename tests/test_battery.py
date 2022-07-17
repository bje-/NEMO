# Copyright (C) 2022 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""A testsuite for the Battery generator."""

import unittest
from nemo import generators
from nemo.polygons import WILDCARD


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
        for hr in range(24):
            result = batt.step(hour=hr, demand=50)
            # 0,0 if no discharging permitted, 50,0 otherwise
            self.assertEqual(result, (50, 0) if hr in hrs else (0, 0),
                             f'discharge failed in hour {hr}')
        self.assertTrue(batt.empty_p())

    def test_charge(self):
        """Test (normal) charging inside and outside of discharge hours."""
        # Test discontiguous hour range
        hrs = [0, 1] + list(range(18, 24))
        batt = generators.Battery(WILDCARD, 400, 8, discharge_hours=hrs, rte=1)
        for hr in range(24):
            result = batt.store(hour=hr, power=50)
            # 0 if no charging permitted, 50 otherwise
            self.assertEqual(result, 0 if hr in hrs else 50)
        self.assertEqual(batt.stored, 50 * (24 - len(hrs)))

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
