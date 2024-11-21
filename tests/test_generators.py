# Copyright (C) 2022 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""A testsuite for the generators module."""

import inspect
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
import tcpserver

from nemo import costs, generators, regions, storage

PORT = 9998
battery_storage = storage.BatteryStorage(800, "Li-ion store")
hydrogen_storage = storage.HydrogenStorage(1000, "H2 store")
pumped_storage = storage.PumpedHydroStorage(1000, "PSH store")

dummy_arguments = {'axes': 0,
                   'battery': battery_storage,
                   'build_limit': 1000,
                   'capacity': 100,
                   'capture': 0.85,
                   'column': 0,
                   'cost_per_mwh': 1000,
                   'discharge_hours': range(18, 21),
                   'efficiency': 30,
                   'filename': 'tracedata.csv',
                   'heatrate': 0.3,
                   'intensity': 0.7,
                   'kwh_per_litre': 10,
                   'label': 'a label',
                   'maxstorage': 1000,
                   'polygon': 31,
                   'reservoirs': pumped_storage,
                   'rte': 0.8,
                   'self': None,
                   'shours': 8,
                   'solarmult': 2.5,
                   'tank': hydrogen_storage}

# This list should contain every generator class in generators.py.
# This ensures that the linters will not report any classes as unused
# because they do not feature in any scenario (eg, GreenPower). They
# are, however, tested below via Python introspection (and hence not
# named explicitly in source code).

classlist = [generators.Battery, generators.BatteryLoad,
             generators.Behind_Meter_PV, generators.Biofuel,
             generators.Biomass, generators.Black_Coal,
             generators.Block, generators.CCGT, generators.CCGT_CCS,
             generators.CCS, generators.CST,
             generators.CSVTraceGenerator, generators.CentralReceiver,
             generators.Coal_CCS, generators.DemandResponse,
             generators.Diesel, generators.Electrolyser,
             generators.Fossil, generators.Fuelled,
             generators.Generator, generators.Geothermal,
             generators.Geothermal_EGS, generators.Geothermal_HSA,
             generators.Hydro, generators.HydrogenGT, generators.OCGT,
             generators.PV, generators.PV1Axis,
             generators.ParabolicTrough, generators.Patch,
             generators.PumpedHydroPump,
             generators.PumpedHydroTurbine, generators.Storage,
             generators.TraceGenerator, generators.Wind,
             generators.WindOffshore]


class TestGenerators(unittest.TestCase):
    """Test generators.py."""

    def setUp(self):
        """Test harness setup."""
        self.tracefile = 'tracedata.csv'
        with Path(self.tracefile).open('w', encoding='utf-8') as tracefile:
            for i in range(100):
                print(f'{0.01 * i:.2f}, 0', file=tracefile)

        self.years = lambda: 1
        self.costs = costs.NullCosts()
        self.classes = [cls for cls in
                        inspect.getmembers(generators, inspect.isclass)
                        if cls[1].__module__ == generators.__name__]
        self.generators = []

        for (cls, clstype) in self.classes:
            # Skip abstract classes
            if cls in ['Generator', 'TraceGenerator',
                       'CSVTraceGenerator', 'Storage']:
                continue

            # check that every class in generators.py is in classlist
            self.assertIn(clstype, classlist)

            args = inspect.getfullargspec(clstype.__init__).args
            arglist = [dummy_arguments[arg] for arg in args if
                       dummy_arguments[arg] is not None]
            obj = clstype(*arglist)
            self.generators.append(obj)

    def tearDown(self):
        """Remove tracefile on teardown."""
        path = Path(self.tracefile)
        path.unlink()

    def test_series(self):
        """Test series() method."""
        gen = generators.Generator(1, 0, 'label')
        # fake up these attributes
        gen.series_power = {1: 100}
        gen.series_spilled = {1: 200}
        # .. and then call gen.series()
        series1 = pd.Series(gen.series_power, dtype=float)
        self.assertTrue(gen.series()['power'].equals(other=series1))
        series2 = pd.Series(gen.series_spilled, dtype=float)
        self.assertTrue(gen.series()['spilled'].equals(other=series2))

    def test_step_abstract(self):
        """Test step() method in the abstract Generator class."""
        gen = generators.Generator(1, 0, 'label')
        with self.assertRaises(NotImplementedError):
            gen.step(0, 100)

    def test_step(self):
        """Test step() method."""
        for gen in self.generators:
            for hour in range(10):
                gen.step(hour, 20)

    def test_store(self):
        """Test store() method."""
        for gen in self.generators:
            if gen.storage_p:
                for hour in range(10):
                    gen.step(hour, 20)

    def test_capcost(self):
        """Test capcost() method."""
        for gen in self.generators:
            gen.capcost(self.costs)

    def test_capfactor_nan(self):
        """Test capfactor() NaN case."""
        gen = generators.Generator(1, 0, 'label')
        self.assertTrue(np.isnan(gen.capfactor()))

    def test_capfactor(self):
        """Test capfactor() method."""
        for gen in self.generators:
            # 10 MW for 10 hours = 100 MWh
            gen.series_power = {n: 10 for n in range(10)}
            self.assertEqual(gen.capfactor(), 10)

    def test_lcoe(self):
        """Test lcoe() method."""
        for gen in self.generators:
            # 10 MWh for 10 hours = 100 MWh
            gen.series_power = {n: 10 for n in range(10)}
            gen.lcoe(self.costs, self.years())

    def test_reset(self):
        """Test reset() method."""
        for gen in self.generators:
            gen.series_power = {n: 10 for n in range(10)}
            gen.series_spilled = {n: 10 for n in range(10)}
        for gen in self.generators:
            gen.reset()
        for gen in self.generators:
            self.assertEqual(len(gen.series_power), 0)
            self.assertEqual(len(gen.series_spilled), 0)

    def test_summary(self):
        """Test summary() method."""
        class MyContext:
            """A mocked up Context class."""

            costs = self.costs

            def years(self):
                """Mock up a version of the Context years method."""
                return 1

        context = MyContext()
        for gen in self.generators:
            gen.series_power = {n: 10 for n in range(10)}  # 10 MW * 10 h
            gen.series_spilled = {n: 1 for n in range(10)}  # 1 MW * 10 h
            # fake up a capcost() method for testing summary()
            gen.capcost = lambda _: 100
            output = gen.summary(context)
            self.assertIn('capcost $100,', output)
            self.assertIn('supplied 100.00 MWh', output)
            self.assertIn('surplus 10.00 MWh', output)
            self.assertIn('CF 10.0%', output)

    def test_set_capacity(self):
        """Test set_capacity() method."""
        initial_cap = self.generators[0].capacity
        for gen in self.generators:
            gen.set_capacity(0.2)
            self.assertEqual(gen.capacity, 200)
            # put capacity back to its initial value
            gen.set_capacity(initial_cap / 1000)
            self.assertEqual(gen.capacity, initial_cap)

    def test_set_storage(self):
        """Test set_storage() method."""
        # set_storage does not have a uniform calling convention for
        # different generator types, so handle each case specifically.
        for gen in self.generators:
            if isinstance(gen, generators.CST):
                testvalue = 10
                gen.set_storage(testvalue)
                self.assertEqual(gen.shours, testvalue)
                self.assertEqual(gen.maxstorage, gen.capacity * testvalue)
                self.assertEqual(gen.stored, 0.5 * gen.maxstorage)

    def test_str(self):
        """Test __str__() method."""
        for gen in self.generators:
            str(gen)

    def test_repr(self):
        """Test __repr__() method."""
        for gen in self.generators:
            repr(gen)


class TestGeneratorExceptions(unittest.TestCase):
    """Test exceptions raised by base Generator constructor."""

    def test_negative_capacity(self):
        """Capacity less than zero should raise ValueError."""
        with self.assertRaises(ValueError):
            generators.Generator(0, -1, 'label')

    def test_polygon_type(self):
        """A polygon that is a region should raise TypeError."""
        with self.assertRaises(TypeError):
            poly = regions.nsw
            generators.Generator(poly, 100, 'label')

    def test_polygon_number(self):
        """A polygon out of range should raise AssertionError."""
        with self.assertRaises(AssertionError):
            poly = 1000
            generators.Generator(poly, 100, 'label')

    def test_ccs_capture_range(self):
        """A capture fraction out of range should raise ValueError."""
        with self.assertRaises(ValueError):
            generators.CCS(1, 100, intensity=0.5, capture=1.2)
        with self.assertRaises(ValueError):
            generators.CCS(1, 100, intensity=0.5, capture=-0.2)

    def test_batteryload_store_negative(self):
        """Storing power <= 0 should raise a ValueError."""
        battery = storage.BatteryStorage(100)
        gen = generators.BatteryLoad(1, 100, battery)
        with self.assertRaises(ValueError):
            gen.store(hour=0, power=-1)
        with self.assertRaises(ValueError):
            gen.store(hour=0, power=0)

    def test_battery_shours(self):
        """Hours that are not in [1,2,4,8] should raise ValueError."""
        battery = storage.BatteryStorage(100)
        with self.assertRaises(ValueError):
            generators.Battery(1, 100, 3, battery)

    def test_battery_capacity(self):
        """If capacity * shours != battery size, raise ValueError."""
        battery = storage.BatteryStorage(100)
        with self.assertRaises(ValueError):
            # 120 MW x 1 hour = 120 MWh ( != 100 MWh)
            generators.Battery(1, 120, 1, battery)

    def test_battery_capcost(self):
        """Hours that are not in [1,2,4,8] should raise ValueError."""
        battery = storage.BatteryStorage(100)
        gen = generators.Battery(1, 100, 1, battery)
        nullcosts = costs.NullCosts()
        with self.assertRaises(ValueError):
            gen.shours = 3
            gen.capcost(nullcosts)

    def test_hydrogen_gt_tank(self):
        """Tank that is not a HydrogenStorage should raise TypeError."""
        with self.assertRaises(TypeError):
            tank = None
            generators.HydrogenGT(tank, 1, 100)


class TestTraceGeneratorTimeout(unittest.TestCase):
    """Test timeout handling for a trace generator (Wind)."""

    def setUp(self):
        """Start the simple TCP server."""
        self.child = tcpserver.run(PORT, "block")
        self.url = f'http://localhost:{PORT}/data.csv'

    def tearDown(self):
        """Terminate TCP server on teardown."""
        self.child.terminate()

    def test_timeout(self):
        """Test fetching trace data from a dud server."""
        with self.assertRaises(TimeoutError):
            generators.Wind(1, 100, self.url, column=0)


class TestTraceGeneratorError(unittest.TestCase):
    """Test HTTP error handling for a trace generator."""

    def setUp(self):
        """Start the simple TCP server."""
        self.child = tcpserver.run(PORT, "http400")
        self.url = f'http://localhost:{PORT}/data.csv'

    def tearDown(self):
        """Terminate TCP server on teardown."""
        self.child.terminate()

    def test_timeout(self):
        """Test fetching trace data from a dud server."""
        with self.assertRaisesRegex(ConnectionError, "HTTP 400"):
            generators.Wind(1, 100, self.url, column=0)
