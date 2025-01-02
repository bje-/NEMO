# Copyright (C) 2024 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Australian Energy Technology Assessment costs."""

from nemo import generators as tech

from .common import Common

# We use class names here that upset Pylint.
# pylint: disable=invalid-name, disable=duplicate-code


class AETA2012_2030(Common):
    """Australian Energy Technology Assessment (2012) costs for 2030.

    Source: BREE AETA report (2012), bree.gov.au
    """

    ESCALATION = 1.171

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        Common.__init__(self, discount)
        self.ccs_storage_per_t = ccs_price
        self.coal_price_per_gj = coal_price
        self.gas_price_per_gj = gas_price

        # Variable O&M (VOM) costs
        self.opcost_per_mwh.update({
            tech.Wind: 12 * self.ESCALATION,
            tech.CentralReceiver: 15 * self.ESCALATION,
            tech.ParabolicTrough: 20 * self.ESCALATION,
            tech.PV: 0,
            tech.PV1Axis: 0,
            tech.CCGT: 4 * self.ESCALATION,
            tech.OCGT: 10 * self.ESCALATION,
            tech.CCGT_CCS: 9 * self.ESCALATION,
            tech.Coal_CCS: 15 * self.ESCALATION,
            tech.Black_Coal: 7 * self.ESCALATION,
            tech.Geothermal_HSA: 0,
            tech.Geothermal_EGS: 0})

        # Fixed O&M (FOM) costs
        self.fixed_om_costs.update({
            tech.Wind: 40 * self.ESCALATION,
            tech.CentralReceiver: 60 * self.ESCALATION,
            tech.ParabolicTrough: 65 * self.ESCALATION,
            tech.PV: 25 * self.ESCALATION,
            tech.PV1Axis: 38 * self.ESCALATION,
            tech.CCGT: 10 * self.ESCALATION,
            tech.OCGT: 4 * self.ESCALATION,
            tech.CCGT_CCS: 17 * self.ESCALATION,
            tech.Coal_CCS: 73.2 * self.ESCALATION,
            tech.Black_Coal: 50.5 * self.ESCALATION,
            tech.Geothermal_HSA: 200 * self.ESCALATION,
            tech.Geothermal_EGS: 170 * self.ESCALATION})


class AETA2012_2030Low(AETA2012_2030):
    """AETA (2012) costs for 2030, low end of the range."""

    def __init__(self, discount, coal_price, gas_price, ccs_storage_costs):
        """Construct a cost object."""
        AETA2012_2030.__init__(self, discount, coal_price, gas_price,
                               ccs_storage_costs)
        # capital costs in $/kW
        table = self.capcost_per_kw
        table[tech.Wind] = 1701
        table[tech.CentralReceiver] = 4203
        table[tech.ParabolicTrough] = 4563
        table[tech.PV] = 1482
        table[tech.PV1Axis] = 2013
        table[tech.CCGT] = 1015
        table[tech.OCGT] = 694
        table[tech.CCGT_CCS] = 2095
        table[tech.Coal_CCS] = 4453
        table[tech.Black_Coal] = 2947
        table[tech.Geothermal_HSA] = 6645
        table[tech.Geothermal_EGS] = 10331


class AETA2012_2030High(AETA2012_2030):
    """AETA (2012) costs for 2030, high end of the range."""

    def __init__(self, discount, coal_price, gas_price, ccs_storage_costs):
        """Construct a cost object."""
        AETA2012_2030.__init__(self, discount, coal_price, gas_price,
                               ccs_storage_costs)
        # capital costs in $/kW
        table = self.capcost_per_kw
        table[tech.Wind] = 1917
        table[tech.CentralReceiver] = 5253
        table[tech.ParabolicTrough] = 5659
        table[tech.PV] = 1871
        table[tech.PV1Axis] = 2542
        table[tech.CCGT] = 1221
        table[tech.OCGT] = 809
        table[tech.CCGT_CCS] = 2405
        table[tech.Coal_CCS] = 4727
        table[tech.Black_Coal] = 3128
        table[tech.Geothermal_HSA] = 7822
        table[tech.Geothermal_EGS] = 11811


class AETA2012_2030Mid(AETA2012_2030):
    """AETA (2012) costs for 2030, middle of the range."""

    def __init__(self, discount, coal_price, gas_price, ccs_storage_costs):
        """Construct a cost object."""
        AETA2012_2030.__init__(self, discount, coal_price, gas_price,
                               ccs_storage_costs)

        low = AETA2012_2030Low(discount, coal_price, gas_price,
                               ccs_storage_costs)
        high = AETA2012_2030High(discount, coal_price, gas_price,
                                 ccs_storage_costs)
        if low.opcost_per_mwh != high.opcost_per_mwh:
            raise AssertionError
        if low.fixed_om_costs != high.fixed_om_costs:
            raise AssertionError

        table = self.capcost_per_kw
        lowtable = low.capcost_per_kw
        hightable = high.capcost_per_kw
        for key, lowcost in lowtable.items():
            highcost = hightable[key]
            table[key] = lowcost / 2 + highcost / 2


class AETA2013_2030Low(AETA2012_2030Low):
    """AETA (2013 update) costs for 2030, low end of the range."""

    def __init__(self, discount, coal_price, gas_price, ccs_storage_costs):
        """Construct a cost object."""
        AETA2012_2030Low.__init__(self, discount, coal_price, gas_price,
                                  ccs_storage_costs)

        # Override a few O&M costs.
        fom = self.fixed_om_costs
        fom[tech.Wind] = 32.5 * self.ESCALATION
        fom[tech.PV1Axis] = 30 * self.ESCALATION
        fom[tech.CentralReceiver] = 71.312 * self.ESCALATION
        fom[tech.ParabolicTrough] = 72.381 * self.ESCALATION
        vom = self.opcost_per_mwh
        vom[tech.Wind] = 10 * self.ESCALATION
        vom[tech.CentralReceiver] = 5.65 * self.ESCALATION
        vom[tech.ParabolicTrough] = 11.39 * self.ESCALATION


class AETA2013_2030High(AETA2012_2030High):
    """AETA (2013 update) costs for 2030, high end of the range."""

    def __init__(self, discount, coal_price, gas_price, ccs_storage_costs):
        """Construct a cost object."""
        AETA2012_2030High.__init__(self, discount, coal_price, gas_price,
                                   ccs_storage_costs)

        # Override a few O&M costs.
        fom = self.fixed_om_costs
        fom[tech.Wind] = 32.5 * self.ESCALATION
        fom[tech.PV1Axis] = 30 * self.ESCALATION
        fom[tech.CentralReceiver] = 71.312 * self.ESCALATION
        fom[tech.ParabolicTrough] = 72.381 * self.ESCALATION
        vom = self.opcost_per_mwh
        vom[tech.Wind] = 10 * self.ESCALATION
        vom[tech.CentralReceiver] = 5.65 * self.ESCALATION
        vom[tech.ParabolicTrough] = 11.39 * self.ESCALATION


class AETA2013_2030Mid(AETA2012_2030):
    """AETA (2013) costs for 2030, middle of the range."""

    def __init__(self, discount, coal_price, gas_price, ccs_storage_costs):
        """Construct a cost object."""
        AETA2012_2030.__init__(self, discount, coal_price, gas_price,
                               ccs_storage_costs)

        low = AETA2013_2030Low(discount, coal_price, gas_price,
                               ccs_storage_costs)
        high = AETA2013_2030High(discount, coal_price, gas_price,
                                 ccs_storage_costs)
        if low.opcost_per_mwh != high.opcost_per_mwh:
            raise AssertionError
        if low.fixed_om_costs != high.fixed_om_costs:
            raise AssertionError

        table = self.capcost_per_kw
        lowtable = low.capcost_per_kw
        hightable = high.capcost_per_kw
        for key, lowcost in lowtable.items():
            highcost = hightable[key]
            table[key] = lowcost / 2 + highcost / 2
