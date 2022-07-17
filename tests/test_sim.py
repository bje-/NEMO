# Copyright (C) 2022 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

# pylint: disable=protected-access

"""A testsuite for the penalties module."""

import unittest
import numpy as np
import pandas as pd
from nemo import sim, generators, configfile
from nemo.context import Context


class TestSim(unittest.TestCase):
    """Test sim.py."""

    def setUp(self):
        """Test harness setup."""
        self.context = Context()
        self.date_range = pd.date_range('2010-01-01', '2010-01-02', freq='H')
        self.generation = np.zeros((len(self.date_range),
                                    len(self.context.generators)))
        self.spill = np.zeros((len(self.date_range),
                               len(self.context.generators)))

    def test_sim(self):
        """Test _sim() function."""
        self.context.verbose = True
        sim._sim(self.context, self.date_range)

    def test_dispatch(self):
        """Test _dispatch() function."""
        self.context.verbose = True
        sim._dispatch(self.context, 0, 10000, self.context.generators,
                      self.generation, self.spill)
        self.assertEqual(self.spill.sum(), 0)

    def test_dispatch_pv(self):
        """Test _dispatch() function with an async generator."""
        cfg = configfile.get('generation', 'pv1axis-trace')
        pv = generators.PV1Axis(31, 10, cfg, 30)
        # put a 10 MW PV plant at the top of the merit order
        self.context.generators.insert(0, pv)
        self.generation = np.zeros((len(self.date_range),
                                    len(self.context.generators)))
        self.spill = np.zeros((len(self.date_range),
                               len(self.context.generators)))
        sim._dispatch(self.context, 0, 10000, self.context.generators,
                      self.generation, self.spill)
        self.assertEqual(self.spill.sum(), 0)

    def test_store_spills(self):
        """Test _store_spills()."""
        self.context = type('context', (), {'verbose': 0})
        self.context.verbose = True
        hydro = generators.Hydro(1, 100)
        h2store = generators.HydrogenStorage(400)
        electrolyser = generators.Electrolyser(h2store, 1, 100,
                                               efficiency=1.0)
        result = sim._store_spills(self.context, 0, hydro,
                                   [electrolyser], 50)
        self.assertEqual(result, 0.0)
        self.assertEqual(h2store.storage, 250.0)

    def test_store_spills_negative(self):
        """Test _store_spills().

        This test checks proper handling of a small negative residual
        due to floating point arithmetic.
        """
        self.context = Context()
        ccgt = generators.CCGT(31, 200)
        psh = generators.PumpedHydro(1, 250, 1000)
        psh.store = lambda hour, spl: 1e-9  # return tiny value
        self.assertEqual(sim._store_spills(self.context, 0,
                                           ccgt, [psh], 0), 0)

    def test_run_1(self):
        """Test run() with region not a list."""
        self.context.regions = None
        with self.assertRaises(ValueError):
            sim.run(self.context)

    def test_run_2(self):
        """Test run() normally."""
        sim.run(self.context)
