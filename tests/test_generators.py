# Copyright (C) 2022 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""A testsuite for the generators module."""

import os
import unittest
import inspect
import numpy as np
from nemo import generators
from nemo import costs

hydrogen_storage = generators.HydrogenStorage(1000, "H2 store")

dummy_arguments = {'self': None,
                   'polygon': 31,
                   'capacity': 100,
                   'filename': 'file:tracedata.csv',
                   'column': 0,
                   'label': 'a label',
                   'build_limit': 1000,
                   'maxstorage': 1000,
                   'discharge_hours': range(18, 21),
                   'rte': 0.8,
                   'heatrate': 0.3,
                   'intensity': 0.7,
                   'capture': 0.85,
                   'solarmult': 2.5,
                   'shours': 8,
                   'cost_per_mwh': 1000,
                   'kwh_per_litre': 10,
                   'tank': hydrogen_storage,
                   'efficiency': 30}


class TestGenerators(unittest.TestCase):
    """Test generators.py."""

    def setUp(self):
        """Test harness setup."""
        self.tracefile = 'tracedata.csv'
        with open(self.tracefile, 'w', encoding='utf-8') as tracefile:
            for i in range(100):
                print(f'{0.01 * i:.2f},', file=tracefile)

        self.years = 1
        self.costs = costs.NullCosts()
        self.classes = inspect.getmembers(generators, inspect.isclass)
        self.generators = []

        for (cls, clstype) in self.classes:
            if cls in ['Generator', 'Patch', 'HydrogenStorage']:
                # imported via matplotlib
                continue
            args = inspect.getfullargspec(clstype.__init__).args
            arglist = []
            for arg in args:
                if dummy_arguments[arg] is not None:
                    arglist.append(dummy_arguments[arg])
            obj = clstype(*arglist)
            self.generators.append(obj)

    def tearDown(self):
        """Remove tracefile on teardown."""
        os.unlink(self.tracefile)

    def test_step(self):
        """Test step() method."""
        for gen in self.generators:
            for hour in range(0, 10):
                gen.step(hour, 20)

    def test_store(self):
        """Test store() method."""
        for gen in self.generators:
            if gen.storage_p:
                for hour in range(0, 10):
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
            gen.lcoe(self.costs, self.years)

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
            years = self.years

        context = MyContext()
        for gen in self.generators:
            gen.series_power = {n: 10 for n in range(10)}  # 10 MW * 10 h
            gen.series_spilled = {n: 1 for n in range(10)}  # 1 MW * 10 h
            output = gen.summary(context)
            self.assertIn('supplied 100.00 MWh', output)
            self.assertIn('surplus 10.00 MWh', output)
            self.assertIn('CF 10.0%', output)

    def test_set_capacity(self):
        """Test set_capacity() method."""
        for gen in self.generators:
            gen.set_capacity(0.2)
        self.assertEqual(self.generators[0].capacity, 200)

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
            elif isinstance(gen, generators.Battery):
                testvalue = 4
                gen.set_storage(testvalue)
                self.assertEqual(gen.maxstorage, gen.capacity * testvalue)
                self.assertEqual(gen.stored, 0)

    def test_str(self):
        """Test __str__() method."""
        for gen in self.generators:
            str(gen)

    def test_repr(self):
        """Test __repr__() method."""
        for gen in self.generators:
            repr(gen)
