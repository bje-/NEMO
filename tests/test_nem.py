# Copyright (C) 2022 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""A testsuite for the generators module."""

import importlib
import configparser
import unittest
import tcpserver
from nemo import nem

PORT = 9998


class MockConfigParser(configparser.ConfigParser):
    """A mocked up ConfigParser."""

    def newget(self, section, option):
        """Fake the demand trace location."""
        if (section, option) == ('demand', 'demand-trace'):
            return f'http://localhost:{PORT}/data.csv'
        return configparser.ConfigParser.get(self, section, option)


class TestDemandError(unittest.TestCase):
    """Test HTTP error handling for loading demand."""

    def setUp(self):
        """Start the simple TCP server."""
        self.child = tcpserver.run(PORT, "http400")
        self.oldget = configparser.ConfigParser.get
        configparser.ConfigParser.get = MockConfigParser.newget

    def tearDown(self):
        """Terminate TCP server on teardown."""
        self.child.terminate()
        configparser.ConfigParser.get = self.oldget

    def test_http_error(self):
        """Test fetching demand data from a dud server."""
        with self.assertRaisesRegex(RuntimeError, "HTTP 400"):
            importlib.reload(nem)


class TestDemandTimeout(unittest.TestCase):
    """Test timeout handling when fetching demand data."""

    def setUp(self):
        """Start the simple TCP server."""
        self.child = tcpserver.run(PORT, "block")
        self.oldget = configparser.ConfigParser.get
        configparser.ConfigParser.get = MockConfigParser.newget

    def tearDown(self):
        """Terminate TCP server on teardown."""
        self.child.terminate()
        configparser.ConfigParser.get = self.oldget

    def test_timeout(self):
        """Test fetching demand data from a dud server."""
        with self.assertRaises(RuntimeError):
            importlib.reload(nem)
