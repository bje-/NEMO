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

    def setUp(self):
        """Test harness setup."""
        self.stg = generators.Storage()

    def test_initialisation(self):
        """Test constructor."""
        assert self.stg.series_charge == {}

    def test_reset(self):
        """Test reset() method."""
        self.stg.series_charge = {0: 150}
        self.stg.reset()
        assert self.stg.series_charge == {}

    def test_soc(self):
        """Test soc() method in the base class."""
        with self.assertRaises(NotImplementedError):
            self.stg.soc()

    def test_record(self):
        """Test record() method."""
        # redefine base soc() method to avoid NotImplementedError
        self.stg.soc = lambda: 0.5
        self.stg.record(0, 100)
        self.stg.record(0, 50)
        self.stg.record(1, 75)
        assert self.stg.series_charge == {0: 150, 1: 75}
        assert self.stg.series_soc == {0: 0.5, 1: 0.5}

    def test_series(self):
        """Test series() method."""
        value = {0: 150}
        self.stg.series_charge = value
        series = pd.Series(value, dtype=float)
        assert self.stg.series()['charge'].equals(series)

    def test_store(self):
        """Test store() method."""
        with self.assertRaises(NotImplementedError):
            self.stg.store(0, 100)


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
        assert self.pump.storage_p
        assert self.reservoir.last_gen is None
        assert self.reservoir.last_pump is None
        assert self.reservoir.storage == .5 * \
            self.reservoir.maxstorage
        assert self.pump.rte == 1.0
        assert self.reservoir.maxstorage == 1000

    def test_type_exceptions(self):
        """"Test type exceptions for pump and turbine."""
        with self.assertRaises(TypeError):
            generators.PumpedHydroPump(WILDCARD, 100, None)
        with self.assertRaises(TypeError):
            generators.PumpedHydroTurbine(WILDCARD, 100, None)

    def test_soc(self):
        """Test soc() method."""
        assert self.pump.soc() == 0.5

    def test_series_pump(self):
        """Test series() method for the pump."""
        series = self.pump.series()
        keys = series.keys()
        assert len(keys) == 4
        # use a set comparison
        assert {'power', 'spilled', 'charge', 'soc'} <= keys

    def test_series_turbine(self):
        """Test series() method for the turbine."""
        series = self.turbine.series()
        keys = series.keys()
        assert len(keys) == 2
        # use a set comparison
        assert {'power', 'spilled'} <= keys

    def test_pump_and_generate(self):
        """Test that pumping and generating cannot happen at the same time."""
        result = self.pump.store(hour=0, power=100)
        assert result == 100
        result = self.turbine.step(hour=0, demand=50)
        assert result == (0, 0)

    def test_pump_multiple(self):
        """Test that pump can run more than once per timestep."""
        result = self.pump.store(hour=0, power=100)
        assert result == 100
        result = self.pump.store(hour=0, power=50)
        assert result == 0
        assert self.reservoir.storage == 600

    def test_step(self):
        """Test step() method."""
        for i in range(10):
            result = self.turbine.step(hour=i, demand=50)
            assert result == (50, 0)
        assert self.reservoir.storage == 0
        assert sum(self.turbine.series_power.values()) == 500
        assert len(self.turbine.series_power) == 10

    def test_store(self):
        """Test store() method."""
        result = self.turbine.step(hour=0, demand=100)
        assert result == (100, 0)
        # Can't pump and generate in the same hour.
        result = self.pump.store(hour=0, power=250)
        assert result == 0

        self.reservoir.storage = 800
        result = self.pump.store(1, 200)
        assert result == 100
        assert self.reservoir.storage == 900
        result = self.pump.store(2, 200)
        assert result == 100
        assert self.reservoir.storage == 1000
        result = self.pump.store(3, 200)
        assert result == 0
        assert self.reservoir.storage == 1000
        assert sum(self.pump.series_charge.values()) == 200
        assert len(self.pump.series_charge) == 2

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
        assert self.reservoir.storage == \
            .5 * self.reservoir.maxstorage
        assert self.reservoir.last_gen is None
        assert self.reservoir.last_pump is None
        assert len(self.pump.series_charge) == 0
        assert len(self.turbine.series_power) == 0


class TestCST(unittest.TestCase):
    """Test CST class in detail."""

    def setUp(self):
        """Test harness setup."""
        trace_file = configfile.get('generation', 'cst-trace')
        self.cst = generators.CentralReceiver(WILDCARD, 100, 2.5, 8,
                                              trace_file, 0)

    def test_initialisation(self):
        """Test CST constructor."""
        assert self.cst.capacity == 100
        assert self.cst.shours == 8
        assert self.cst.maxstorage == \
            self.cst.capacity * self.cst.shours
        assert self.cst.stored == 0.5 * self.cst.maxstorage
        assert self.cst.solarmult == 2.5

    def test_set_capacity(self):
        """Test set_capacity() method."""
        self.cst.set_capacity(0.2)
        assert self.cst.capacity == 200
        assert self.cst.maxstorage == 200 * self.cst.shours

    def test_set_multiple(self):
        """Test set_multiple() method."""
        self.cst.set_multiple(3)
        assert self.cst.solarmult == 3

    def test_set_storage(self):
        """Test set_storage() method."""
        self.cst.set_storage(6)
        assert self.cst.maxstorage == \
            self.cst.capacity * self.cst.shours
        assert self.cst.stored == 0.5 * self.cst.maxstorage

    def test_reset(self):
        """Test reset() method."""
        self.cst.stored = 0
        self.cst.reset()
        assert self.cst.stored == 0.5 * self.cst.maxstorage


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
        assert self.stor.maxstorage == 800
        assert batt.discharge_hours == range(18, 24)
        assert batt.battery.empty_p()
        assert not batt.battery.full_p()
        assert batt.storage_p
        assert batt.rte == 0.95
        assert len(batt.series_charge) == 0

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
        assert len(keys) == 4
        # use a set comparison
        assert {'power', 'spilled', 'charge', 'soc'} <= keys

    def test_series_battery(self):
        """Test series() method."""
        batt = generators.Battery(WILDCARD, 400, 2, self.stor)
        keys = batt.series().keys()
        assert len(keys) == 2
        # use a set comparison
        assert {'power', 'spilled'} <= keys

    def test_soc(self):
        """Test soc() method in Battery and BatteryLoad."""
        batt = generators.Battery(WILDCARD, 400, 2, self.stor)
        battload = generators.BatteryLoad(WILDCARD, 400, self.stor)
        assert batt.soc() == 0
        self.stor.storage = 200
        assert batt.soc() == 0.25
        assert battload.soc() == batt.soc()

    def test_empty_p(self):
        """Test the empty_p() method."""
        batt = generators.BatteryLoad(WILDCARD, 800, self.stor, rte=1)
        assert batt.battery.storage == 0
        assert batt.battery.empty_p()

    def test_full_p(self):
        """Test the full_p() method."""
        batt = generators.BatteryLoad(WILDCARD, 800, self.stor, rte=1)
        assert not batt.battery.full_p()
        self.stor.storage = 800
        assert batt.battery.full_p()

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
        assert batt.battery.empty_p()

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
            assert result == 0 if hour in hrs else 50
        nhours = 24 - len(hrs)
        assert self.stor.storage == 50 * nhours * rte
        assert sum(batt.series_charge.values()) == 50 * nhours

    def test_charge_multiple(self):
        """Test multiple calls to store()."""
        self.stor = storage.BatteryStorage(125 * 4)
        batt = generators.BatteryLoad(WILDCARD, 125, self.stor,
                                      discharge_hours=[], rte=1)
        result = batt.store(12, 100)
        assert result == 100
        result = batt.store(12, 100)
        assert result == 25
        result = batt.store(12, 100)
        assert result == 0
        assert self.stor.storage == 250 + 125

    def test_to_full(self):
        """Test charging to full."""
        batt = generators.BatteryLoad(WILDCARD, 400, self.stor, rte=1)
        self.stor.storage = 700
        result = batt.store(hour=0, power=200)
        assert result == 100
        assert self.stor.storage == 800

    def test_reset(self):
        """Test battery reset() method."""
        batt = generators.BatteryLoad(WILDCARD, 400, self.stor, rte=1)
        batt.series_power = {0: 200}
        batt.series_charge = {0: 150}
        batt.reset()
        assert len(batt.series_charge) == 0
        assert len(batt.series_power) == 0

    def test_round_trip_efficiency(self):
        """Test a battery with 50% round trip efficiency."""
        batt = generators.BatteryLoad(WILDCARD, 100, self.stor, rte=0.5)
        assert self.stor.storage == 0
        result = batt.store(hour=0, power=100)
        assert result == 100
        assert self.stor.storage == 50


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
        assert tank_soc == 0.5
        assert self.electrolyser.soc() == tank_soc

    def test_type_error(self):
        """Check that the wrong type raises a TypeError."""
        with self.assertRaises(TypeError):
            generators.Electrolyser(None, 1, 100, 'test')

    def test_series(self):
        """Test series() method."""
        series = self.electrolyser.series()
        keys = series.keys()
        assert len(keys) == 4
        # use a set comparison
        assert {'power', 'spilled', 'charge', 'soc'} <= keys

    def test_step(self):
        """Test step() method."""
        # an electrolyser is not a generator
        assert self.electrolyser.step(0, 100) == (0, 0)
        # store 100 MWh of hydrogen
        assert self.electrolyser.store(0, 100) == 100
        # store another 100 MWh of hydrogen
        assert self.electrolyser.store(0, 100) == 100
        # tank is full, none stored
        assert self.electrolyser.store(0, 100) == 0
