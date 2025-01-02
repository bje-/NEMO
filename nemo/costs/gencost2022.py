# Copyright (C) 2024 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""CSIRO GenCost costs for 2021-22."""

from nemo import generators as tech

from .gencost import GenCost

# We use class names here that upset Pylint.
# pylint: disable=invalid-name, disable=duplicate-code


class GenCost2022(GenCost):
    """GenCost 2021-22 costs.

    Source:
    CSIRO GenCost 2021-22 report
    https://data.csiro.au/collections/collection/CIcsiro:44228
    """

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost.__init__(self, discount, coal_price, gas_price, ccs_price)

        self.fixed_om_costs.update({tech.CentralReceiver: 120.0,
                                    tech.WindOffshore: 149.9})
        self.opcost_per_mwh.update({tech.OCGT: 7.3,
                                    tech.WindOffshore: 0})


class GenCost2022_2021(GenCost2022):
    """GenCost 2020-21 costs for 2021 (low assumption)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2022.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 4343
        table[tech.CCGT] = 1559
        table[tech.CCGT_CCS] = 4011
        table[tech.CentralReceiver] = 6693
        table[tech.Coal_CCS] = 9077
        table[tech.OCGT] = 873
        table[tech.Behind_Meter_PV] = 1333
        table[tech.PV1Axis] = 1441
        table[tech.Wind] = 1960
        table[tech.WindOffshore] = 4649

        table = self.totcost_per_kwh
        table[tech.Battery] = {1: 790, 2: 527, 4: 407, 8: 357}


class GenCost2022_2030_CP(GenCost2022):
    """GenCost 2021-22 costs for 2030 (current policies)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2022.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 4223
        table[tech.CCGT] = 1516
        table[tech.CCGT_CCS] = 3957
        table[tech.CentralReceiver] = 5660
        table[tech.Coal_CCS] = 8884
        table[tech.OCGT] = 741
        table[tech.Behind_Meter_PV] = 949
        table[tech.PV1Axis] = 1013
        table[tech.Wind] = 1897
        table[tech.WindOffshore] = 4545

        table = self.totcost_per_kwh
        table[tech.Battery] = {1: 687, 2: 452, 4: 343, 8: 298}


class GenCost2022_2040_CP(GenCost2022):
    """GenCost 2021-22 costs for 2040 (current policies)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2022.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 4078
        table[tech.CCGT] = 1464
        table[tech.CCGT_CCS] = 3892
        table[tech.CentralReceiver] = 4894
        table[tech.Coal_CCS] = 8650
        table[tech.OCGT] = 716
        table[tech.Behind_Meter_PV] = 691
        table[tech.PV1Axis] = 733
        table[tech.Wind] = 1868
        table[tech.WindOffshore] = 4482

        table = self.totcost_per_kwh
        table[tech.Battery] = {1: 565, 2: 363, 4: 269, 8: 230}


class GenCost2022_2050_CP(GenCost2022):
    """GenCost 2021-22 costs for 2050 (current policies)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2022.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 3937
        table[tech.CCGT] = 1413
        table[tech.CCGT_CCS] = 3324
        table[tech.CentralReceiver] = 4103
        table[tech.Coal_CCS] = 7958
        table[tech.OCGT] = 691
        table[tech.Behind_Meter_PV] = 606
        table[tech.PV1Axis] = 644
        table[tech.Wind] = 1828
        table[tech.WindOffshore] = 4431

        table = self.totcost_per_kwh
        table[tech.Battery] = {1: 485, 2: 315, 4: 236, 8: 203}


class GenCost2022_2030_NZE2050(GenCost2022):
    """GenCost 2021-22 costs for 2030 (Global NZE by 2050)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2022.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 4208
        table[tech.CCGT] = 1511
        table[tech.CCGT_CCS] = 3725
        table[tech.CentralReceiver] = 4657
        table[tech.Coal_CCS] = 8631
        table[tech.OCGT] = 741
        table[tech.Behind_Meter_PV] = 752
        table[tech.PV1Axis] = 785
        table[tech.Wind] = 1633
        table[tech.WindOffshore] = 2967

        table = self.totcost_per_kwh
        table[tech.Battery] = {1: 553, 2: 344, 4: 242, 8: 200}


class GenCost2022_2040_NZE2050(GenCost2022):
    """GenCost 2021-22 costs for 2040 (Global NZE by 2050)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2022.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 4063
        table[tech.CCGT] = 1459
        table[tech.CCGT_CCS] = 3039
        table[tech.CentralReceiver] = 3620
        table[tech.Coal_CCS] = 7768
        table[tech.OCGT] = 716
        table[tech.Behind_Meter_PV] = 557
        table[tech.PV1Axis] = 578
        table[tech.Wind] = 1553
        table[tech.WindOffshore] = 2653

        table = self.totcost_per_kwh
        table[tech.Battery] = {1: 436, 2: 272, 4: 194, 8: 161}


class GenCost2022_2050_NZE2050(GenCost2022):
    """GenCost 2021-22 costs for 2050 (Global NZE by 2050)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2022.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 3930
        table[tech.CCGT] = 1411
        table[tech.CCGT_CCS] = 2978
        table[tech.CentralReceiver] = 2911
        table[tech.Coal_CCS] = 7552
        table[tech.OCGT] = 691
        table[tech.Behind_Meter_PV] = 500
        table[tech.PV1Axis] = 521
        table[tech.Wind] = 1521
        table[tech.WindOffshore] = 2506

        table = self.totcost_per_kwh
        table[tech.Battery] = {1: 337, 2: 220, 4: 167, 8: 144}


class GenCost2022_2030_NZEPost2050(GenCost2022):
    """GenCost 2021-22 costs for 2030 (Global NZE post 2050)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2022.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 4223
        table[tech.CCGT] = 1516
        table[tech.CCGT_CCS] = 3784
        table[tech.CentralReceiver] = 5236
        table[tech.Coal_CCS] = 8747
        table[tech.OCGT] = 741
        table[tech.Behind_Meter_PV] = 977
        table[tech.PV1Axis] = 1046
        table[tech.Wind] = 1778
        table[tech.WindOffshore] = 4437

        table = self.totcost_per_kwh
        table[tech.Battery] = {1: 608, 2: 390, 4: 287, 8: 244}


class GenCost2022_2040_NZEPost2050(GenCost2022):
    """GenCost 2021-22 costs for 2040 (Global NZE post 2050)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2022.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 4078
        table[tech.CCGT] = 1464
        table[tech.CCGT_CCS] = 3276
        table[tech.CentralReceiver] = 4181
        table[tech.Coal_CCS] = 8025
        table[tech.OCGT] = 716
        table[tech.Behind_Meter_PV] = 653
        table[tech.PV1Axis] = 689
        table[tech.Wind] = 1648
        table[tech.WindOffshore] = 3772

        table = self.totcost_per_kwh
        table[tech.Battery] = {1: 483, 2: 309, 4: 227, 8: 193}


class GenCost2022_2050_NZEPost2050(GenCost2022):
    """GenCost 2021-22 costs for 2050 (Global NZE post 2050)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2022.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 3937
        table[tech.CCGT] = 1413
        table[tech.CCGT_CCS] = 3206
        table[tech.CentralReceiver] = 3478
        table[tech.Coal_CCS] = 7792
        table[tech.OCGT] = 691
        table[tech.Behind_Meter_PV] = 508
        table[tech.PV1Axis] = 530
        table[tech.Wind] = 1546
        table[tech.WindOffshore] = 3168

        table = self.totcost_per_kwh
        table[tech.Battery] = {1: 385, 2: 255, 4: 196, 8: 172}
