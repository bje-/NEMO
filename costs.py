# -*- Python -*-
# Copyright (C) 2012, 2013 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

import generators as tech

def annuity_factor (t, r):
    "Return the annuity factor for lifetime t and interest rate r."
    return (1 - (1 / pow (1 + r, t))) / r

####
# Data source: BREE AETA report (2012)
####

class AETA2030:
    lifetime = 30

    def __init__ (self, discount, coal_price, gas_price, ccs_price):
        self.discount_rate = discount
        self.ccs_storage_per_t = ccs_price
        self.coal_price_per_gj = coal_price
        self.gas_price_per_gj = gas_price
        self.capcost_per_kw_per_yr = {}
        self.opcost_per_mwh = {}
        self.fixed_om_costs = {}
        self.annuityf = annuity_factor (AETA2030.lifetime, discount)
        
        escalation = 1.171

        # Common capital costs
        table = self.capcost_per_kw_per_yr
        table[tech.Hydro] = 0
        table[tech.PumpedHydro] = 0
        table[tech.DemandResponse] = 0

        # Variable O&M (VOM) costs
        table = self.opcost_per_mwh
        table[tech.Hydro] = 0
        table[tech.PumpedHydro] = 0
        table[tech.Wind] = 12 * escalation
        table[tech.CST] = 20 * escalation
        table[tech.PV] = 0
        table[tech.Biofuel] = 10 * escalation + 80 # (fuel)
        table[tech.CCGT] = 4 * escalation
        table[tech.OCGT] = 10 * escalation
        table[tech.CCGT_CCS] = 9 * escalation
        table[tech.Coal_CCS] = 15 * escalation
        table[tech.Black_Coal] = 7 * escalation
	table[tech.Geothermal] = 0 

        # Fixed O&M (FOM) costs
        table = self.fixed_om_costs
        table[tech.DemandResponse] = 0
        table[tech.Hydro] = 0
        table[tech.PumpedHydro] = 0
        table[tech.Wind] = 40 * escalation
        table[tech.CST] = 65 * escalation
        table[tech.PV] = 25 * escalation
        table[tech.Biofuel] = 4 * escalation
        table[tech.CCGT] = 10 * escalation
        table[tech.OCGT] = 4 * escalation
        table[tech.CCGT_CCS] = 17 * escalation
        table[tech.Coal_CCS] = 73.2 * escalation
        table[tech.Black_Coal] = 50.5 * escalation
	table[tech.Geothermal] = 200 * escalation

class AETA2030Low (AETA2030):
    def __init__ (self, discount, coal_price, gas_price, ccs_storage_costs):
        AETA2030.__init__ (self, discount, coal_price, gas_price, ccs_storage_costs)
        af = self.annuityf
        # capital costs in $/kW
        table = self.capcost_per_kw_per_yr
        fom = self.fixed_om_costs
        table[tech.Wind] = 1701 / af + fom[tech.Wind]
        table[tech.CST] = 4563 / af + fom[tech.CST]
        table[tech.PV] = 1482 / af + fom[tech.PV]
        table[tech.Biofuel] = 694 / af + fom[tech.Biofuel]
        table[tech.CCGT] = 1015 / af + fom[tech.CCGT]
        table[tech.OCGT] = 694 / af + fom[tech.OCGT]
        table[tech.CCGT_CCS] = 2095 / af + fom[tech.CCGT_CCS]
        table[tech.Coal_CCS] = 4453 / af + fom[tech.Coal_CCS]
        table[tech.Black_Coal] = 2947 / af + fom[tech.Black_Coal]
	table[tech.Geothermal] = 6645 / af + fom[tech.Geothermal]

class AETA2030High (AETA2030):
    def __init__ (self, discount, coal_price, gas_price, ccs_storage_costs):
        AETA2030.__init__ (self, discount, coal_price, gas_price, ccs_storage_costs)
        af = self.annuityf
        # capital costs in $/kW
        table = self.capcost_per_kw_per_yr
        fom = self.fixed_om_costs
        table[tech.Wind] = 1917 / af + fom[tech.Wind]
        table[tech.CST] = 5659 / af + fom[tech.CST]
        table[tech.PV] = 1871 / af + fom[tech.PV]
        table[tech.Biofuel] = 809 / af + fom[tech.Biofuel]
        table[tech.CCGT] = 1221 / af + fom[tech.CCGT]
        table[tech.OCGT] = 809 / af + fom[tech.OCGT]
        table[tech.CCGT_CCS] = 2405 / af + fom[tech.CCGT_CCS]
        table[tech.Coal_CCS] = 4727 / af + fom[tech.Coal_CCS]
        table[tech.Black_Coal] = 3128 / af + fom[tech.Black_Coal]
	table[tech.Geothermal] = 7822 / af + fom[tech.Geothermal] 
