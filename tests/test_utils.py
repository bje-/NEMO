# Copyright (C) 2022 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

# pylint: disable=too-many-public-methods

"""A testsuite for the Context class."""

import os
import unittest

from nemo import context, scenarios, sim, utils


class TestUtils(unittest.TestCase):
    """Tests for utils.py functions."""

    def setUp(self):
        """Test harness setup."""
        self.context = context.Context()

    def test_plot_1(self):
        """Test plot() function."""
        try:
            os.unlink('foo.png')
        except FileNotFoundError:
            pass
        scenarios.ccgt(self.context)
        sim.run(self.context)
        utils.plot(self.context, spills=True, filename='foo.png',
                   showlegend=True)
        try:
            os.stat('foo.png')
            exists = True
        except FileNotFoundError:
            exists = False
        self.assertTrue(exists)
        os.unlink('foo.png')

    def test_plot_2(self):
        """Test plot() function with many generators."""
        try:
            os.unlink('foo.png')
        except FileNotFoundError:
            pass
        scenarios.ccgt(self.context)
        self.context.generators *= 2  # double list length
        sim.run(self.context)
        utils.plot(self.context, spills=True, filename='foo.png',
                   showlegend=True)
        try:
            os.stat('foo.png')
            exists = True
        except FileNotFoundError:
            exists = False
        self.assertTrue(exists)
        os.unlink('foo.png')
