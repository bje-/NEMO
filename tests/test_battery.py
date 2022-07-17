# Copyright (C) 2022 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""A testsuite for the Battery generator."""

import unittest
from nemo import generators
from nemo import polygons


class TestBattery(unittest.TestCase):
    """Test Battery class in detail."""

    def test_initialisation(self):
        """Test Battery constructor."""
        batt = generators.Battery(polygons.WILDCARD, 400, 2, rte=1)
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
        batt = generators.Battery(polygons.WILDCARD, 800, 1, rte=1)
        self.assertEqual(batt.stored, 0)
        self.assertTrue(batt.empty_p())

    def test_full_p(self):
        """Test the full_p() method."""
        batt = generators.Battery(polygons.WILDCARD, 800, 1, rte=1)
        self.assertFalse(batt.full_p())
        batt.stored = 800
        self.assertTrue(batt.full_p())

    def test_discharge_outside_hours(self):
        """Test discharging outside of discharge hours."""
        batt = generators.Battery(polygons.WILDCARD, 400, 2, rte=1)
        batt.stored = 400
        result = batt.step(hour=0, demand=200)
        self.assertEqual(result, (0, 0))

    def test_normal_charging(self):
        """Test (normal) charging outside of discharge hours."""
        batt = generators.Battery(polygons.WILDCARD, 400, 2, rte=1)
        result = batt.store(hour=0, power=400)
        self.assertEqual(result, 400)

    def test_charging_in_hours(self):
        """Test charging during discharge hours."""
        batt = generators.Battery(polygons.WILDCARD, 400, 2, rte=1)
        result = batt.store(hour=19, power=200)
        self.assertEqual(result, 0)

    def test_to_full(self):
        """Test charging to full."""
        batt = generators.Battery(polygons.WILDCARD, 400, 2, rte=1)
        batt.stored = 700
        result = batt.store(hour=1, power=200)
        self.assertEqual(result, 100)
        self.assertEqual(batt.stored, 800)

    def test_zero_power(self):
        """Test a battery with zero capacity."""
        batt = generators.Battery(polygons.WILDCARD, 0, 1)
        result = batt.store(hour=0, power=400)
        self.assertEqual(result, 0)
        result = batt.step(hour=0, demand=400)
        self.assertEqual(result, (0, 0))
        self.assertEqual(len(batt.chargehours), 0)
        self.assertEqual(batt.runhours, 0)

    def test_round_trip_efficiency(self):
        """Test a battery with 50% round trip efficiency."""
        batt = generators.Battery(polygons.WILDCARD, 100, 4, rte=0.5)
        self.assertEqual(batt.stored, 0)
        result = batt.store(hour=0, power=100)
        self.assertEqual(result, 100)
        self.assertEqual(batt.stored, 100)
        result = batt.step(hour=18, demand=1000)
        self.assertEqual(result, (50, 0))
        self.assertEqual(batt.stored, 50)
