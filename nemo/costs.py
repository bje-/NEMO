# Copyright (C) 2012, 2013 Ben Elliston
# Copyright (C) 2014, 2015 The University of New South Wales
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

# We use class names here that upset Pylint.
# pylint: disable=invalid-name

"""Generation technology costs."""

# pylint: disable=too-many-lines

from collections import defaultdict

from nemo import generators as tech


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


class Common:
    """Costs common to all cost classes (eg, existing hydro)."""

    def __init__(self, discount):
        """
        Initialise common costs.

        Derived costs can call update() on these dicts.
        """
        self.discount_rate = discount

        # Common capital costs
        self.capcost_per_kw = {
            tech.DemandResponse: 0,
            tech.Diesel: 0,
            tech.Hydro: 0,
            tech.PumpedHydroPump: 0,
            tech.PumpedHydroTurbine: 0}

        # Variable O&M (VOM) costs
        self.opcost_per_mwh = {
            # a reasonable estimate of diesel VOM
            tech.Diesel: 8,
            tech.Hydro: 0,
            tech.PumpedHydroPump: 0,
            tech.PumpedHydroTurbine: 0}

        # Fixed O&M (FOM) costs
        self.fixed_om_costs = {
            tech.DemandResponse: 0,
            tech.Diesel: 0,
            tech.Hydro: 0,
            tech.PumpedHydroPump: 0,
            tech.PumpedHydroTurbine: 0}

    def annuity_factor(self, lifetime):
        """Return the annuity factor for lifetime t and discount rate r."""
        rate = self.discount_rate
        return (1 - (1 / (1 + rate) ** lifetime)) / rate


class APGTR2015(Common):
    """Australian Power Generation Technology Report costs in 2015.

    Source: CO2CRC Australian Power Generation Technology Report (2015)
    """

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        Common.__init__(self, discount)
        self.ccs_storage_per_t = ccs_price
        # bioenergy costs taken from CSIRO energy storage report for AEMO
        self.bioenergy_price_per_gj = 12
        self.coal_price_per_gj = coal_price
        self.gas_price_per_gj = gas_price
        self.diesel_price_per_litre = 1.50

        # Variable O&M (VOM) costs
        self.opcost_per_mwh.update({
            tech.Wind: 0,
            tech.CentralReceiver: 4,
            tech.PV: 0,
            tech.PV1Axis: 0,
            tech.CCGT: 1.5,
            tech.OCGT: 12,
            tech.Black_Coal: 2.5})

        # Fixed O&M (FOM) costs
        self.fixed_om_costs.update({
            tech.Wind: 55,
            tech.CentralReceiver: 65,
            tech.PV: 30,
            tech.PV1Axis: 35,
            tech.CCGT: 20,
            tech.OCGT: 8,
            tech.Black_Coal: 45})

        table = self.capcost_per_kw
        table[tech.Wind] = 2450
        table[tech.CentralReceiver] = 8500
        table[tech.PV] = 2100
        table[tech.PV1Axis] = 2700
        table[tech.CCGT] = 1450
        table[tech.OCGT] = 1000
        table[tech.Black_Coal] = 3000


class APGTR2030(APGTR2015):
    """Australian Power Generation Technology Report (2015) costs in 2030.

    Source: CO2CRC Australian Power Generation Technology Report (2015)
    """

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        APGTR2015.__init__(self, discount, coal_price, gas_price, ccs_price)

        # Modify the capital costs in APGTR2015 by specified learning rates.
        # Fixed and variable O&M remain the same as in 2015.
        table = self.capcost_per_kw
        table[tech.Wind] *= 0.8
        table[tech.CentralReceiver] *= 0.8
        table[tech.PV] *= 0.5
        table[tech.PV1Axis] *= 0.5
        table[tech.CCGT] *= 0.9
        table[tech.OCGT] *= 1.1
        table[tech.Black_Coal] *= 0.9


class AETA2012_2030(Common):
    """Australian Energy Technology Assessment (2012) costs for 2030.

    Source: BREE AETA report (2012), bree.gov.au
    """

    ESCALATION = 1.171

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        Common.__init__(self, discount)
        self.ccs_storage_per_t = ccs_price
        # bioenergy costs taken from CSIRO energy storage report for AEMO
        self.bioenergy_price_per_gj = 12
        self.coal_price_per_gj = coal_price
        self.gas_price_per_gj = gas_price
        self.diesel_price_per_litre = 1.50

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


class CEEM2016_2030(AETA2012_2030Mid):
    """
    CEEM 2016 custom costs.

    These custom costs were produced by CEEM -- AETA (2013) mid costs
    with CO2CRC Power Generation Technology Report 2030 capital costs
    for utility-scale PV.
    """

    def __init__(self, discount, coal_price, gas_price, ccs_storage_costs):
        """Construct a cost object."""
        AETA2012_2030Mid.__init__(self, discount, coal_price, gas_price,
                                  ccs_storage_costs)

        # CO2CRC Power Generation Technology Report (p. 253) gives a
        # narrow range of $1,108 to $1,218 per kW. Meet half-way.
        self.capcost_per_kw[tech.PV1Axis] = 1255


class GenCost2021(Common):
    """GenCost 2020-21 costs.

    Source:
    CSIRO GenCost 2020-21 report
    https://data.csiro.au/collections/collection/CIcsiro:44228
    """

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        Common.__init__(self, discount)
        self.ccs_storage_per_t = ccs_price
        # bioenergy costs taken from CSIRO energy storage report for AEMO
        self.bioenergy_price_per_gj = 12
        self.coal_price_per_gj = coal_price
        self.gas_price_per_gj = gas_price
        self.diesel_price_per_litre = 1.50

        # Fixed O&M (FOM) costs
        # Note: These are the same for all years (2030, 2040, 2050),
        # so we can set them once here.
        self.fixed_om_costs.update({
            tech.Black_Coal: 53.2,
            tech.CCGT: 10.9,
            tech.CCGT_CCS: 16.4,
            tech.CentralReceiver: 142.5,
            tech.Coal_CCS: 77.8,
            tech.OCGT: 10.2,
            tech.PV1Axis: 17.0,
            tech.Wind: 25.0})

        # Variable O&M (VOM) costs
        # Likewise, these are the same for all years (2030, 2040, 2050).
        self.opcost_per_mwh.update({
            tech.Black_Coal: 4.2,
            tech.CCGT: 3.7,
            tech.CCGT_CCS: 7.2,
            tech.CentralReceiver: 0,
            tech.Coal_CCS: 8.0,
            tech.OCGT: 2.4,
            tech.PV1Axis: 0,
            tech.Wind: 0})


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


class GenCost2022(Common):
    """GenCost 2021-22 costs.

    Source:
    CSIRO GenCost 2021-22 report
    https://data.csiro.au/collections/collection/CIcsiro:44228
    """

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        Common.__init__(self, discount)
        self.ccs_storage_per_t = ccs_price
        # bioenergy costs taken from CSIRO energy storage report for AEMO
        self.bioenergy_price_per_gj = 12
        self.coal_price_per_gj = coal_price
        self.gas_price_per_gj = gas_price
        self.diesel_price_per_litre = 1.50

        # Fixed O&M (FOM) costs
        # Note: These are the same for all years (2030, 2040, 2050),
        # so we can set them once here.
        self.fixed_om_costs.update({
            tech.Black_Coal: 53.2,
            tech.CCGT: 10.9,
            tech.CCGT_CCS: 16.4,
            tech.CentralReceiver: 120.0,
            tech.Coal_CCS: 77.8,
            tech.OCGT: 10.2,
            tech.Behind_Meter_PV: 0,
            tech.PV1Axis: 17.0,
            tech.Wind: 25.0,
            tech.WindOffshore: 149.9})

        # Variable O&M (VOM) costs
        # Likewise, these are the same for all years (2030, 2040, 2050).
        self.opcost_per_mwh.update({
            tech.Black_Coal: 4.2,
            tech.CCGT: 3.7,
            tech.CCGT_CCS: 7.2,
            tech.CentralReceiver: 0,
            tech.Coal_CCS: 8.0,
            tech.OCGT: 7.3,
            tech.Behind_Meter_PV: 0,
            tech.PV1Axis: 0,
            tech.Wind: 0,
            tech.WindOffshore: 0})

        # Storage is expressed on a total cost basis (GenCost 2022, p. 18)
        # Figures are entered in the classes in $/kWh, but these are
        # converted to $/kW in capcost().
        self.totcost_per_kwh = {}


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


class GenCost2023(Common):
    """GenCost 2022-23 costs.

    Source:
    CSIRO GenCost 2022-23 report
    https://data.csiro.au/collections/collection/CIcsiro:44228
    """

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        Common.__init__(self, discount)
        self.ccs_storage_per_t = ccs_price
        # bioenergy costs taken from CSIRO energy storage report for AEMO
        self.bioenergy_price_per_gj = 12
        self.coal_price_per_gj = coal_price
        self.gas_price_per_gj = gas_price
        self.diesel_price_per_litre = 1.50

        # Fixed O&M (FOM) costs
        # Note: These are the same for all years (2030, 2040, 2050),
        # so we can set them once here.
        self.fixed_om_costs.update({
            tech.Black_Coal: 53.2,
            tech.CCGT: 10.9,
            tech.CCGT_CCS: 16.4,
            tech.CentralReceiver: 120.0,
            tech.Coal_CCS: 77.8,
            tech.OCGT: 10.2,
            tech.Behind_Meter_PV: 0,
            tech.PV1Axis: 17.0,
            tech.Wind: 25.0,
            tech.WindOffshore: 149.9})

        # Variable O&M (VOM) costs
        # Likewise, these are the same for all years (2030, 2040, 2050).
        self.opcost_per_mwh.update({
            tech.Black_Coal: 4.2,
            tech.CCGT: 3.7,
            tech.CCGT_CCS: 7.2,
            tech.CentralReceiver: 0,
            tech.Coal_CCS: 8.0,
            tech.OCGT: 7.3,
            tech.Behind_Meter_PV: 0,
            tech.PV1Axis: 0,
            tech.Wind: 0,
            tech.WindOffshore: 0})

        # Storage is expressed on a total cost basis (GenCost 2023, p. 17)
        # Figures are entered in the classes in $/kWh, but these are
        # converted to $/kW in capcost().
        self.totcost_per_kwh = {}


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


cost_scenarios = {'Null': NullCosts,
                  'AETA2012-in2030-low': AETA2012_2030Low,
                  'AETA2012-in2030-mid': AETA2012_2030Mid,
                  'AETA2012-in2030-high': AETA2012_2030High,
                  'AETA2013-in2030-low': AETA2013_2030Low,
                  'AETA2013-in2030-mid': AETA2013_2030Mid,
                  'AETA2013-in2030-high': AETA2013_2030High,
                  'CEEM2016-in2030': CEEM2016_2030,
                  'GenCost2021-in2020': GenCost2021_2020,
                  'GenCost2021-in2030-low': GenCost2021_2030Low,
                  'GenCost2021-in2030-high': GenCost2021_2030High,
                  'GenCost2021-in2040-low': GenCost2021_2040Low,
                  'GenCost2021-in2040-high': GenCost2021_2040High,
                  'GenCost2021-in2050-low': GenCost2021_2050Low,
                  'GenCost2021-in2050-high': GenCost2021_2050High,
                  'GenCost2022-in2021': GenCost2022_2021,
                  'GenCost2022-in2030-CP': GenCost2022_2030_CP,
                  'GenCost2022-in2030-NZE2050': GenCost2022_2030_NZE2050,
                  'GenCost2022-in2030-NZE2050+': GenCost2022_2030_NZEPost2050,
                  'GenCost2022-in2040-CP': GenCost2022_2040_CP,
                  'GenCost2022-in2040-NZE2050': GenCost2022_2040_NZE2050,
                  'GenCost2022-in2040-NZE2050+': GenCost2022_2040_NZEPost2050,
                  'GenCost2022-in2050-CP': GenCost2022_2050_CP,
                  'GenCost2022-in2050-NZE2050': GenCost2022_2050_NZE2050,
                  'GenCost2022-in2050-NZE2050+': GenCost2022_2050_NZEPost2050,
                  'GenCost2023-in2030-CP': GenCost2023_2030_CP,
                  'GenCost2023-in2030-NZE2050': GenCost2023_2030_NZE2050,
                  'GenCost2023-in2030-NZE2050+': GenCost2023_2030_NZEPost2050,
                  'GenCost2023-in2040-CP': GenCost2023_2040_CP,
                  'GenCost2023-in2040-NZE2050': GenCost2023_2040_NZE2050,
                  'GenCost2023-in2040-NZE2050+': GenCost2023_2040_NZEPost2050,
                  'GenCost2023-in2050-CP': GenCost2023_2050_CP,
                  'GenCost2023-in2050-NZE2050': GenCost2023_2050_NZE2050,
                  'GenCost2023-in2050-NZE2050+': GenCost2023_2050_NZEPost2050,
                  'PGTR2015': APGTR2015,
                  'PGTR2030': APGTR2030}
