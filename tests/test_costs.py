# Copyright (C) 2022 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""A testsuite for the costs module."""

import unittest

from nemo import costs


class TestCosts(unittest.TestCase):
    """Test costs.py."""

    def setUp(self):
        """Test harness setup."""
        self.discount = 0.05
        self.coal_price = 2.00
        self.gas_price = 9.00
        self.ccs_price = 27
        self.costclasses = costs.cost_scenarios.items()

    def test_annuity_factor(self):
        """Test annuity_factor function."""
        result = round(costs.annuity_factor(30, 0.05), 3)
        self.assertEqual(result, 15.372)

    def test_table(self):
        """Check all table entries are valid."""
        for _, cls in self.costclasses:
            obj = cls(self.discount, self.coal_price, self.gas_price,
                      self.ccs_price)
            if isinstance(obj, costs.NullCosts):
                # special case for NullCosts
                self.assertEqual(obj.coal_price_per_gj, 0)
                self.assertEqual(obj.gas_price_per_gj, 0)
                self.assertEqual(obj.ccs_storage_per_t, 0)
            else:
                self.assertEqual(obj.coal_price_per_gj, self.coal_price)
                self.assertEqual(obj.gas_price_per_gj, self.gas_price)
                self.assertEqual(obj.ccs_storage_per_t, self.ccs_price)

    def test_costs_sensible(self):
        """Test if cost values are sensible."""
        for _, cls in self.costclasses:
            obj = cls(self.discount, self.coal_price, self.gas_price,
                      self.ccs_price)

            for table in [obj.capcost_per_kw, obj.fixed_om_costs,
                          obj.opcost_per_mwh]:
                self.assertTrue(all(value >= 0 for value in table.values()))
