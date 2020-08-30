# Copyright (C) 2012, 2013 Ben Elliston
# Copyright (C) 2014, 2015 The University of New South Wales
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Generation technology costs."""
from nemo import generators as tech


def annuity_factor(t, r):
    """Return the annuity factor for lifetime t and interest rate r."""
    return (1 - (1 / (1 + r) ** t)) / r


def txcost(x):
    """Transmission cost expression."""
    return 0 if x == 0 else 965 if x > 5000 else 16319 * (x ** -0.332)


class NullCosts():

    """All costs are zero. Useful for debugging."""

    class _ZeroDict(dict):
        """Return 0 for any key."""
        def __getitem__(self, key):
            return dict.get(self, key, 0)

    # pylint: disable=unused-argument
    def __init__(self, discount=0, coal_price=0, gas_price=0, ccs_price=0):
        self.capcost_per_kw = self._ZeroDict()
        self.fixed_om_costs = self._ZeroDict()
        self.opcost_per_mwh = self._ZeroDict()
        self.annuityf = 1
        self.ccs_storage_per_t = 0
        self.bioenergy_price_per_gj = 0
        self.coal_price_per_gj = 0
        self.gas_price_per_gj = 0
        self.diesel_price_per_litre = 0
        self.carbon = 0


class APGTR2015():

    """Australian Power Generation Technology Report costs in 2015.

    Source: CO2CRC Australian Power Generation Technology Report (2015)
    """

    lifetime = 30
    escalation = 1.0

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object given discount rate, coal, gas and CCS costs."""
        self.discount_rate = discount
        self.ccs_storage_per_t = ccs_price
        # bioenergy costs are taken from the CSIRO energy storage report for AEMO
        self.bioenergy_price_per_gj = 12
        self.coal_price_per_gj = coal_price
        self.gas_price_per_gj = gas_price
        self.diesel_price_per_litre = 1.50
        self.annuityf = annuity_factor(self.lifetime, discount)

        # Common capital costs
        self.capcost_per_kw = {
            tech.Hydro: 0,
            tech.PumpedHydro: 0,
            tech.Diesel: 0,
            tech.DemandResponse: 0}

        # Variable O&M (VOM) costs
        self.opcost_per_mwh = {
            tech.Hydro: 0,
            tech.PumpedHydro: 0,
            tech.Diesel: 0,
            tech.Wind: 0,
            tech.CentralReceiver: 4,
            tech.PV: 0,
            tech.PV1Axis: 0,
            tech.CCGT: 1.5,
            tech.OCGT: 12,
            tech.Black_Coal: 2.5}
        # same as OCGT
        self.opcost_per_mwh[tech.Biofuel] = self.opcost_per_mwh[tech.OCGT]

        # Fixed O&M (FOM) costs
        self.fixed_om_costs = {
            tech.DemandResponse: 0,
            tech.Diesel: 0,
            tech.Hydro: 0,
            tech.PumpedHydro: 0,
            tech.Wind: 55,
            tech.CentralReceiver: 65,
            tech.PV: 30,
            tech.PV1Axis: 35,
            tech.CCGT: 20,
            tech.OCGT: 8,
            tech.Black_Coal: 45}
        # same as OCGT
        self.fixed_om_costs[tech.Biofuel] = self.fixed_om_costs[tech.OCGT]

        table = self.capcost_per_kw
        table[tech.Wind] = 2450
        table[tech.CentralReceiver] = 8500
        table[tech.PV] = 2100
        table[tech.PV1Axis] = 2700
        table[tech.CCGT] = 1450
        table[tech.OCGT] = 1000
        table[tech.Black_Coal] = 3000
        table[tech.Biofuel] = table[tech.OCGT]  # same as OCGT


class APGTR2030(APGTR2015):

    """Australian Power Generation Technology Report (2015) costs in 2030.

    Source: CO2CRC Australian Power Generation Technology Report (2015)
    """

    def __init__(self, discount, coal_price, gas_price, ccs_price):
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
        table[tech.Biofuel] = table[tech.OCGT]  # same as OCGT


class AETA2012_2030():

    """Australian Energy Technology Assessment (2012) costs for 2030.

    Source: BREE AETA report (2012), bree.gov.au
    """

    lifetime = 30
    escalation = 1.171

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object given discount rate, coal, gas and CCS costs."""
        self.discount_rate = discount
        self.ccs_storage_per_t = ccs_price
        # bioenergy costs are taken from the CSIRO energy storage report for AEMO
        self.bioenergy_price_per_gj = 12
        self.coal_price_per_gj = coal_price
        self.gas_price_per_gj = gas_price
        self.diesel_price_per_litre = 1.50
        self.annuityf = annuity_factor(self.lifetime, discount)

        # Common capital costs
        self.capcost_per_kw = {
            tech.Hydro: 0,
            tech.PumpedHydro: 0,
            tech.Diesel: 0,
            tech.DemandResponse: 0}

        # Variable O&M (VOM) costs
        self.opcost_per_mwh = {
            tech.Hydro: 0,
            tech.PumpedHydro: 0,
            tech.Diesel: 0,
            tech.Wind: 12 * self.escalation,
            tech.CentralReceiver: 15 * self.escalation,
            tech.ParabolicTrough: 20 * self.escalation,
            tech.PV: 0,
            tech.PV1Axis: 0,
            tech.CCGT: 4 * self.escalation,
            tech.OCGT: 10 * self.escalation,
            tech.CCGT_CCS: 9 * self.escalation,
            tech.Coal_CCS: 15 * self.escalation,
            tech.Black_Coal: 7 * self.escalation,
            tech.Geothermal_HSA: 0,
            tech.Geothermal_EGS: 0}
        # same as OCGT
        self.opcost_per_mwh[tech.Biofuel] = self.opcost_per_mwh[tech.OCGT]

        # Fixed O&M (FOM) costs
        self.fixed_om_costs = {
            tech.DemandResponse: 0,
            tech.Diesel: 0,
            tech.Hydro: 0,
            tech.PumpedHydro: 0,
            tech.Wind: 40 * self.escalation,
            tech.CentralReceiver: 60 * self.escalation,
            tech.ParabolicTrough: 65 * self.escalation,
            tech.PV: 25 * self.escalation,
            tech.PV1Axis: 38 * self.escalation,
            tech.CCGT: 10 * self.escalation,
            tech.OCGT: 4 * self.escalation,
            tech.CCGT_CCS: 17 * self.escalation,
            tech.Coal_CCS: 73.2 * self.escalation,
            tech.Black_Coal: 50.5 * self.escalation,
            tech.Geothermal_HSA: 200 * self.escalation,
            tech.Geothermal_EGS: 170 * self.escalation}
        # same as OCGT
        self.fixed_om_costs[tech.Biofuel] = self.fixed_om_costs[tech.OCGT]


class AETA2012_2030Low(AETA2012_2030):

    """AETA (2012) costs for 2030, low end of the range."""

    def __init__(self, discount, coal_price, gas_price, ccs_storage_costs):
        """Construct a cost object given discount rate, coal, gas and CCS costs.

        >>> obj = AETA2012_2030Low(0.05, 1.00, 9.00, 30)
        """
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
        table[tech.Biofuel] = table[tech.OCGT]  # same as OCGT


class AETA2012_2030High(AETA2012_2030):

    """AETA (2012) costs for 2030, high end of the range."""

    def __init__(self, discount, coal_price, gas_price, ccs_storage_costs):
        """Construct a cost object given discount rate, coal, gas and CCS costs.

        >>> obj = AETA2012_2030High(0.05, 1.00, 9.00, 30)
        """
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
        table[tech.Biofuel] = table[tech.OCGT]  # same as OCGT


class AETA2012_2030Mid(AETA2012_2030):

    """AETA (2012) costs for 2030, middle of the range."""

    def __init__(self, discount, coal_price, gas_price, ccs_storage_costs):
        """Construct a cost object given discount rate, coal, gas and CCS costs.

        >>> obj = AETA2012_2030Mid(0.05, 1.00, 9.00, 30)
        """
        AETA2012_2030.__init__(self, discount, coal_price, gas_price,
                               ccs_storage_costs)

        low = AETA2012_2030Low(discount, coal_price, gas_price, ccs_storage_costs)
        high = AETA2012_2030High(discount, coal_price, gas_price, ccs_storage_costs)
        assert low.opcost_per_mwh == high.opcost_per_mwh
        assert low.fixed_om_costs == high.fixed_om_costs

        table = self.capcost_per_kw
        lowtable = low.capcost_per_kw
        hightable = high.capcost_per_kw
        for t in lowtable:
            table[t] = lowtable[t] / 2 + hightable[t] / 2


class AETA2013_2030Low(AETA2012_2030Low):
    """AETA (2013 update) costs for 2030, low end of the range."""

    def __init__(self, discount, coal_price, gas_price, ccs_storage_costs):
        """Construct a cost object given discount rate, coal, gas and CCS costs.

        >>> obj = AETA2013_2030Low(0.05, 1.00, 9.00, 30)
        """
        AETA2012_2030Low.__init__(self, discount, coal_price, gas_price,
                                  ccs_storage_costs)

        # Override a few O&M costs.
        fom = self.fixed_om_costs
        fom[tech.Wind] = 32.5 * self.escalation
        fom[tech.PV1Axis] = 30 * self.escalation
        fom[tech.CentralReceiver] = 71.312 * self.escalation
        fom[tech.ParabolicTrough] = 72.381 * self.escalation
        vom = self.opcost_per_mwh
        vom[tech.Wind] = 10 * self.escalation
        vom[tech.CentralReceiver] = 5.65 * self.escalation
        vom[tech.ParabolicTrough] = 11.39 * self.escalation


class AETA2013_2030High(AETA2012_2030High):
    """AETA (2013 update) costs for 2030, high end of the range."""

    def __init__(self, discount, coal_price, gas_price, ccs_storage_costs):
        """Construct a cost object given discount rate, coal, gas and CCS costs.

        >>> obj = AETA2013_2030High(0.05, 1.00, 9.00, 30)
        """
        AETA2012_2030High.__init__(self, discount, coal_price, gas_price,
                                   ccs_storage_costs)

        # Override a few O&M costs.
        fom = self.fixed_om_costs
        fom[tech.Wind] = 32.5 * self.escalation
        fom[tech.PV1Axis] = 30 * self.escalation
        fom[tech.CentralReceiver] = 71.312 * self.escalation
        fom[tech.ParabolicTrough] = 72.381 * self.escalation
        vom = self.opcost_per_mwh
        vom[tech.Wind] = 10 * self.escalation
        vom[tech.CentralReceiver] = 5.65 * self.escalation
        vom[tech.ParabolicTrough] = 11.39 * self.escalation


class AETA2013_2030Mid(AETA2012_2030):

    """AETA (2013) costs for 2030, middle of the range."""

    def __init__(self, discount, coal_price, gas_price, ccs_storage_costs):
        """Construct a cost object given discount rate, coal, gas and CCS costs.

        >>> obj = AETA2013_2030Mid(0.05, 1.00, 9.00, 30)
        """
        AETA2012_2030.__init__(self, discount, coal_price, gas_price,
                               ccs_storage_costs)

        low = AETA2013_2030Low(discount, coal_price, gas_price, ccs_storage_costs)
        high = AETA2013_2030High(discount, coal_price, gas_price, ccs_storage_costs)
        assert low.opcost_per_mwh == high.opcost_per_mwh
        self.opcost_per_mwh = low.opcost_per_mwh
        assert low.fixed_om_costs == high.fixed_om_costs
        self.fixed_om_costs = low.fixed_om_costs

        table = self.capcost_per_kw
        lowtable = low.capcost_per_kw
        hightable = high.capcost_per_kw
        for t in lowtable:
            table[t] = lowtable[t] / 2 + hightable[t] / 2


class CEEM2016_2030(AETA2012_2030Mid):

    """Custom costs produced by CEEM -- AETA (2013) mid costs with CO2CRC
    Power Generation Technology Report 2030 capital costs for
    utility-scale PV."""

    def __init__(self, discount, coal_price, gas_price, ccs_storage_costs):
        """Construct a cost object given discount rate, coal, gas and CCS costs.

        >>> obj = CEEM2016_2030(0.05, 1.00, 9.00, 30)
        """
        AETA2012_2030Mid.__init__(self, discount, coal_price, gas_price,
                                  ccs_storage_costs)

        # CO2CRC Power Generation Technology Report (p. 253) gives a
        # narrow range of $1,108 to $1,218 per kW. Meet half-way.
        self.capcost_per_kw[tech.PV1Axis] = 1255


cost_scenarios = {'Null': NullCosts,
                  'AETA2012-in2030-low': AETA2012_2030Low,
                  'AETA2012-in2030-mid': AETA2012_2030Mid,
                  'AETA2012-in2030-high': AETA2012_2030High,
                  'AETA2013-in2030-low': AETA2013_2030Low,
                  'AETA2013-in2030-mid': AETA2013_2030Mid,
                  'AETA2013-in2030-high': AETA2013_2030High,
                  'CEEM2016-in2030': CEEM2016_2030,
                  'PGTR2015': APGTR2015,
                  'PGTR2030': APGTR2030}
