# Copyright (C) 2022 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""A testsuite for the configfile module."""

import configparser
import importlib
import os
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

    def test_has_option_p(self):
        """Test has_option_p() function."""
        self.assertTrue(configfile.has_option_p('optimiser', 'sigma'))
        self.assertFalse(configfile.has_option_p('optimiser', 'nooption'))
        self.assertFalse(configfile.has_option_p('nosection', 'sigma'))


class TestConfigFileSet(unittest.TestCase):
    """Test with NEMORC set."""

    def setUp(self):
        """Set NEMORC."""
        try:
            self.old = os.environ['NEMORC']
        except KeyError:
            self.old = None
        os.environ['NEMORC'] = '/file/not/found'

    def tearDown(self):
        """Clean up the environment."""
        if self.old is None:
            del os.environ['NEMORC']
        else:
            os.environ['NEMORC'] = self.old
        importlib.reload(configfile)

    def test_open(self):
        """Test opening a non-existent config file."""
        with self.assertRaises(FileNotFoundError):
            importlib.reload(configfile)


class TestConfigFileUnset(unittest.TestCase):
    """Test with NEMORC unset."""

    def setUp(self):
        """Unset NEMORC."""
        try:
            self.old = os.environ['NEMORC']
            del os.environ['NEMORC']
        except KeyError:
            self.old = None
        if 'NEMORC' in os.environ:
            raise OSError
        importlib.reload(configfile)

    def tearDown(self):
        """Reset the environment."""
        if self.old:
            os.environ['NEMORC'] = self.old
        importlib.reload(configfile)

    def test_open(self):
        """Test opening the default configuration file."""
        reference = configparser.ConfigParser()
        reference.read('nemo.cfg')
        self.assertEqual(reference, configfile.config)
