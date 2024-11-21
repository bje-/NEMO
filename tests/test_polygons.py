# Copyright (C) 2024 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""A testsuite for the polygons.py module."""

import unittest

from nemo import polygons


class TestPolygons(unittest.TestCase):
    """Tests for polygons.py."""

    def test_centroid(self):
        """Test _centroid function."""
        notclosed = [(1, 1), (0, 0), (1, 2), (3, 3)]
        with self.assertRaises(ValueError):
            polygons._centroid(notclosed)
