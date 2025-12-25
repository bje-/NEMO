# Copyright (C) 2025 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

# NOTE: This is a consultation draft only. This file will be updated
# when the final report is issued.

"""CSIRO GenCost costs for 2025-26."""

from nemo import generators as tech

from .gencost import GenCost

# We use class names here that upset Pylint.
# pylint: disable=invalid-name


class GenCost2026(GenCost):
    """GenCost 2025-26 costs.

    Source:
    CSIRO GenCost 2025-26 report
    https://data.csiro.au/collections/collection/CIcsiro:44228
    """

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost.__init__(self, discount, coal_price, gas_price, ccs_price)

        # Fixed O&M (FOM) costs
        # Note: These are the same for all years (2030, 2040, 2050),
        # so we can set them once here.
        self.fixed_om_costs.update({
            tech.Black_Coal: 64.9,
            tech.CCGT: 36,
            tech.CCGT_CCS: 46,
            tech.CentralReceiver: 124.2,
            tech.Coal_CCS: 94.8,
            tech.Nuclear: 200,
            tech.OCGT: 17.4,
            tech.PV1Axis: 12,
            tech.Wind: 29,
            tech.WindOffshore: 175})

        # Variable O&M (VOM) costs
        # Likewise, these are the same for all years (2030, 2040, 2050).
        self.opcost_per_mwh.update({
            tech.Black_Coal: 4.7,
            tech.CCGT: 5,
            tech.CCGT_CCS: 8,
            # 10 GJ/MWh heat rate (36% efficiency), $1.10/GJ fuel cost
            tech.Nuclear: 5.3 + (10 * 1.1),
            tech.OCGT: 16.1,
            tech.WindOffshore: 0})


class GenCost2026_2030_CP(GenCost2026):
    """GenCost 2025-26 costs for 2030 (current policies)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2026.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 6164
        table[tech.CCGT] = 2180
        table[tech.CCGT_CCS] = 5807
        table[tech.CentralReceiver] = 7197
        table[tech.Coal_CCS] = 11961
        table[tech.Nuclear] = 9658
        table[tech.OCGT] = 2296
        table[tech.Behind_Meter_PV] = 1135
        table[tech.PV1Axis] = 1239
        table[tech.Wind] = 2697
        table[tech.WindOffshore] = 5268

        table = self.totcost_per_kwh
        table[tech.Battery] = {
            1: 717, 2: 484, 4: 355, 8: 284, 12: 265, 24: 246,
        }


class GenCost2026_2040_CP(GenCost2026):
    """GenCost 2025-26 costs for 2040 (current policies)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2026.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 5631
        table[tech.CCGT] = 1939
        table[tech.CCGT_CCS] = 4834
        table[tech.CentralReceiver] = 6456
        table[tech.Coal_CCS] = 11299
        table[tech.Nuclear] = 9306
        table[tech.OCGT] = 1767
        table[tech.Behind_Meter_PV] = 1103
        table[tech.PV1Axis] = 918
        table[tech.Wind] = 2343
        table[tech.WindOffshore] = 5301

        table = self.totcost_per_kwh
        table[tech.Battery] = {
            1: 568, 2: 378, 4: 274, 8: 217, 12: 201, 24: 186,
        }


class GenCost2026_2050_CP(GenCost2026):
    """GenCost 2025-26 costs for 2050 (current policies)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2026.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 5803
        table[tech.CCGT] = 1978
        table[tech.CCGT_CCS] = 4553
        table[tech.CentralReceiver] = 6089
        table[tech.Coal_CCS] = 11254
        table[tech.Nuclear] = 9607
        table[tech.OCGT] = 1798
        table[tech.Behind_Meter_PV] = 1091
        table[tech.PV1Axis] = 851
        table[tech.Wind] = 2290
        table[tech.WindOffshore] = 5344

        table = self.totcost_per_kwh
        table[tech.Battery] = {
            1: 537, 2: 358, 4: 259, 8: 205, 12: 190, 24: 176,
        }


class GenCost2026_2030_NZE2050(GenCost2026):
    """GenCost 2025-26 costs for 2030 (Global NZE by 2050)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2026.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 6296
        table[tech.CCGT] = 2204
        table[tech.CCGT_CCS] = 5846
        table[tech.CentralReceiver] = 6869
        table[tech.Coal_CCS] = 12196
        table[tech.Nuclear] = 9858
        table[tech.OCGT] = 2319
        table[tech.Behind_Meter_PV] = 1101
        table[tech.PV1Axis] = 743
        table[tech.Wind] = 2608
        table[tech.WindOffshore] = 3281

        table = self.totcost_per_kwh
        table[tech.Battery] = {
            1: 420, 2: 295, 4: 223, 8: 183, 12: 173, 24: 163,
        }


class GenCost2026_2040_NZE2050(GenCost2026):
    """GenCost 2025-26 costs for 2040 (Global NZE by 2050)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2026.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 5941
        table[tech.CCGT] = 1994
        table[tech.CCGT_CCS] = 4645
        table[tech.CentralReceiver] = 6122
        table[tech.Coal_CCS] = 11551
        table[tech.Nuclear] = 9795
        table[tech.OCGT] = 1811
        table[tech.Behind_Meter_PV] = 1058
        table[tech.PV1Axis] = 584
        table[tech.Wind] = 2153
        table[tech.WindOffshore] = 3139

        table = self.totcost_per_kwh
        table[tech.Battery] = {
            1: 329, 2: 218, 4: 157, 8: 124, 12: 115, 24: 106,
        }


class GenCost2026_2050_NZE2050(GenCost2026):
    """GenCost 2025-26 costs for 2050 (Global NZE by 2050)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2026.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 6326
        table[tech.CCGT] = 2069
        table[tech.CCGT_CCS] = 4782
        table[tech.CentralReceiver] = 6076
        table[tech.Coal_CCS] = 12282
        table[tech.Nuclear] = 10429
        table[tech.OCGT] = 1874
        table[tech.Behind_Meter_PV] = 920
        table[tech.PV1Axis] = 564
        table[tech.Wind] = 2141
        table[tech.WindOffshore] = 3197

        table = self.totcost_per_kwh
        table[tech.Battery] = {
            1: 332, 2: 219, 4: 158, 8: 124, 12: 115, 24: 106,
        }


class GenCost2026_2030_NZEPost2050(GenCost2026):
    """GenCost 2025-26 costs for 2030 (Global NZE post 2050)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2026.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 6207
        table[tech.CCGT] = 2188
        table[tech.CCGT_CCS] = 5802
        table[tech.CentralReceiver] = 7372
        table[tech.Coal_CCS] = 12015
        table[tech.Nuclear] = 9718
        table[tech.OCGT] = 2303
        table[tech.Behind_Meter_PV] = 1126
        table[tech.PV1Axis] = 930
        table[tech.Wind] = 2636
        table[tech.WindOffshore] = 5306

        table = self.totcost_per_kwh
        table[tech.Battery] = {
            1: 589, 2: 400, 4: 295, 8: 237, 12: 222, 24: 206,
        }


class GenCost2026_2040_NZEPost2050(GenCost2026):
    """GenCost 2025-26 costs for 2040 (Global NZE post 2050)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2026.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 5740
        table[tech.CCGT] = 1957
        table[tech.CCGT_CCS] = 4812
        table[tech.CentralReceiver] = 6618
        table[tech.Coal_CCS] = 11425
        table[tech.Nuclear] = 9464
        table[tech.OCGT] = 1781
        table[tech.Behind_Meter_PV] = 1059
        table[tech.PV1Axis] = 725
        table[tech.Wind] = 2201
        table[tech.WindOffshore] = 4597

        table = self.totcost_per_kwh
        table[tech.Battery] = {
            1: 492, 2: 326, 4: 234, 8: 184, 12: 171, 24: 157,
        }


class GenCost2026_2050_NZEPost2050(GenCost2026):
    """GenCost 2025-26 costs for 2050 (Global NZE post 2050)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2026.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 5993
        table[tech.CCGT] = 2008
        table[tech.CCGT_CCS] = 4714
        table[tech.CentralReceiver] = 5949
        table[tech.Coal_CCS] = 11692
        table[tech.Nuclear] = 9880
        table[tech.OCGT] = 1823
        table[tech.Behind_Meter_PV] = 1054
        table[tech.PV1Axis] = 664
        table[tech.Wind] = 2137
        table[tech.WindOffshore] = 4472

        table = self.totcost_per_kwh
        table[tech.Battery] = {
            1: 451, 2: 302, 4: 220, 8: 175, 12: 163, 24: 151,
        }
