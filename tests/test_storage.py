# Copyright (C) 2022 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""A testsuite for generators that have storage."""

import unittest

import pandas as pd

from nemo import configfile, generators
from nemo.polygons import WILDCARD


class TestStorage(unittest.TestCase):
    """Test Storage class."""

    def test_initialisation(self):
        """Test constructor."""
        storage = generators.Storage()
        self.assertEqual(storage.series_charge, {})

    def test_reset(self):
        """Test reset() method."""
        storage = generators.Storage()
        storage.series_charge = {0: 150}
        storage.reset()
        self.assertEqual(storage.series_charge, {})

    def test_record(self):
        """Test record() method."""
        storage = generators.Storage()
        storage.record(0, 100)
        storage.record(0, 50)
        storage.record(1, 75)
        self.assertEqual(storage.series_charge, {0: 150, 1: 75})

    def test_series(self):
        """Test series() method."""
        storage = generators.Storage()
        value = {0: 150}
        storage.series_charge = value
        series = pd.Series(value, dtype=float)
        self.assertTrue(storage.series()['charge'].equals(series))

    def test_store(self):
        """Test store() method."""
        storage = generators.Storage()
        with self.assertRaises(NotImplementedError):
            storage.store(0, 100)


class TestPumpedHydro(unittest.TestCase):
    """Test pumped hydro class in detail."""

    def setUp(self):
        """Test harness setup."""
        self.psh = generators.PumpedHydro(WILDCARD, 100, 1000, rte=1)

    def test_initialisation(self):
        """Test constructor."""
        self.assertTrue(self.psh.storage_p)
        self.assertEqual(self.psh.last_gen, None)
        self.assertEqual(self.psh.last_pump, None)
        self.assertEqual(self.psh.stored, 0.5 * self.psh.maxstorage)
        self.assertEqual(self.psh.rte, 1.0)
        self.assertEqual(self.psh.maxstorage, 1000)

    def test_series(self):
        """Test series() method."""
        series = self.psh.series()
        keys = series.keys()
        self.assertEqual(len(series), 3)
        self.assertTrue('power' in keys)
        self.assertTrue('spilled' in keys)
        self.assertTrue('charge' in keys)

    def test_pump_and_generate(self):
        """Test that pumping and generating cannot happen at the same time."""
        result = self.psh.store(hour=0, power=100)
        self.assertEqual(result, 100)
        result = self.psh.step(hour=0, demand=50)
        self.assertEqual(result, (0, 0))

    def test_pump_multiple(self):
        """Test that pump can run more than once per timestep."""
        result = self.psh.store(hour=0, power=100)
        self.assertEqual(result, 100)
        result = self.psh.store(hour=0, power=50)
        self.assertEqual(result, 0)
        self.assertEqual(self.psh.stored, 600)

    def test_step(self):
        """Test step() method."""
        for i in range(10):
            result = self.psh.step(hour=i, demand=50)
            self.assertEqual(result, (50, 0))
        self.assertEqual(self.psh.stored, 0)
        self.assertEqual(sum(self.psh.series_power.values()), 500)
        self.assertEqual(len(self.psh.series_power), 10)

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
        self.assertEqual(sum(self.psh.series_charge.values()), 200)
        self.assertEqual(len(self.psh.series_charge), 2)

    def test_store_multiple(self):
        """Test store() called multiple times."""
        # For now.

    def test_reset(self):
        """Test reset() method."""
        self.psh.series_power = {0: 200}
        self.psh.series_charge = {0: 150}
        self.psh.stored = 0
        self.psh.last_gen = 123
        self.psh.last_pump = 456
        self.psh.reset()
        self.assertEqual(self.psh.stored, 0.5 * self.psh.maxstorage)
        self.assertEqual(self.psh.last_gen, None)
        self.assertEqual(self.psh.last_pump, None)
        self.assertEqual(len(self.psh.series_charge), 0)
        self.assertEqual(len(self.psh.series_power), 0)


class TestCST(unittest.TestCase):
    """Test CST class in detail."""

    def setUp(self):
        """Test harness setup."""
        trace_file = configfile.get('generation', 'cst-trace')
        self.cst = generators.CentralReceiver(WILDCARD, 100, 2.5, 8,
                                              trace_file, 0)

    def test_initialisation(self):
        """Test CST constructor."""
        self.assertEqual(self.cst.capacity, 100)
        self.assertEqual(self.cst.shours, 8)
        self.assertEqual(self.cst.maxstorage,
                         self.cst.capacity * self.cst.shours)
        self.assertEqual(self.cst.stored, 0.5 * self.cst.maxstorage)
        self.assertEqual(self.cst.solarmult, 2.5)

    def test_set_capacity(self):
        """Test set_capacity() method."""
        self.cst.set_capacity(0.2)
        self.assertEqual(self.cst.capacity, 200)
        self.assertEqual(self.cst.maxstorage, 200 * self.cst.shours)

    def test_set_multiple(self):
        """Test set_multiple() method."""
        self.cst.set_multiple(3)
        self.assertEqual(self.cst.solarmult, 3)

    def test_set_storage(self):
        """Test set_storage() method."""
        self.cst.set_storage(6)
        self.assertEqual(self.cst.maxstorage,
                         self.cst.capacity * self.cst.shours)
        self.assertEqual(self.cst.stored, 0.5 * self.cst.maxstorage)

    def test_reset(self):
        """Test reset() method."""
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
        self.assertFalse(batt.full_p())
        self.assertTrue(batt.storage_p)
        self.assertEqual(batt.rte, 1)
        self.assertEqual(batt.stored, 0)
        self.assertEqual(batt.runhours, 0)
        self.assertEqual(len(batt.series_charge), 0)

    def test_series(self):
        """Test series() method."""
        batt = generators.Battery(WILDCARD, 400, 2)
        series = batt.series()
        keys = series.keys()
        self.assertEqual(len(series), 3)
        self.assertTrue('power' in keys)
        self.assertTrue('spilled' in keys)
        self.assertTrue('charge' in keys)

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
        nhours = 24 - len(hrs)
        self.assertEqual(batt.stored, 50 * nhours)
        self.assertEqual(sum(batt.series_charge.values()), 50 * nhours)

    def test_charge_multiple(self):
        """Test multiple calls to store()."""
        # 125 MW x 8h = 1000 MWh
        batt = generators.Battery(WILDCARD, 125, 8, discharge_hours=[], rte=1)
        result = batt.store(hour=12, power=100)
        self.assertEqual(result, 100)
        result = batt.store(hour=12, power=100)
        self.assertEqual(result, 25)
        result = batt.store(hour=12, power=100)
        self.assertEqual(result, 0)
        self.assertEqual(batt.stored, 125)

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
        self.assertEqual(len(batt.series_charge), 0)
        self.assertEqual(batt.runhours, 0)

    def test_reset(self):
        batt = generators.Battery(WILDCARD, 400, 2, rte=1)
        batt.series_power = {0: 200}
        batt.series_charge = {0: 150}
        batt.reset()
        self.assertEqual(len(batt.series_charge), 0)
        self.assertEqual(len(batt.series_power), 0)

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


class TestElectrolyser(unittest.TestCase):
    """Test Electrolyser class in detail."""

    def setUp(self):
        """Test harness setup."""
        self.tank = generators.HydrogenStorage(400, 'test')
        self.electrolyser = \
            generators.Electrolyser(self.tank, WILDCARD, 100,
                                    efficiency=1)

    def test_type_error(self):
        """Check that the wrong type raises a TypeError."""
        with self.assertRaises(TypeError):
            generators.Electrolyser(None, 1, 100, 'test')

    def test_series(self):
        """Test series() method."""
        series = self.electrolyser.series()
        keys = series.keys()
        self.assertEqual(len(series), 3)
        self.assertTrue('power' in keys)
        self.assertTrue('spilled' in keys)
        self.assertTrue('charge' in keys)

    def test_step(self):
        """Test step() method."""
        # an electrolyser is not a generator
        self.assertEqual(self.electrolyser.step(0, 100), (0, 0))
        # store 100 MWh of hydrogen
        self.assertEqual(self.electrolyser.store(0, 100), 100)
        # store another 100 MWh of hydrogen
        self.assertEqual(self.electrolyser.store(0, 100), 100)
        # tank is full, none stored
        self.assertEqual(self.electrolyser.store(0, 100), 0)
