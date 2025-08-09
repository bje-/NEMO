# Copyright (C) 2025 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

# NOTE: This is a consultation draft only. This file will be updated
# when the final report is issued.

"""CSIRO GenCost costs for 2024-25."""

from nemo import generators as tech

from .gencost import GenCost

# We use class names here that upset Pylint.
# pylint: disable=invalid-name


class GenCost2025(GenCost):
    """GenCost 2024-25 costs.

    Source:
    CSIRO GenCost 2024-25 report
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
        table[tech.Black_Coal] = 5299
        table[tech.CCGT] = 1917
        table[tech.CCGT_CCS] = 4822
        table[tech.CentralReceiver] = 6480
        table[tech.Coal_CCS] = 10696
        table[tech.Nuclear] = 8736
        table[tech.OCGT] = 1283
        table[tech.Behind_Meter_PV] = 1227
        table[tech.PV1Axis] = 1123
        table[tech.Wind] = 2646
        table[tech.WindOffshore] = 4654

        table = self.totcost_per_kwh
        table[tech.Battery] = {
            1: 691, 2: 484, 4: 349, 8: 294, 12: 276, 24: 259,
        }


class GenCost2025_2040_CP(GenCost2025):
    """GenCost 2024-25 costs for 2040 (current policies)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2025.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 5500
        table[tech.CCGT] = 1904
        table[tech.CCGT_CCS] = 4796
        table[tech.CentralReceiver] = 6470
        table[tech.Coal_CCS] = 11020
        table[tech.Nuclear] = 9102
        table[tech.OCGT] = 1239
        table[tech.Behind_Meter_PV] = 1175
        table[tech.PV1Axis] = 1024
        table[tech.Wind] = 2163
        table[tech.WindOffshore] = 4690

        table = self.totcost_per_kwh
        table[tech.Battery] = {
            1: 557, 2: 382, 4: 271, 8: 225, 12: 211, 24: 196,
        }


class GenCost2025_2050_CP(GenCost2025):
    """GenCost 2024-25 costs for 2050 (current policies)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2025.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 5635
        table[tech.CCGT] = 1940
        table[tech.CCGT_CCS] = 4653
        table[tech.CentralReceiver] = 5799
        table[tech.Coal_CCS] = 11026
        table[tech.Nuclear] = 9368
        table[tech.OCGT] = 1196
        table[tech.Behind_Meter_PV] = 1122
        table[tech.PV1Axis] = 934
        table[tech.Wind] = 2108
        table[tech.WindOffshore] = 4724

        table = self.totcost_per_kwh
        table[tech.Battery] = {
            1: 519, 2: 358, 4: 255, 8: 212, 12: 199, 24: 185,
        }


class GenCost2025_2030_NZE2050(GenCost2025):
    """GenCost 2024-25 costs for 2030 (Global NZE by 2050)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2025.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 5441
        table[tech.CCGT] = 2113
        table[tech.CCGT_CCS] = 5170
        table[tech.CentralReceiver] = 6152
        table[tech.Coal_CCS] = 10901
        table[tech.Nuclear] = 8919
        table[tech.OCGT] = 1283
        table[tech.Behind_Meter_PV] = 1172
        table[tech.PV1Axis] = 1027
        table[tech.Wind] = 2616
        table[tech.WindOffshore] = 3180

        table = self.totcost_per_kwh
        table[tech.Battery] = {
            1: 346, 2: 254, 4: 190, 8: 164, 12: 157, 24: 149,
        }


class GenCost2025_2040_NZE2050(GenCost2025):
    """GenCost 2024-25 costs for 2040 (Global NZE by 2050)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2025.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 5777
        table[tech.CCGT] = 1953
        table[tech.CCGT_CCS] = 4580
        table[tech.CentralReceiver] = 5244
        table[tech.Coal_CCS] = 11028
        table[tech.Nuclear] = 9524
        table[tech.OCGT] = 1239
        table[tech.Behind_Meter_PV] = 1025
        table[tech.PV1Axis] = 713
        table[tech.Wind] = 2123
        table[tech.WindOffshore] = 3067

        table = self.totcost_per_kwh
        table[tech.Battery] = {
            1: 264, 2: 183, 4: 131, 8: 110, 12: 103, 24: 96,
        }


class GenCost2025_2050_NZE2050(GenCost2025):
    """GenCost 2024-25 costs for 2050 (Global NZE by 2050)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2025.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 6111
        table[tech.CCGT] = 2023
        table[tech.CCGT_CCS] = 4621
        table[tech.CentralReceiver] = 4972
        table[tech.Coal_CCS] = 11374
        table[tech.Nuclear] = 10074
        table[tech.OCGT] = 1196
        table[tech.Behind_Meter_PV] = 909
        table[tech.PV1Axis] = 647
        table[tech.Wind] = 2064
        table[tech.WindOffshore] = 3112

        table = self.totcost_per_kwh
        table[tech.Battery] = {
            1: 264, 2: 183, 4: 131, 8: 109, 12: 103, 24: 96,
        }


class GenCost2025_2030_NZEPost2050(GenCost2025):
    """GenCost 2024-25 costs for 2030 (Global NZE post 2050)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2025.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 5372
        table[tech.CCGT] = 2102
        table[tech.CCGT_CCS] = 5157
        table[tech.CentralReceiver] = 6191
        table[tech.Coal_CCS] = 10822
        table[tech.Nuclear] = 8806
        table[tech.OCGT] = 1283
        table[tech.Behind_Meter_PV] = 1208
        table[tech.PV1Axis] = 1030
        table[tech.Wind] = 2592
        table[tech.WindOffshore] = 4679

        table = self.totcost_per_kwh
        table[tech.Battery] = {
            1: 544, 2: 383, 4: 277, 8: 234, 12: 221, 24: 207,
        }


class GenCost2025_2040_NZEPost2050(GenCost2025):
    """GenCost 2024-25 costs for 2040 (Global NZE post 2050)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2025.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 5604
        table[tech.CCGT] = 1920
        table[tech.CCGT_CCS] = 4749
        table[tech.CentralReceiver] = 5886
        table[tech.Coal_CCS] = 11047
        table[tech.Nuclear] = 9234
        table[tech.OCGT] = 1239
        table[tech.Behind_Meter_PV] = 1111
        table[tech.PV1Axis] = 868
        table[tech.Wind] = 2144
        table[tech.WindOffshore] = 4334

        table = self.totcost_per_kwh
        table[tech.Battery] = {
            1: 457, 2: 317, 4: 226, 8: 189, 12: 177, 24: 166,
        }


class GenCost2025_2050_NZEPost2050(GenCost2025):
    """GenCost 2024-25 costs for 2050 (Global NZE post 2050)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2025.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 5825
        table[tech.CCGT] = 1968
        table[tech.CCGT_CCS] = 4660
        table[tech.CentralReceiver] = 5405
        table[tech.Coal_CCS] = 11160
        table[tech.Nuclear] = 9602
        table[tech.OCGT] = 1196
        table[tech.Behind_Meter_PV] = 1073
        table[tech.PV1Axis] = 790
        table[tech.Wind] = 2087
        table[tech.WindOffshore] = 3888

        table = self.totcost_per_kwh
        table[tech.Battery] = {
            1: 415, 2: 292, 4: 212, 8: 179, 12: 169, 24: 159,
        }
