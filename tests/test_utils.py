# Copyright (C) 2022 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""A testsuite for the utils module."""

import io
import hashlib
import unittest

from nemo import context, scenarios, sim, utils


class TestUtils(unittest.TestCase):
    """Tests for utils.py functions."""

    def setUp(self):
        """Set up a context and run the CCGT scenario."""
        self.context = context.Context()
        scenarios.ccgt(self.context)
        sim.run(self.context)

    def test_plot(self):
        """Test plotting to the display."""
        utils.plot(self.context, spills=True)

    def test_plot_to_file(self):
        """Test plotting to file."""
        imgdata = io.BytesIO()
        utils.plot(self.context, spills=True, filename=imgdata,
                   showlegend=True)
        # rewind the stream
        imgdata.seek(0)
        hashval = hashlib.sha224(imgdata.getbuffer()).hexdigest()
        expected = '506de0f6c9f3349ae83e59c7de59cdff8465cd8bbeab29ca90d8be3c'
        self.assertEqual(hashval, expected)

    def test_plot_many(self):
        """Test plot() function with many generators."""
        scenarios.ccgt(self.context)
        self.context.generators *= 2  # double list length
        sim.run(self.context)
        imgdata = io.BytesIO()
        utils.plot(self.context, spills=True, filename=imgdata,
                   showlegend=True)
        # rewind the stream
        imgdata.seek(0)
        hashval = hashlib.sha224(imgdata.getbuffer()).hexdigest()
        expected = 'f295c962b522825dc337bcc64447f994f44cbddc79b08009a08b42a1'
        self.assertEqual(hashval, expected)
