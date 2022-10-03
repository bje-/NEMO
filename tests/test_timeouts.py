# Copyright (C) 2022 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Tests for timeout conditions."""

import configparser
import importlib
import unittest

import tcpserver

from nemo import generators, nem

PORT = 9999


class TestTraceGenerator(unittest.TestCase):
    """Test timeout handling for a trace generator (Wind)."""

    def setUp(self):
        """Start the simple TCP server."""
        self.child = tcpserver.run(PORT)
        self.url = f'http://localhost:{PORT}/data.csv'

    def tearDown(self):
        """Terminate TCP server on teardown."""
        self.child.terminate()

    def test_timeout(self):
        """Test fetching trace data from a dud server."""
        with self.assertRaises(RuntimeError):
            generators.Wind(1, 100, self.url, column=0)


class TestDemandTimeout(unittest.TestCase):
    """Test timeout handling when fetching demand data."""

    class NewConfigParser(configparser.ConfigParser):
        """A mocked up ConfigParser."""

        def newget(self, section, option):
            """Fake the demand trace location."""
            if (section, option) == ('demand', 'demand-trace'):
                return f'http://localhost:{PORT}/data.csv'
            return configparser.ConfigParser.get(self, section, option)

    def setUp(self):
        """Start the simple TCP server."""
        self.child = tcpserver.run(PORT)
        self.oldget = configparser.ConfigParser.get
        configparser.ConfigParser.get = self.NewConfigParser.newget

    def tearDown(self):
        """Terminate TCP server on teardown."""
        self.child.terminate()
        configparser.ConfigParser.get = self.oldget

    def test_timeout(self):
        """Test fetching demand data from a dud server."""
        with self.assertRaises(RuntimeError):
            importlib.reload(nem)
