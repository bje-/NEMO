# Copyright (C) 2022 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""A testsuite for the regions module."""

import copy
import unittest

from nemo import regions


class TestRegions(unittest.TestCase):
    """Tests for Region methods."""

    def test_region(self):
        """Test Region class."""
        rgn = regions.Region(0, 'NSW1', 'New South Wales')
        assert str(rgn) == 'NSW1'
        lst = range(5)
        assert lst[rgn] == 0

    def test_region_copy(self):
        """Check for no copying."""
        sa1 = regions.sa
        sa1copy = copy.copy(sa1)
        assert sa1 is sa1copy

    def test_region_deepcopy(self):
        """Check for no deepcopying."""
        sa1 = regions.sa
        sa1copy = copy.deepcopy(sa1)
        assert sa1 is sa1copy
