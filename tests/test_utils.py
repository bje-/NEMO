# Copyright (C) 2022 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""A testsuite for the utils module."""

# Some protected members (eg _figure) are accessed to facilitate testing.
# pylint: disable=protected-access

import os
import unittest
from datetime import timedelta

import pytest

from nemo import context, scenarios, sim, utils


class TestUtils(unittest.TestCase):
    """Tests for utils.py functions."""

    def unlink(self, filename):
        """Unlink filename without error."""
        try:
            os.unlink(filename)
        except FileNotFoundError:
            pass

    def exists(self, filename):
        """Return True if filename exists."""
        try:
            os.stat(filename)
            return True
        except FileNotFoundError:
            return False

    def setUp(self):
        """Test harness setup."""
        self.context = context.Context()
        scenarios.ccgt(self.context)
        sim.run(self.context)

    @pytest.mark.mpl_image_compare
    def test_figure_1(self):
        """Test simple supply/demand plot."""
        utils._figure(self.context, spills=True, showlegend=True, xlim=None)
        return utils.plt.gcf()

    @pytest.mark.mpl_image_compare
    def test_figure_2(self):
        """Test supply/demand plot with many generators."""
        ngens = len(self.context.generators)
        extras = utils.MAX_PLOT_GENERATORS - ngens + 5
        self.context.generators[0].set_capacity(0.001)  # 1 MW
        self.context.generators = \
            [self.context.generators[0]] * extras + \
            self.context.generators
        sim.run(self.context)
        utils._figure(self.context, spills=True, showlegend=True, xlim=None)
        return utils.plt.gcf()

    def test_plot_1(self):
        """Test plot() function writing to file."""
        fname = 'test_plot_1.png'
        self.unlink(fname)
        utils.plot(self.context, filename=fname)
        self.assertTrue(self.exists(fname))
        os.unlink(fname)

    def test_plot_2(self):
        """Test plot with only 7 days of data."""
        start = self.context.demand.index[0]
        end = start + timedelta(days=7)
        fname = 'test_plot_2.png'
        self.unlink(fname)
        utils.plot(self.context, filename=fname, xlim=(start, end))
        self.assertTrue(self.exists(fname))
        os.unlink(fname)

    def test_plot_3(self):
        """Test plot with only 7 days of data."""
        fname = 'test_plot_3.png'
        self.unlink(fname)
        # 7 * 24 hours of timesteps
        self.context.timesteps = lambda: 7 * 24
        utils.plot(self.context, filename=fname)
        self.assertTrue(self.exists(fname))
        os.unlink(fname)
