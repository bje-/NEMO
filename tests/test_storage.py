# Copyright (C) 2022 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""A testsuite for generators that have storage."""

import unittest

import pandas as pd
from nemo import configfile, generators, storage
from nemo.polygons import WILDCARD


class TestStorage(unittest.TestCase):
    """Test Storage class."""

    def test_initialisation(self):
        """Test constructor."""
        stg = generators.Storage()
        self.assertEqual(stg.series_charge, {})

    def test_reset(self):
        """Test reset() method."""
        stg = generators.Storage()
        stg.series_charge = {0: 150}
        stg.reset()
        self.assertEqual(stg.series_charge, {})

    def test_soc(self):
        """Test soc() method in the base class."""
        stg = generators.Storage()
        with self.assertRaises(NotImplementedError):
            stg.soc()

    def test_record(self):
        """Test record() method."""
        stg = generators.Storage()
        # redefine base soc() method to avoid NotImplementedError
        stg.soc = lambda: 0.5
        stg.record(0, 100)
        stg.record(0, 50)
        stg.record(1, 75)
        self.assertEqual(stg.series_charge, {0: 150, 1: 75})
        self.assertEqual(stg.series_soc, {0: 0.5, 1: 0.5})

    def test_series(self):
        """Test series() method."""
        stg = generators.Storage()
        value = {0: 150}
        stg.series_charge = value
        series = pd.Series(value, dtype=float)
        self.assertTrue(stg.series()['charge'].equals(series))

    def test_store(self):
        """Test store() method."""
        stg = generators.Storage()
        with self.assertRaises(NotImplementedError):
            stg.store(0, 100)


class TestPumpedHydro(unittest.TestCase):
    """Test pumped hydro class in detail."""

    def setUp(self):
        """Test harness setup."""
        # Attach the reservroir to the pump and the turbine.
        # In this case, the pump and turbine are symmetric at 100 MW.
        self.reservoir = storage.PumpedHydroStorage(1000)
        self.pump = generators.PumpedHydroPump(WILDCARD, 100, self.reservoir,
                                               rte=1)
        self.turbine = generators.PumpedHydroTurbine(WILDCARD, 100,
                                                     self.reservoir)

    def test_initialisation(self):
        """Test constructor."""
        self.assertTrue(self.pump.storage_p)
        self.assertEqual(self.reservoir.last_gen, None)
        self.assertEqual(self.reservoir.last_pump, None)
        self.assertEqual(self.reservoir.storage,
                         .5 * self.reservoir.maxstorage)
        self.assertEqual(self.pump.rte, 1.0)
        self.assertEqual(self.reservoir.maxstorage, 1000)

    def test_type_exceptions(self):
        """"Test type exceptions for pump and turbine."""
        with self.assertRaises(TypeError):
            generators.PumpedHydroPump(WILDCARD, 100, None)
        with self.assertRaises(TypeError):
            generators.PumpedHydroTurbine(WILDCARD, 100, None)

    def test_soc(self):
        """Test soc() method."""
        self.assertEqual(self.pump.soc(), 0.5)

    def test_series_pump(self):
        """Test series() method for the pump."""
        series = self.pump.series()
        keys = series.keys()
        self.assertEqual(len(keys), 4)
        # use a set comparison
        self.assertLessEqual({'power', 'spilled', 'charge', 'soc'}, keys)

    def test_series_turbine(self):
        """Test series() method for the turbine."""
        series = self.turbine.series()
        keys = series.keys()
        self.assertEqual(len(keys), 2)
        # use a set comparison
        self.assertLessEqual({'power', 'spilled'}, keys)

    def test_pump_and_generate(self):
        """Test that pumping and generating cannot happen at the same time."""
        result = self.pump.store(hour=0, power=100)
        self.assertEqual(result, 100)
        result = self.turbine.step(hour=0, demand=50)
        self.assertEqual(result, (0, 0))

    def test_pump_multiple(self):
        """Test that pump can run more than once per timestep."""
        result = self.pump.store(hour=0, power=100)
        self.assertEqual(result, 100)
        result = self.pump.store(hour=0, power=50)
        self.assertEqual(result, 0)
        self.assertEqual(self.reservoir.storage, 600)

    def test_step(self):
        """Test step() method."""
        for i in range(10):
            result = self.turbine.step(hour=i, demand=50)
            self.assertEqual(result, (50, 0))
        self.assertEqual(self.reservoir.storage, 0)
        self.assertEqual(sum(self.turbine.series_power.values()), 500)
        self.assertEqual(len(self.turbine.series_power), 10)

    def test_store(self):
        """Test store() method."""
        result = self.turbine.step(hour=0, demand=100)
        self.assertEqual(result, (100, 0))
        # Can't pump and generate in the same hour.
        result = self.pump.store(hour=0, power=250)
        self.assertEqual(result, 0)

        self.reservoir.storage = 800
        result = self.pump.store(1, 200)
        self.assertEqual(result, 100)
        self.assertEqual(self.reservoir.storage, 900)
        result = self.pump.store(2, 200)
        self.assertEqual(result, 100)
        self.assertEqual(self.reservoir.storage, 1000)
        result = self.pump.store(3, 200)
        self.assertEqual(result, 0)
        self.assertEqual(self.reservoir.storage, 1000)
        self.assertEqual(sum(self.pump.series_charge.values()), 200)
        self.assertEqual(len(self.pump.series_charge), 2)

    def test_store_multiple(self):
        """Test store() called multiple times."""
        # For now.

    def test_reset(self):
        """Test reset() method."""
        self.turbine.series_power = {0: 200}
        self.pump.series_charge = {0: 150}
        self.reservoir.storage = 0
        self.reservoir.last_gen = 123
        self.reservoir.last_pump = 456
        self.pump.reset()
        self.turbine.reset()
        self.assertEqual(self.reservoir.storage,
                         .5 * self.reservoir.maxstorage)
        self.assertEqual(self.reservoir.last_gen, None)
        self.assertEqual(self.reservoir.last_pump, None)
        self.assertEqual(len(self.pump.series_charge), 0)
        self.assertEqual(len(self.turbine.series_power), 0)


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

    def setUp(self):
        """Test harness setup."""
        self.stor = storage.BatteryStorage(800)
        # to simplify testing, override the default behaviour of
        # setting a new battery to 50% SOC
        self.stor.storage = 0

    def test_initialisation(self):
        """Test Battery constructor."""
        batt = generators.BatteryLoad(WILDCARD, 400, self.stor)
        self.assertEqual(self.stor.maxstorage, 800)
        self.assertEqual(batt.discharge_hours, range(18, 24))
        self.assertTrue(batt.battery.empty_p())
        self.assertFalse(batt.battery.full_p())
        self.assertTrue(batt.storage_p)
        self.assertEqual(batt.rte, 0.95)
        self.assertEqual(len(batt.series_charge), 0)

    def test_type_error(self):
        """Check that the wrong type raises a TypeError."""
        with self.assertRaises(TypeError):
            generators.Battery(WILDCARD, 400, 2, None)
        with self.assertRaises(TypeError):
            generators.BatteryLoad(WILDCARD, 400, None)

    def test_series_batteryload(self):
        """Test series() method."""
        batt = generators.BatteryLoad(WILDCARD, 400, self.stor)
        keys = batt.series().keys()
        self.assertEqual(len(keys), 4)
        # use a set comparison
        self.assertLessEqual({'power', 'spilled', 'charge', 'soc'}, keys)

    def test_series_battery(self):
        """Test series() method."""
        batt = generators.Battery(WILDCARD, 400, 2, self.stor)
        keys = batt.series().keys()
        self.assertEqual(len(keys), 2)
        # use a set comparison
        self.assertLessEqual({'power', 'spilled'}, keys)

    def test_soc(self):
        """Test soc() method in Battery and BatteryLoad."""
        batt = generators.Battery(WILDCARD, 400, 2, self.stor)
        battload = generators.BatteryLoad(WILDCARD, 400, self.stor)
        self.assertEqual(batt.soc(), 0)
        self.stor.storage = 200
        self.assertEqual(batt.soc(), 0.25)
        self.assertEqual(battload.soc(), batt.soc())

    def test_empty_p(self):
        """Test the empty_p() method."""
        batt = generators.BatteryLoad(WILDCARD, 800, self.stor, rte=1)
        self.assertEqual(batt.battery.storage, 0)
        self.assertTrue(batt.battery.empty_p())

    def test_full_p(self):
        """Test the full_p() method."""
        batt = generators.BatteryLoad(WILDCARD, 800, self.stor, rte=1)
        self.assertFalse(batt.battery.full_p())
        self.stor.storage = 800
        self.assertTrue(batt.battery.full_p())

    def test_discharge(self):
        """Test discharging outside of discharge hours."""
        # Test discontiguous hour range
        hrs = [0, 1, *list(range(18, 24))]
        self.stor = storage.BatteryStorage(400 * 8)
        batt = generators.Battery(WILDCARD, 400, 8, self.stor,
                                  discharge_hours=hrs)
        self.stor.storage = 400
        for hour in range(24):
            result = batt.step(hour, demand=50)
            # 0,0 if no discharging permitted, 50,0 otherwise
            self.assertEqual(result, (50, 0) if hour in hrs else (0, 0),
                             f'discharge failed in hour {hour}')
        self.assertTrue(batt.battery.empty_p())

    def test_charge(self):
        """Test (normal) charging inside and outside of discharge hours."""
        # Test discontiguous hour range
        hrs = [0, 1, *list(range(18, 24))]
        rte = 0.95
        batt = generators.BatteryLoad(WILDCARD, 400, self.stor,
                                      discharge_hours=hrs, rte=rte)
        for hour in range(24):
            result = batt.store(hour=hour, power=50)
            # 0 if no charging permitted, 50 otherwise
            self.assertEqual(result, 0 if hour in hrs else 50)
        nhours = 24 - len(hrs)
        self.assertEqual(self.stor.storage, 50 * nhours * rte)
        self.assertEqual(sum(batt.series_charge.values()), 50 * nhours)

    def test_charge_multiple(self):
        """Test multiple calls to store()."""
        self.stor = storage.BatteryStorage(125 * 4)
        batt = generators.BatteryLoad(WILDCARD, 125, self.stor,
                                      discharge_hours=[], rte=1)
        result = batt.store(12, 100)
        self.assertEqual(result, 100)
        result = batt.store(12, 100)
        self.assertEqual(result, 25)
        result = batt.store(12, 100)
        self.assertEqual(result, 0)
        self.assertEqual(self.stor.storage, 250 + 125)

    def test_to_full(self):
        """Test charging to full."""
        batt = generators.BatteryLoad(WILDCARD, 400, self.stor, rte=1)
        self.stor.storage = 700
        result = batt.store(hour=0, power=200)
        self.assertEqual(result, 100)
        self.assertEqual(self.stor.storage, 800)

    def test_reset(self):
        """Test battery reset() method."""
        batt = generators.BatteryLoad(WILDCARD, 400, self.stor, rte=1)
        batt.series_power = {0: 200}
        batt.series_charge = {0: 150}
        batt.reset()
        self.assertEqual(len(batt.series_charge), 0)
        self.assertEqual(len(batt.series_power), 0)

    def test_round_trip_efficiency(self):
        """Test a battery with 50% round trip efficiency."""
        batt = generators.BatteryLoad(WILDCARD, 100, self.stor, rte=0.5)
        self.assertEqual(self.stor.storage, 0)
        result = batt.store(hour=0, power=100)
        self.assertEqual(result, 100)
        self.assertEqual(self.stor.storage, 50)


class TestElectrolyser(unittest.TestCase):
    """Test Electrolyser class in detail."""

    def setUp(self):
        """Test harness setup."""
        self.tank = storage.HydrogenStorage(400, 'test')
        self.electrolyser = \
            generators.Electrolyser(self.tank, WILDCARD, 100,
                                    efficiency=1)

    def test_soc(self):
        """Test tank and electrolyser soc() method."""
        tank_soc = self.tank.soc()
        self.assertEqual(tank_soc, 0.5)
        self.assertEqual(self.electrolyser.soc(), tank_soc)

    def test_type_error(self):
        """Check that the wrong type raises a TypeError."""
        with self.assertRaises(TypeError):
            generators.Electrolyser(None, 1, 100, 'test')

    def test_series(self):
        """Test series() method."""
        series = self.electrolyser.series()
        keys = series.keys()
        self.assertEqual(len(keys), 4)
        # use a set comparison
        self.assertLessEqual({'power', 'spilled', 'charge', 'soc'}, keys)

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
