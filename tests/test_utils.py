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
        self.context.generators *= 2  # double list length
        sim.run(self.context)
        utils._figure(self.context, spills=True, showlegend=True, xlim=None)
        return utils.plt.gcf()

    @pytest.mark.mpl_image_compare
    def test_figure_3(self):
        """Test supply/demand plot with only 7 days of data."""
        start = self.context.demand.index[0]
        end = start + timedelta(days=7)
        utils._figure(self.context, spills=True, showlegend=False,
                      xlim=(start, end))
        return utils.plt.gcf()

    def test_plot_1(self):
        """Test plot() function writing to file."""
        fname = 'test_plot_1.png'
        try:
            os.unlink(fname)
        except FileNotFoundError:
            pass
        utils.plot(self.context, filename=fname)
        try:
            os.stat(fname)
            exists = True
        except FileNotFoundError:
            exists = False
        self.assertTrue(exists)
        os.unlink(fname)
