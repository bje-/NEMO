# Copyright (C) 2022 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""A testsuite for the scenarios module."""

import unittest

from nemo import context, scenarios


class TestScenarios(unittest.TestCase):
    """Test scenarios.py."""

    def test_all_scenarios(self):
        """Run each scenario and then check the generator list."""
        ctx = context.Context()
        for setupfn in scenarios.supply_scenarios.values():
            with self.subTest(scenario=setupfn):
                ctx.generators = []
                setupfn(ctx)
                self.assertGreater(len(ctx.generators), 0)
                # sanity check
                self.assertLess(len(ctx.generators), 250)
