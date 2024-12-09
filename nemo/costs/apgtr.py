# Copyright (C) 2024 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Australian Power Generation Technology Report costs."""

from nemo import generators as tech

from .common import Common


class APGTR2015(Common):
    """Australian Power Generation Technology Report costs in 2015.

    Source: CO2CRC Australian Power Generation Technology Report (2015)
    """

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        Common.__init__(self, discount)
        self.ccs_storage_per_t = ccs_price
        self.coal_price_per_gj = coal_price
        self.gas_price_per_gj = gas_price

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
