# Copyright (C) 2024 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""CSIRO GenCost costs for 2020-21."""

from nemo import generators as tech

from .gencost import GenCost

# We use class names here that upset Pylint.
# pylint: disable=invalid-name


class GenCost2021(GenCost):
    """GenCost 2020-21 costs.

    Source:
    CSIRO GenCost 2020-21 report
    https://data.csiro.au/collections/collection/CIcsiro:44228
    """

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost.__init__(self, discount, coal_price, gas_price, ccs_price)

        # Fixed O&M (FOM) costs
        self.fixed_om_costs.update({
            tech.CentralReceiver: 120.0})

        # Variable O&M (VOM) costs
        self.opcost_per_mwh.update({
            tech.OCGT: 2.4})


class GenCost2021_2020(GenCost2021):
    """GenCost 2020-21 costs for 2020."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2021.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 4450
        table[tech.CCGT] = 1743
        table[tech.CCGT_CCS] = 4396
        table[tech.CentralReceiver] = 7411
        table[tech.Coal_CCS] = 9311
        table[tech.OCGT] = 873
        table[tech.PV1Axis] = 1505
        table[tech.Wind] = 1951


class GenCost2021_2030Low(GenCost2021):
    """GenCost 2020-21 costs for 2030 (low end of the range)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2021.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 4362
        table[tech.CCGT] = 1709
        table[tech.CCGT_CCS] = 3865
        table[tech.CentralReceiver] = 5968
        table[tech.Coal_CCS] = 8674
        table[tech.OCGT] = 856
        table[tech.PV1Axis] = 768
        table[tech.Wind] = 1863


class GenCost2021_2030High(GenCost2021):
    """GenCost 2020-21 costs for 2030 (high end of the range)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2021.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 4362
        table[tech.CCGT] = 1709
        table[tech.CCGT_CCS] = 4352
        table[tech.CentralReceiver] = 6496
        table[tech.Coal_CCS] = 14054
        table[tech.OCGT] = 856
        table[tech.PV1Axis] = 933
        table[tech.Wind] = 1910


class GenCost2021_2040Low(GenCost2021):
    """GenCost 2020-21 costs for 2040 (low end of the range)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2021.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 4275
        table[tech.CCGT] = 1675
        table[tech.CCGT_CCS] = 3327
        table[tech.CentralReceiver] = 5234
        table[tech.Coal_CCS] = 8030
        table[tech.OCGT] = 839
        table[tech.PV1Axis] = 569
        table[tech.Wind] = 1822


class GenCost2021_2040High(GenCost2021):
    """GenCost 2020-21 costs for 2040 (high end of the range)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2021.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 4275
        table[tech.CCGT] = 1675
        table[tech.CCGT_CCS] = 4309
        table[tech.CentralReceiver] = 6087
        table[tech.Coal_CCS] = 9034
        table[tech.OCGT] = 839
        table[tech.PV1Axis] = 778
        table[tech.Wind] = 1863


class GenCost2021_2050Low(GenCost2021):
    """GenCost 2020-21 costs for 2050 (low end of the range)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2021.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 4195
        table[tech.CCGT] = 1643
        table[tech.CCGT_CCS] = 3276
        table[tech.CentralReceiver] = 4748
        table[tech.Coal_CCS] = 7891
        table[tech.OCGT] = 822
        table[tech.PV1Axis] = 532
        table[tech.Wind] = 1774


class GenCost2021_2050High(GenCost2021):
    """GenCost 2020-21 costs for 2050 (high end of the range)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2021.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 4195
        table[tech.CCGT] = 1643
        table[tech.CCGT_CCS] = 4270
        table[tech.CentralReceiver] = 5530
        table[tech.Coal_CCS] = 8906
        table[tech.OCGT] = 822
        table[tech.PV1Axis] = 624
        table[tech.Wind] = 1830
