# Copyright (C) 2012, 2013 Ben Elliston
# Copyright (C) 2014 The University of New South Wales
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
                  tech.CCGT_CCS, tech.ParabolicTrough,
                  tech.CentralReceiver, tech.Coal_CCS,
                  tech.DemandResponse, tech.Geothermal, tech.Hydro,
                  tech.OCGT, tech.PV, tech.PumpedHydro, tech.Wind, ]:
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
        table[tech.CentralReceiver] = 15 * self.escalation
        table[tech.ParabolicTrough] = 20 * self.escalation
        table[tech.PV] = 0
        table[tech.PV1Axis] = 0
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
        table[tech.CentralReceiver] = 60 * self.escalation
        table[tech.ParabolicTrough] = 65 * self.escalation
        table[tech.PV] = 25 * self.escalation
        table[tech.PV1Axis] = 38 * self.escalation
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
        table[tech.CentralReceiver] = 4203 / af + fom[tech.CentralReceiver]
        table[tech.ParabolicTrough] = 4563 / af + fom[tech.ParabolicTrough]
        table[tech.PV] = 1482 / af + fom[tech.PV]
        table[tech.PV1Axis] = 2013 / af + fom[tech.PV1Axis]
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
        table[tech.CentralReceiver] = 5253 / af + fom[tech.CentralReceiver]
        table[tech.ParabolicTrough] = 5659 / af + fom[tech.ParabolicTrough]
        table[tech.PV] = 1871 / af + fom[tech.PV]
        table[tech.PV1Axis] = 2542 / af + fom[tech.PV1Axis]
        table[tech.Biofuel] = 809 / af + fom[tech.Biofuel]
        table[tech.CCGT] = 1221 / af + fom[tech.CCGT]
        table[tech.OCGT] = 809 / af + fom[tech.OCGT]
        table[tech.CCGT_CCS] = 2405 / af + fom[tech.CCGT_CCS]
        table[tech.Coal_CCS] = 4727 / af + fom[tech.Coal_CCS]
        table[tech.Black_Coal] = 3128 / af + fom[tech.Black_Coal]
        table[tech.Geothermal] = 7822 / af + fom[tech.Geothermal]


class AETA2012_2030Mid (AETA2012_2030):

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

        table = self.capcost_per_kw_per_yr
        lowtable = low.capcost_per_kw_per_yr
        hightable = high.capcost_per_kw_per_yr
        for t in lowtable:
            # The capital cost tables include fixed O&M (f), but
            # this averaging calculation is safe because:
            #   (low + f) / 2 + (high + f) / 2
            # is equivalent to:
            #   (low + high) / 2 + f
            table[t] = lowtable[t] / 2 + hightable[t] / 2


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
        fom[tech.PV1Axis] = 30 * self.escalation
        fom[tech.CentralReceiver] = 71.312 * self.escalation
        fom[tech.ParabolicTrough] = 72.381 * self.escalation
        vom = self.opcost_per_mwh
        vom[tech.Wind] = 10 * self.escalation
        vom[tech.CentralReceiver] = 5.65 * self.escalation
        vom[tech.ParabolicTrough] = 11.39 * self.escalation

        # Re-calculate annual capital costs for wind and CST.
        af = self.annuityf
        table = self.capcost_per_kw_per_yr
        fom = self.fixed_om_costs
        table[tech.Wind] = 1701 / af + fom[tech.Wind]
        table[tech.CentralReceiver] = 4203 / af + fom[tech.CentralReceiver]
        table[tech.ParabolicTrough] = 4563 / af + fom[tech.ParabolicTrough]


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
        fom[tech.PV1Axis] = 30 * self.escalation
        fom[tech.CentralReceiver] = 71.312 * self.escalation
        fom[tech.ParabolicTrough] = 72.381 * self.escalation
        vom = self.opcost_per_mwh
        vom[tech.Wind] = 10 * self.escalation
        vom[tech.CentralReceiver] = 5.65 * self.escalation
        vom[tech.ParabolicTrough] = 11.39 * self.escalation

        # Re-calculate annual capital costs for wind and CST.
        af = self.annuityf
        table = self.capcost_per_kw_per_yr
        fom = self.fixed_om_costs
        table[tech.Wind] = 1917 / af + fom[tech.Wind]
        table[tech.CentralReceiver] = 5253 / af + fom[tech.CentralReceiver]
        table[tech.ParabolicTrough] = 5659 / af + fom[tech.ParabolicTrough]


class AETA2013_2030Mid (AETA2012_2030):

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
        assert low.fixed_om_costs == high.fixed_om_costs

        table = self.capcost_per_kw_per_yr
        lowtable = low.capcost_per_kw_per_yr
        hightable = high.capcost_per_kw_per_yr
        for t in lowtable:
            # See comment in AETA2012_2030Mid.
            table[t] = lowtable[t] / 2 + hightable[t] / 2


def cost_switch(label):
    """
    Return a class for a given cost scenario.

    >>> cost_switch('AETA2013-in2030-low') # doctest: +ELLIPSIS
    <class costs.AETA2013_2030Low at 0x...>
    >>> cost_switch('foo')
    Traceback (most recent call last):
      ...
    ValueError: unknown cost scenario: foo
    """
    try:
        callback = cost_scenarios[label]
    except KeyError:
        print 'valid scenarios:'
        for k in sorted(cost_scenarios.keys()):
            print '\t', k
        raise ValueError('unknown cost scenario: %s' % label)
    return callback


cost_scenarios = {'null': NullCosts,
                  'AETA2012-in2030-low': AETA2012_2030Low,
                  'AETA2012-in2030-mid': AETA2012_2030Mid,
                  'AETA2012-in2030-high': AETA2012_2030High,
                  'AETA2013-in2030-low': AETA2013_2030Low,
                  'AETA2013-in2030-mid': AETA2013_2030Mid,
                  'AETA2013-in2030-high': AETA2013_2030Low}
