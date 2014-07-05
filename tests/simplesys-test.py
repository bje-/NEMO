# -*- Python -*-
# Copyright (C) 2011, 2014 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

# pylint: disable=too-many-public-methods

"""A testsuite for simplesys.py."""

import simplesys
import unittest


class TestSIMPLESYS(unittest.TestCase):

    """Tests for SIMPLESYS."""

    def setUp(self):
        """Test harness setup."""
        self.context = simplesys.Context()

    def test_001(self):
        """Test that hour is zero."""
        self.assertEqual(self.context.HR, 0)

if __name__ == '__main__':
    unittest.main()
