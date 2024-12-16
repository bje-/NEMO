# Copyright (C) 2024 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

# NOTE: This is a consultation draft only. This file will be updated
# when the final report is issued.

"""CSIRO GenCost costs for 2024-25 (draft)."""

from nemo import generators as tech

from .gencost import GenCost

# We use class names here that upset Pylint.
# pylint: disable=invalid-name


class GenCost2025(GenCost):
    """GenCost 2024-25 costs.

    Source:
    CSIRO GenCost 2024-25 draft consultation report
    """

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost.__init__(self, discount, coal_price, gas_price, ccs_price)

        # Fixed O&M (FOM) costs
        # Note: These are the same for all years (2030, 2040, 2050),
        # so we can set them once here.
        self.fixed_om_costs.update({
            tech.Black_Coal: 64.9,
            tech.CCGT: 15,
            tech.CCGT_CCS: 22.5,
            tech.CentralReceiver: 124.2,
            tech.Coal_CCS: 94.8,
            tech.Nuclear: 200,
            tech.OCGT: 14.1,
            tech.PV1Axis: 12.0,
            tech.Wind: 28.0,
            tech.WindOffshore: 174.6})

        # Variable O&M (VOM) costs
        # Likewise, these are the same for all years (2030, 2040, 2050).
        self.opcost_per_mwh.update({
            tech.Black_Coal: 4.7,
            tech.CCGT: 4.1,
            tech.CCGT_CCS: 8.0,
            # 10 GJ/MWh heat rate (36% efficiency), $1.10/GJ fuel cost
            tech.Nuclear: 5.3 + (10 * 1.1),
            tech.OCGT: 8.1,
            tech.WindOffshore: 0})


class GenCost2025_2030_CP(GenCost2025):
    """GenCost 2024-25 costs for 2030 (current policies)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2025.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 5301
        table[tech.CCGT] = 1969
        table[tech.CCGT_CCS] = 4617
        table[tech.CentralReceiver] = 5973
        table[tech.Coal_CCS] = 10435
        table[tech.Nuclear] = 8467
        table[tech.OCGT] = 1302
        table[tech.Behind_Meter_PV] = 1106
        table[tech.PV1Axis] = 1224
        table[tech.Wind] = 2603
        table[tech.WindOffshore] = 4629

        table = self.totcost_per_kwh
        table[tech.Battery] = {
            1: 780, 2: 525, 4: 367, 8: 300, 12: 278, 24: 256,
        }


class GenCost2025_2040_CP(GenCost2025):
    """GenCost 2024-25 costs for 2040 (current policies)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2025.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 5378
        table[tech.CCGT] = 1935
        table[tech.CCGT_CCS] = 4486
        table[tech.CentralReceiver] = 5217
        table[tech.Coal_CCS] = 10202
        table[tech.Nuclear] = 8322
        table[tech.OCGT] = 1280
        table[tech.Behind_Meter_PV] = 907
        table[tech.PV1Axis] = 1016
        table[tech.Wind] = 2047
        table[tech.WindOffshore] = 4489

        table = self.totcost_per_kwh
        table[tech.Battery] = {
            1: 640, 2: 422, 4: 290, 8: 234, 12: 214, 24: 196,
        }


class GenCost2025_2050_CP(GenCost2025):
    """GenCost 2024-25 costs for 2050 (current policies)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2025.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 5376
        table[tech.CCGT] = 1882
        table[tech.CCGT_CCS] = 4257
        table[tech.CentralReceiver] = 4388
        table[tech.Coal_CCS] = 9810
        table[tech.Nuclear] = 8091
        table[tech.OCGT] = 1243
        table[tech.Behind_Meter_PV] = 718
        table[tech.PV1Axis] = 807
        table[tech.Wind] = 1967
        table[tech.WindOffshore] = 4346

        table = self.totcost_per_kwh
        table[tech.Battery] = {
            1: 617, 2: 406, 4: 279, 8: 225, 12: 206, 24: 188,
        }


class GenCost2025_2030_NZE2050(GenCost2025):
    """GenCost 2024-25 costs for 2030 (Global NZE by 2050)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2025.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 5344
        table[tech.CCGT] = 1996
        table[tech.CCGT_CCS] = 4678
        table[tech.CentralReceiver] = 5437
        table[tech.Coal_CCS] = 10529
        table[tech.Nuclear] = 8493
        table[tech.OCGT] = 1302
        table[tech.Behind_Meter_PV] = 1031
        table[tech.PV1Axis] = 1141
        table[tech.Wind] = 2491
        table[tech.WindOffshore] = 4409

        table = self.totcost_per_kwh
        table[tech.Battery] = {
            1: 531, 2: 371, 4: 268, 8: 225, 12: 211, 24: 198,
        }


class GenCost2025_2040_NZE2050(GenCost2025):
    """GenCost 2024-25 costs for 2040 (Global NZE by 2050)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2025.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 5396
        table[tech.CCGT] = 1935
        table[tech.CCGT_CCS] = 4292
        table[tech.CentralReceiver] = 4269
        table[tech.Coal_CCS] = 10001
        table[tech.Nuclear] = 8322
        table[tech.OCGT] = 1280
        table[tech.Behind_Meter_PV] = 599
        table[tech.PV1Axis] = 671
        table[tech.Wind] = 1940
        table[tech.WindOffshore] = 4235

        table = self.totcost_per_kwh
        table[tech.Battery] = {
            1: 466, 2: 316, 4: 223, 8: 183, 12: 170, 24: 158,
        }


class GenCost2025_2050_NZE2050(GenCost2025):
    """GenCost 2024-25 costs for 2050 (Global NZE by 2050)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2025.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 5427
        table[tech.CCGT] = 1882
        table[tech.CCGT_CCS] = 4122
        table[tech.CentralReceiver] = 3444
        table[tech.Coal_CCS] = 9670
        table[tech.Nuclear] = 8091
        table[tech.OCGT] = 1243
        table[tech.Behind_Meter_PV] = 505
        table[tech.PV1Axis] = 569
        table[tech.Wind] = 1868
        table[tech.WindOffshore] = 4136

        table = self.totcost_per_kwh
        table[tech.Battery] = {
            1: 457, 2: 311, 4: 219, 8: 180, 12: 167, 24: 155,
        }


class GenCost2025_2030_NZEPost2050(GenCost2025):
    """GenCost 2024-25 costs for 2030 (Global NZE post 2050)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2025.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 5344
        table[tech.CCGT] = 1996
        table[tech.CCGT_CCS] = 4678
        table[tech.CentralReceiver] = 5666
        table[tech.Coal_CCS] = 10529
        table[tech.Nuclear] = 8467
        table[tech.OCGT] = 1302
        table[tech.Behind_Meter_PV] = 1069
        table[tech.PV1Axis] = 1183
        table[tech.Wind] = 2533
        table[tech.WindOffshore] = 4379

        table = self.totcost_per_kwh
        table[tech.Battery] = {
            1: 667, 2: 453, 4: 319, 8: 263, 12: 244, 24: 226,
        }


class GenCost2025_2040_NZEPost2050(GenCost2025):
    """GenCost 2024-25 costs for 2040 (Global NZE post 2050)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2025.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 5396
        table[tech.CCGT] = 1935
        table[tech.CCGT_CCS] = 4457
        table[tech.CentralReceiver] = 4570
        table[tech.Coal_CCS] = 10172
        table[tech.Nuclear] = 8322
        table[tech.OCGT] = 1280
        table[tech.Behind_Meter_PV] = 753
        table[tech.PV1Axis] = 843
        table[tech.Wind] = 2039
        table[tech.WindOffshore] = 3961

        table = self.totcost_per_kwh
        table[tech.Battery] = {
            1: 539, 2: 355, 4: 245, 8: 197, 12: 181, 24: 166,
        }


class GenCost2025_2050_NZEPost2050(GenCost2025):
    """GenCost 2024-25 costs for 2050 (Global NZE post 2050)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2025.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 5427
        table[tech.CCGT] = 1882
        table[tech.CCGT_CCS] = 4184
        table[tech.CentralReceiver] = 3814
        table[tech.Coal_CCS] = 8734
        table[tech.Nuclear] = 8091
        table[tech.OCGT] = 1243
        table[tech.Behind_Meter_PV] = 612
        table[tech.PV1Axis] = 688
        table[tech.Wind] = 2001
        table[tech.WindOffshore] = 3679

        table = self.totcost_per_kwh
        table[tech.Battery] = {
            1: 509, 2: 338, 4: 233, 8: 189, 12: 174, 24: 160,
        }
