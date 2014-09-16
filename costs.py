# Copyright (C) 2012, 2013 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Generation technology costs."""

import generators as tech


def annuity_factor(t, r):
    """Return the annuity factor for lifetime t and interest rate r."""
    return (1 - (1 / pow(1 + r, t))) / r


class NullCosts:

    """All costs are zero. Useful for debugging."""

    def __init__(self):
        self.capcost_per_kw_per_yr = {}
        self.fixed_om_costs = {}
        self.opcost_per_mwh = {}
        self.annuityf = 1

        for t in [tech.Biofuel, tech.Black_Coal, tech.CCGT,
                  tech.CCGT_CCS, tech.CST, tech.Coal_CCS, tech.DemandResponse,
                  tech.Geothermal, tech.Hydro, tech.OCGT, tech.PV, tech.PumpedHydro,
                  tech.Wind, ]:
            self.capcost_per_kw_per_yr[t] = 0
            self.opcost_per_mwh[t] = 0
            self.fixed_om_costs[t] = 0


class AETA2012_2030:

    """Australian Energy Technology Assessment (2012) costs for 2030.

    Source: BREE AETA report (2012), bree.gov.au
    """

    lifetime = 30
    escalation = 1.171

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object given discount rate, coal, gas and CCS costs."""
        self.discount_rate = discount
        self.ccs_storage_per_t = ccs_price
        self.coal_price_per_gj = coal_price
        self.gas_price_per_gj = gas_price
        self.capcost_per_kw_per_yr = {}
        self.opcost_per_mwh = {}
        self.fixed_om_costs = {}
        self.annuityf = annuity_factor(self.lifetime, discount)

        # Common capital costs
        table = self.capcost_per_kw_per_yr
        table[tech.Hydro] = 0
        table[tech.PumpedHydro] = 0
        table[tech.DemandResponse] = 0

        # Variable O&M (VOM) costs
        table = self.opcost_per_mwh
        table[tech.Hydro] = 0
        table[tech.PumpedHydro] = 0
        table[tech.Wind] = 12 * self.escalation
        table[tech.CST] = 20 * self.escalation
        table[tech.PV] = 0
        table[tech.CSV_PV] = 0
        table[tech.Biofuel] = 10 * self.escalation + 80  # (fuel)
        table[tech.CCGT] = 4 * self.escalation
        table[tech.OCGT] = 10 * self.escalation
        table[tech.CCGT_CCS] = 9 * self.escalation
        table[tech.Coal_CCS] = 15 * self.escalation
        table[tech.Black_Coal] = 7 * self.escalation
        table[tech.Geothermal] = 0

        # Fixed O&M (FOM) costs
        table = self.fixed_om_costs
        table[tech.DemandResponse] = 0
        table[tech.Hydro] = 0
        table[tech.PumpedHydro] = 0
        table[tech.Wind] = 40 * self.escalation
        table[tech.CST] = 65 * self.escalation
        table[tech.PV] = 25 * self.escalation
        table[tech.CSV_PV] = 38 * self.escalation
        table[tech.Biofuel] = 4 * self.escalation
        table[tech.CCGT] = 10 * self.escalation
        table[tech.OCGT] = 4 * self.escalation
        table[tech.CCGT_CCS] = 17 * self.escalation
        table[tech.Coal_CCS] = 73.2 * self.escalation
        table[tech.Black_Coal] = 50.5 * self.escalation
        table[tech.Geothermal] = 200 * self.escalation


class AETA2012_2030Low (AETA2012_2030):

    """AETA (2012) costs for 2030, low end of the range."""

    def __init__(self, discount, coal_price, gas_price, ccs_storage_costs):
        """Construct a cost object given discount rate, coal, gas and CCS costs.

        >>> obj = AETA2012_2030Low(0.05, 1.00, 9.00, 30)
        """
        AETA2012_2030.__init__(self, discount, coal_price, gas_price,
                               ccs_storage_costs)
        af = self.annuityf
        # capital costs in $/kW
        table = self.capcost_per_kw_per_yr
        fom = self.fixed_om_costs
        table[tech.Wind] = 1701 / af + fom[tech.Wind]
        table[tech.CST] = 4563 / af + fom[tech.CST]
        table[tech.PV] = 1482 / af + fom[tech.PV]
        table[tech.CSV_PV] = 2013 / af + fom[tech.CSV_PV]
        table[tech.Biofuel] = 694 / af + fom[tech.Biofuel]
        table[tech.CCGT] = 1015 / af + fom[tech.CCGT]
        table[tech.OCGT] = 694 / af + fom[tech.OCGT]
        table[tech.CCGT_CCS] = 2095 / af + fom[tech.CCGT_CCS]
        table[tech.Coal_CCS] = 4453 / af + fom[tech.Coal_CCS]
        table[tech.Black_Coal] = 2947 / af + fom[tech.Black_Coal]
        table[tech.Geothermal] = 6645 / af + fom[tech.Geothermal]


class AETA2012_2030High (AETA2012_2030):

    """AETA (2012) costs for 2030, high end of the range."""

    def __init__(self, discount, coal_price, gas_price, ccs_storage_costs):
        """Construct a cost object given discount rate, coal, gas and CCS costs.

        >>> obj = AETA2012_2030High(0.05, 1.00, 9.00, 30)
        """
        AETA2012_2030.__init__(self, discount, coal_price, gas_price,
                               ccs_storage_costs)
        af = self.annuityf
        # capital costs in $/kW
        table = self.capcost_per_kw_per_yr
        fom = self.fixed_om_costs
        table[tech.Wind] = 1917 / af + fom[tech.Wind]
        table[tech.CST] = 5659 / af + fom[tech.CST]
        table[tech.PV] = 1871 / af + fom[tech.PV]
        table[tech.CSV_PV] = 2542 / af + fom[tech.CSV_PV]
        table[tech.Biofuel] = 809 / af + fom[tech.Biofuel]
        table[tech.CCGT] = 1221 / af + fom[tech.CCGT]
        table[tech.OCGT] = 809 / af + fom[tech.OCGT]
        table[tech.CCGT_CCS] = 2405 / af + fom[tech.CCGT_CCS]
        table[tech.Coal_CCS] = 4727 / af + fom[tech.Coal_CCS]
        table[tech.Black_Coal] = 3128 / af + fom[tech.Black_Coal]
        table[tech.Geothermal] = 7822 / af + fom[tech.Geothermal]


class AETA2013_2030Low (AETA2012_2030Low):
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
        fom[tech.CST] = 72.381 * self.escalation
        vom = self.opcost_per_mwh
        vom[tech.Wind] = 10 * self.escalation
        vom[tech.CST] = 11.39 * self.escalation


class AETA2013_2030High (AETA2012_2030High):
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
        fom[tech.CST] = 72.381 * self.escalation
        vom = self.opcost_per_mwh
        vom[tech.Wind] = 10 * self.escalation
        vom[tech.CST] = 11.39 * self.escalation
