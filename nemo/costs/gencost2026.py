# Copyright (C) 2025, 2026 Ben Elliston
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
        table[tech.Black_Coal] = 6162
        table[tech.CCGT] = 2426
        table[tech.CCGT_CCS] = 6269
        table[tech.CentralReceiver] = 6358
        table[tech.Coal_CCS] = 11961
        table[tech.Nuclear] = 9658
        table[tech.OCGT] = 2624
        table[tech.Behind_Meter_PV] = 1135
        table[tech.PV1Axis] = 1378
        table[tech.Wind] = 2650
        table[tech.WindOffshore] = 5300

        table = self.totcost_per_kwh
        table[tech.Battery] = {
            1: 653, 2: 438, 4: 319, 8: 254, 12: 237, 24: 219,
        }


class GenCost2026_2040_CP(GenCost2026):
    """GenCost 2025-26 costs for 2040 (current policies)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2026.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 5624
        table[tech.CCGT] = 1939
        table[tech.CCGT_CCS] = 4933
        table[tech.CentralReceiver] = 5873
        table[tech.Coal_CCS] = 11408
        table[tech.Nuclear] = 9306
        table[tech.OCGT] = 1767
        table[tech.Behind_Meter_PV] = 1090
        table[tech.PV1Axis] = 1191
        table[tech.Wind] = 2253
        table[tech.WindOffshore] = 5315

        table = self.totcost_per_kwh
        table[tech.Battery] = {
            1: 582, 2: 373, 4: 261, 8: 201, 12: 183, 24: 166,
        }


class GenCost2026_2050_CP(GenCost2026):
    """GenCost 2025-26 costs for 2050 (current policies)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2026.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 5791
        table[tech.CCGT] = 1978
        table[tech.CCGT_CCS] = 5031
        table[tech.CentralReceiver] = 5376
        table[tech.Coal_CCS] = 11790
        table[tech.Nuclear] = 9607
        table[tech.OCGT] = 1798
        table[tech.Behind_Meter_PV] = 1077
        table[tech.PV1Axis] = 1029
        table[tech.Wind] = 2207
        table[tech.WindOffshore] = 5342

        table = self.totcost_per_kwh
        table[tech.Battery] = {
            1: 567, 2: 362, 4: 252, 8: 193, 12: 177, 24: 160,
        }


class GenCost2026_2030_NZE2050(GenCost2026):
    """GenCost 2025-26 costs for 2030 (Global NZE by 2050)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2026.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 6296
        table[tech.CCGT] = 2443
        table[tech.CCGT_CCS] = 6252
        table[tech.CentralReceiver] = 6037
        table[tech.Coal_CCS] = 12196
        table[tech.Nuclear] = 9858
        table[tech.OCGT] = 2642
        table[tech.Behind_Meter_PV] = 1055
        table[tech.PV1Axis] = 847
        table[tech.Wind] = 2629
        table[tech.WindOffshore] = 4133

        table = self.totcost_per_kwh
        table[tech.Battery] = {
            1: 588, 2: 406, 4: 302, 8: 245, 12: 230, 24: 215,
        }


class GenCost2026_2040_NZE2050(GenCost2026):
    """GenCost 2025-26 costs for 2040 (Global NZE by 2050)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2026.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 5941
        table[tech.CCGT] = 1994
        table[tech.CCGT_CCS] = 4654
        table[tech.CentralReceiver] = 5662
        table[tech.Coal_CCS] = 11561
        table[tech.Nuclear] = 9795
        table[tech.OCGT] = 1811
        table[tech.Behind_Meter_PV] = 855
        table[tech.PV1Axis] = 672
        table[tech.Wind] = 2214
        table[tech.WindOffshore] = 4126

        table = self.totcost_per_kwh
        table[tech.Battery] = {
            1: 472, 2: 318, 4: 232, 8: 186, 12: 173, 24: 161,
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
        table[tech.CentralReceiver] = 5723
        table[tech.Coal_CCS] = 12282
        table[tech.Nuclear] = 10429
        table[tech.OCGT] = 1874
        table[tech.Behind_Meter_PV] = 731
        table[tech.PV1Axis] = 616
        table[tech.Wind] = 2180
        table[tech.WindOffshore] = 4231

        table = self.totcost_per_kwh
        table[tech.Battery] = {
            1: 427, 2: 295, 4: 220, 8: 179, 12: 169, 24: 158,
        }


class GenCost2026_2030_NZEPost2050(GenCost2026):
    """GenCost 2025-26 costs for 2030 (Global NZE post 2050)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2026.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 6207
        table[tech.CCGT] = 2431
        table[tech.CCGT_CCS] = 6264
        table[tech.CentralReceiver] = 6511
        table[tech.Coal_CCS] = 12015
        table[tech.Nuclear] = 9718
        table[tech.OCGT] = 2630
        table[tech.Behind_Meter_PV] = 1137
        table[tech.PV1Axis] = 1392
        table[tech.Wind] = 2647
        table[tech.WindOffshore] = 5292

        table = self.totcost_per_kwh
        table[tech.Battery] = {
            1: 620, 2: 421, 4: 310, 8: 249, 12: 233, 24: 216,
        }


class GenCost2026_2040_NZEPost2050(GenCost2026):
    """GenCost 2025-26 costs for 2040 (Global NZE post 2050)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2026.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 5740
        table[tech.CCGT] = 1957
        table[tech.CCGT_CCS] = 4925
        table[tech.CentralReceiver] = 6007
        table[tech.Coal_CCS] = 11552
        table[tech.Nuclear] = 9464
        table[tech.OCGT] = 1781
        table[tech.Behind_Meter_PV] = 1069
        table[tech.PV1Axis] = 1088
        table[tech.Wind] = 2251
        table[tech.WindOffshore] = 4929

        table = self.totcost_per_kwh
        table[tech.Battery] = {
            1: 521, 2: 340, 4: 241, 8: 188, 12: 173, 24: 159,
        }


class GenCost2026_2050_NZEPost2050(GenCost2026):
    """GenCost 2025-26 costs for 2050 (Global NZE post 2050)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2026.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 5993
        table[tech.CCGT] = 2008
        table[tech.CCGT_CCS] = 5049
        table[tech.CentralReceiver] = 5548
        table[tech.Coal_CCS] = 12073
        table[tech.Nuclear] = 9880
        table[tech.OCGT] = 1823
        table[tech.Behind_Meter_PV] = 1004
        table[tech.PV1Axis] = 873
        table[tech.Wind] = 2213
        table[tech.WindOffshore] = 4721

        table = self.totcost_per_kwh
        table[tech.Battery] = {
            1: 487, 2: 320, 4: 229, 8: 180, 12: 166, 24: 152,
        }
