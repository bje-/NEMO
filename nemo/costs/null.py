# Copyright (C) 2024 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""All-zero cost class suitable for testing."""

from collections import defaultdict


class NullCosts:
    """All costs are zero. Useful for debugging."""

    # pylint: disable=unused-argument
    def __init__(self, discount=0, coal_price=0, gas_price=0, ccs_price=0):
        """Construct an all-zero costs object."""
        self.capcost_per_kw = defaultdict(lambda: 0)
        self.fixed_om_costs = defaultdict(lambda: 0)
        self.opcost_per_mwh = defaultdict(lambda: 0)
        # a dictionary of dictionary of zeros
        self.totcost_per_kwh = defaultdict(lambda: defaultdict(lambda: 0))
        self.ccs_storage_per_t = 0
        self.bioenergy_price_per_gj = 0
        self.coal_price_per_gj = 0
        self.gas_price_per_gj = 0
        self.diesel_price_per_litre = 0
        self.carbon = 0

    def annuity_factor(self, lifetime):
        """Return the annuity factor for lifetime t."""
        return 1
