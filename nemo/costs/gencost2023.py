# Copyright (C) 2024 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""CSIRO GenCost costs for 2022-23."""

from nemo import generators as tech

from .gencost import GenCost

# We use class names here that upset Pylint.
# pylint: disable=invalid-name, disable=duplicate-code


class GenCost2023(GenCost):
    """GenCost 2022-23 costs.

    Source:
    CSIRO GenCost 2022-23 report
    https://data.csiro.au/collections/collection/CIcsiro:44228
    """

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost.__init__(self, discount, coal_price, gas_price, ccs_price)

        self.fixed_om_costs.update({tech.CentralReceiver: 120.0,
                                    tech.WindOffshore: 149.9})
        self.opcost_per_mwh.update({tech.OCGT: 7.3,
                                    tech.WindOffshore: 0})
        # pylint: enable=duplicate-code


class GenCost2023_2030_CP(GenCost2023):
    """GenCost 2022-23 costs for 2030 (current policies)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2023.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 4558
        table[tech.CCGT] = 1636
        table[tech.CCGT_CCS] = 4279
        table[tech.CentralReceiver] = 5562
        table[tech.Coal_CCS] = 9597
        table[tech.OCGT] = 803
        table[tech.Behind_Meter_PV] = 977
        table[tech.PV1Axis] = 1058
        table[tech.Wind] = 1989
        table[tech.WindOffshore] = 4803

        table = self.totcost_per_kwh
        table[tech.Battery] = {1: 742, 2: 510, 4: 411, 8: 366}


class GenCost2023_2040_CP(GenCost2023):
    """GenCost 2022-23 costs for 2040 (current policies)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2023.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 4484
        table[tech.CCGT] = 1610
        table[tech.CCGT_CCS] = 3673
        table[tech.CentralReceiver] = 4826
        table[tech.Coal_CCS] = 8896
        table[tech.OCGT] = 790
        table[tech.Behind_Meter_PV] = 764
        table[tech.PV1Axis] = 839
        table[tech.Wind] = 1959
        table[tech.WindOffshore] = 4659

        table = self.totcost_per_kwh
        table[tech.Battery] = {1: 581, 2: 380, 4: 291, 8: 251}


class GenCost2023_2050_CP(GenCost2023):
    """GenCost 2022-23 costs for 2050 (current policies)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2023.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 4361
        table[tech.CCGT] = 1565
        table[tech.CCGT_CCS] = 3488
        table[tech.CentralReceiver] = 4051
        table[tech.Coal_CCS] = 8566
        table[tech.OCGT] = 768
        table[tech.Behind_Meter_PV] = 619
        table[tech.PV1Axis] = 676
        table[tech.Wind] = 1927
        table[tech.WindOffshore] = 4511

        table = self.totcost_per_kwh
        table[tech.Battery] = {1: 514, 2: 335, 4: 257, 8: 221}


class GenCost2023_2030_NZE2050(GenCost2023):
    """GenCost 2022-23 costs for 2030 (Global NZE by 2050)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2023.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 4668
        table[tech.CCGT] = 1672
        table[tech.CCGT_CCS] = 4283
        table[tech.CentralReceiver] = 4917
        table[tech.Coal_CCS] = 9639
        table[tech.OCGT] = 828
        table[tech.Behind_Meter_PV] = 988
        table[tech.PV1Axis] = 1071
        table[tech.Wind] = 1913
        table[tech.WindOffshore] = 2755

        table = self.totcost_per_kwh
        table[tech.Battery] = {1: 580, 2: 344, 4: 235, 8: 186}


class GenCost2023_2040_NZE2050(GenCost2023):
    """GenCost 2022-23 costs for 2040 (Global NZE by 2050)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2023.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 4484
        table[tech.CCGT] = 1610
        table[tech.CCGT_CCS] = 3502
        table[tech.CentralReceiver] = 3835
        table[tech.Coal_CCS] = 8722
        table[tech.OCGT] = 790
        table[tech.Behind_Meter_PV] = 610
        table[tech.PV1Axis] = 653
        table[tech.Wind] = 1720
        table[tech.WindOffshore] = 2589

        table = self.totcost_per_kwh
        table[tech.Battery] = {1: 465, 2: 272, 4: 179, 8: 137}


class GenCost2023_2050_NZE2050(GenCost2023):
    """GenCost 2022-23 costs for 2050 (Global NZE by 2050)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2023.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 4361
        table[tech.CCGT] = 1565
        table[tech.CCGT_CCS] = 3012
        table[tech.CentralReceiver] = 3087
        table[tech.Coal_CCS] = 8083
        table[tech.OCGT] = 768
        table[tech.Behind_Meter_PV] = 483
        table[tech.PV1Axis] = 513
        table[tech.Wind] = 1642
        table[tech.WindOffshore] = 2539

        table = self.totcost_per_kwh
        table[tech.Battery] = {1: 410, 2: 241, 4: 162, 8: 126}


class GenCost2023_2030_NZEPost2050(GenCost2023):
    """GenCost 2022-23 costs for 2030 (Global NZE post 2050)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2023.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 4668
        table[tech.CCGT] = 1672
        table[tech.CCGT_CCS] = 4283
        table[tech.CentralReceiver] = 5124
        table[tech.Coal_CCS] = 9639
        table[tech.OCGT] = 828
        table[tech.Behind_Meter_PV] = 976
        table[tech.PV1Axis] = 1071
        table[tech.Wind] = 1900
        table[tech.WindOffshore] = 4352

        table = self.totcost_per_kwh
        table[tech.Battery] = {1: 623, 2: 401, 4: 293, 8: 244}


class GenCost2023_2040_NZEPost2050(GenCost2023):
    """GenCost 2022-23 costs for 2040 (Global NZE post 2050)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2023.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 4484
        table[tech.CCGT] = 1610
        table[tech.CCGT_CCS] = 3518
        table[tech.CentralReceiver] = 4105
        table[tech.Coal_CCS] = 8739
        table[tech.OCGT] = 790
        table[tech.Behind_Meter_PV] = 618
        table[tech.PV1Axis] = 687
        table[tech.Wind] = 1817
        table[tech.WindOffshore] = 3988

        table = self.totcost_per_kwh
        table[tech.Battery] = {1: 507, 2: 322, 4: 230, 8: 189}


class GenCost2023_2050_NZEPost2050(GenCost2023):
    """GenCost 2022-23 costs for 2050 (Global NZE post 2050)."""

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        GenCost2023.__init__(self, discount, coal_price, gas_price, ccs_price)
        table = self.capcost_per_kw
        table[tech.Black_Coal] = 4361
        table[tech.CCGT] = 1565
        table[tech.CCGT_CCS] = 3037
        table[tech.CentralReceiver] = 3419
        table[tech.Coal_CCS] = 8109
        table[tech.OCGT] = 768
        table[tech.Behind_Meter_PV] = 525
        table[tech.PV1Axis] = 586
        table[tech.Wind] = 1787
        table[tech.WindOffshore] = 3751

        table = self.totcost_per_kwh
        table[tech.Battery] = {1: 443, 2: 284, 4: 207, 8: 172}
