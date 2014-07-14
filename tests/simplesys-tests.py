# Copyright (C) 2011, 2014 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

# pylint: disable=too-many-public-methods

"""A testsuite for simplesys.py."""

import math
import simplesys
import unittest


class OrigContext(simplesys.Context):
    def collectorOutput(self):
        """Calculate collector field output."""
        CM = 500
        T = self.HR % 24
        x = CM * math.sin((T - 6) / 3.8192) - self.QF
        if T < self.ISTART:
            x = 0
        if T >= self.SHUT:
            x = 0
        self.QC = 0 if x < 0 else x


class TestSIMPLESYS(unittest.TestCase):

    """Tests for SIMPLESYS."""

    def check_row(self, i, row):
        print [i] + row
        qc, qa, qs, es, qd, ql, mode = row
        c = self.context
        self.context.nexthour(150)
        self.assertEqual(c.HR - 1, i)
        self.assertEqual(round(c.QC), round(qc))
        self.assertEqual(round(c.QA), round(qa))
        self.assertEqual(round(c.QS), round(qs))
        self.assertEqual(round(c.ES), round(es))
        self.assertEqual(round(c.QD), round(qd))
        self.assertEqual(c.MODE, mode)

    def testResultsAgainstTableData(self):
        """Check results match the output given on the SIMPLESYS web page."""

        self.context = OrigContext(ep=200, qf=10, sl=10, sm=500)
        data = [[0, 150, 0, 0, 0, 150, 1],
                [0, 150, 0, 0, 0, 150, 1],
                [0, 150, 0, 0, 0, 150, 1],
                [0, 150, 0, 0, 0, 150, 1],
                [0, 150, 0, 0, 0, 150, 1],
                [0, 150, 0, 0, 0, 150, 1],
                [0, 150, 0, 0, 0, 150, 1],
                [0, 150, 0, 0, 0, 150, 1],
                [159, 0, 9, 9, 0, 150, 3],
                [344, 0, 194, 193, 0, 150, 3],
                [423, 0, 273, 456, 0, 150, 3],
                [473, 0, 54, 500, 269, 150, 3.4],
                [490, 0, 10, 500, 330, 150, 3.4],
                [473, 0, 10, 500, 313, 150, 3.4],
                [423, 0, 10, 500, 263, 150, 3.4],
                [343, 0, 10, 500, 183, 150, 3.4],
                [240, 0, 10, 500, 80, 150, 3.4],
                [119, 0, -31, 459, 0, 150, 5],
                [0, 0, -150, 299, 0, 150, 6],
                [0, 0, -150, 139, 0, 150, 6],
                [0, 21, -129, 0, 0, 150, 6.1],
                [0, 150, 0, 0, 0, 150, 1],
                [0, 150, 0, 0, 0, 150, 1],
                [0, 150, 0, 0, 0, 150, 1],
                # day 2
                [0, 150, 0, 0, 0, 150, 1],
                [0, 150, 0, 0, 0, 150, 1],
                [0, 150, 0, 0, 0, 150, 1],
                [0, 150, 0, 0, 0, 150, 1],
                [0, 150, 0, 0, 0, 150, 1],
                [0, 150, 0, 0, 0, 150, 1],
                [0, 150, 0, 0, 0, 150, 1],
                [0, 150, 0, 0, 0, 150, 1],
                [159, 0, 9, 9, 0, 150, 3],
                [344, 0, 194, 193, 0, 150, 3],
                [423, 0, 273, 456, 0, 150, 3],
                [473, 0, 54, 500, 269, 150, 3.4],
                [490, 0, 10, 500, 330, 150, 3.4],
                [473, 0, 10, 500, 313, 150, 3.4],
                [423, 0, 10, 500, 263, 150, 3.4],
                [343, 0, 10, 500, 183, 150, 3.4],
                [240, 0, 10, 500, 80, 150, 3.4],
                [119, 0, -31, 459, 0, 150, 5],
                [0, 0, -150, 299, 0, 150, 6],
                [0, 0, -150, 139, 0, 150, 6],
                [0, 21, -129, 0, 0, 150, 6.1],
                [0, 150, 0, 0, 0, 150, 1],
                [0, 150, 0, 0, 0, 150, 1],
                [0, 150, 0, 0, 0, 150, 1]]

        for i, row in enumerate(data):
            self.check_row(i, row)

    def testResultsAgainstTableData_7am_to_3pm(self):
        """Check results match for a day of limited operation (7am to 3pm)."""
        self.context = OrigContext(ep=200, qf=10, sl=10, sm=500)
        self.context.ISTART = 7
        self.context.SHUT = 15
        data = [[0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 150, 0, 0, 0, 150, 1],
                [159, 0, 9, 9, 0, 150, 3],
                [344, 0, 194, 193, 0, 150, 3],
                [423, 0, 273, 456, 0, 150, 3],
                [473, 0, 54, 500, 269, 150, 3.4],
                [490, 0, 10, 500, 330, 150, 3.4],
                [473, 0, 10, 500, 313, 150, 3.4],
                [423, 0, 10, 500, 263, 150, 3.4],
                [0, 0, 0, 490, 0, 0, 0],
                [0, 0, 0, 480, 0, 0, 0],
                [0, 0, 0, 470, 0, 0, 0],
                [0, 0, 0, 460, 0, 0, 0],
                [0, 0, 0, 450, 0, 0, 0],
                [0, 0, 0, 440, 0, 0, 0],
                [0, 0, 0, 430, 0, 0, 0],
                [0, 0, 0, 420, 0, 0, 0],
                [0, 0, 0, 410, 0, 0, 0]]

        for i, row in enumerate(data):
            self.check_row(i, row)
