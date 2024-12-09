# Copyright (C) 2024 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""CSIRO GenCost costs for 2023-24."""

from nemo import generators as tech

from .gencost import GenCost

# We use class names here that upset Pylint.
# pylint: disable=invalid-name


class GenCost2024(GenCost):
    """GenCost 2023-24 costs.

    Source:
    CSIRO GenCost 2023-24 report
    https://data.csiro.au/collections/collection/CIcsiro:44228
    """

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost.__init__(self, discount, coal_price, gas_price, ccs_price)

        # Fixed O&M (FOM) costs
        self.fixed_om_costs.update({
            tech.CentralReceiver: 124.2,
            tech.WindOffshore: 149.9})

        # Variable O&M (VOM) costs
        self.opcost_per_mwh.update({
            tech.OCGT: 7.3,
            tech.WindOffshore: 0})


class GenCost2024_2030_CP(GenCost2024):
    """GenCost 2023-24 costs for 2030 (current policies)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2024.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 5141
        table[tech.CCGT] = 1731
        table[tech.CCGT_CCS] = 4024
        table[tech.CentralReceiver] = 5301
        table[tech.Coal_CCS] = 9675
        table[tech.OCGT] = 865
        table[tech.Behind_Meter_PV] = 1071
        table[tech.PV1Axis] = 1173
        table[tech.Wind] = 2399
        table[tech.WindOffshore] = 5230

        table = self.totcost_per_kwh
        table[tech.Battery] = {1: 648, 2: 445, 4: 344, 8: 292}


class GenCost2024_2040_CP(GenCost2024):
    """GenCost 2023-24 costs for 2040 (current policies)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2024.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 5205
        table[tech.CCGT] = 1702
        table[tech.CCGT_CCS] = 3831
        table[tech.CentralReceiver] = 4615
        table[tech.Coal_CCS] = 9396
        table[tech.OCGT] = 850
        table[tech.Behind_Meter_PV] = 896
        table[tech.PV1Axis] = 994
        table[tech.Wind] = 1962
        table[tech.WindOffshore] = 4936

        table = self.totcost_per_kwh
        table[tech.Battery] = {1: 502, 2: 338, 4: 256, 8: 215}


class GenCost2024_2050_CP(GenCost2024):
    """GenCost 2023-24 costs for 2050 (current policies)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2024.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 5149
        table[tech.CCGT] = 1655
        table[tech.CCGT_CCS] = 3590
        table[tech.CentralReceiver] = 3878
        table[tech.Coal_CCS] = 9011
        table[tech.OCGT] = 826
        table[tech.Behind_Meter_PV] = 710
        table[tech.PV1Axis] = 791
        table[tech.Wind] = 1924
        table[tech.WindOffshore] = 4778

        table = self.totcost_per_kwh
        table[tech.Battery] = {1: 477, 2: 320, 4: 242, 8: 202}


class GenCost2024_2030_NZE2050(GenCost2024):
    """GenCost 2023-24 costs for 2030 (Global NZE by 2050)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2024.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 5168
        table[tech.CCGT] = 1747
        table[tech.CCGT_CCS] = 4070
        table[tech.CentralReceiver] = 4768
        table[tech.Coal_CCS] = 9751
        table[tech.OCGT] = 893
        table[tech.Behind_Meter_PV] = 1068
        table[tech.PV1Axis] = 1166
        table[tech.Wind] = 2358
        table[tech.WindOffshore] = 3720

        table = self.totcost_per_kwh
        table[tech.Battery] = {1: 433, 2: 302, 4: 236, 8: 202}


class GenCost2024_2040_NZE2050(GenCost2024):
    """GenCost 2023-24 costs for 2040 (Global NZE by 2050)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2024.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 5236
        table[tech.CCGT] = 1702
        table[tech.CCGT_CCS] = 3209
        table[tech.CentralReceiver] = 3731
        table[tech.Coal_CCS] = 8792
        table[tech.OCGT] = 855
        table[tech.Behind_Meter_PV] = 750
        table[tech.PV1Axis] = 832
        table[tech.Wind] = 1871
        table[tech.WindOffshore] = 2755

        table = self.totcost_per_kwh
        table[tech.Battery] = {1: 372, 2: 249, 4: 188, 8: 157}


class GenCost2024_2050_NZE2050(GenCost2024):
    """GenCost 2023-24 costs for 2050 (Global NZE by 2050)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2024.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 5268
        table[tech.CCGT] = 1655
        table[tech.CCGT_CCS] = 3146
        table[tech.CentralReceiver] = 3007
        table[tech.Coal_CCS] = 8575
        table[tech.OCGT] = 830
        table[tech.Behind_Meter_PV] = 524
        table[tech.PV1Axis] = 583
        table[tech.Wind] = 1763
        table[tech.WindOffshore] = 2691

        table = self.totcost_per_kwh
        table[tech.Battery] = {1: 364, 2: 244, 4: 184, 8: 154}


class GenCost2024_2030_NZEPost2050(GenCost2024):
    """GenCost 2023-24 costs for 2030 (Global NZE post 2050)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2024.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 5168
        table[tech.CCGT] = 1747
        table[tech.CCGT_CCS] = 4070
        table[tech.CentralReceiver] = 4968
        table[tech.Coal_CCS] = 9751
        table[tech.OCGT] = 893
        table[tech.Behind_Meter_PV] = 1073
        table[tech.PV1Axis] = 1172
        table[tech.Wind] = 2386
        table[tech.WindOffshore] = 4914

        table = self.totcost_per_kwh
        table[tech.Battery] = {1: 561, 2: 393, 4: 309, 8: 266}


class GenCost2024_2040_NZEPost2050(GenCost2024):
    """GenCost 2023-24 costs for 2040 (Global NZE post 2050)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2024.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 5236
        table[tech.CCGT] = 1702
        table[tech.CCGT_CCS] = 3514
        table[tech.CentralReceiver] = 3994
        table[tech.Coal_CCS] = 9095
        table[tech.OCGT] = 855
        table[tech.Behind_Meter_PV] = 823
        table[tech.PV1Axis] = 913
        table[tech.Wind] = 1949
        table[tech.WindOffshore] = 4339

        table = self.totcost_per_kwh
        table[tech.Battery] = {1: 421, 2: 278, 4: 207, 8: 171}


class GenCost2024_2050_NZEPost2050(GenCost2024):
    """GenCost 2023-24 costs for 2050 (Global NZE post 2050)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2024.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 5268
        table[tech.CCGT] = 1655
        table[tech.CCGT_CCS] = 3154
        table[tech.CentralReceiver] = 3330
        table[tech.Coal_CCS] = 8580
        table[tech.OCGT] = 830
        table[tech.Behind_Meter_PV] = 617
        table[tech.PV1Axis] = 687
        table[tech.Wind] = 1885
        table[tech.WindOffshore] = 3990

        table = self.totcost_per_kwh
        table[tech.Battery] = {1: 405, 2: 267, 4: 198, 8: 163}
