# Copyright (C) 2022 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""A testsuite for the Context class."""

import configparser
import unittest

from nemo import configfile


class TestConfigfile(unittest.TestCase):
    """Tests for configfile.py functions."""

    def test_get(self):
        """Test get() function."""
        self.assertEqual(configfile.get('optimiser', 'sigma'), '2.0')
        with self.assertRaises(configparser.NoSectionError):
            configfile.get('nosection', 'sigma')
        with self.assertRaises(configparser.NoOptionError):
            configfile.get('optimiser', 'nooption')

    def test_has_p(self):
        """Test has_p() function."""
        self.assertTrue(configfile.has_p('optimiser', 'sigma'))
        self.assertFalse(configfile.has_p('optimiser', 'nooption'))
        self.assertFalse(configfile.has_p('nosection', 'sigma'))
