# Copyright (C) 2024 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""CSIRO GenCost common costs across all annual reports."""

from nemo import generators as tech

from .common import Common


class GenCost(Common):
    """Costs from the CSIRO GenCost series of reports.

    Source:
    https://data.csiro.au/collections/collection/CIcsiro:44228
    """

    def __init__(self, discount, coal_price, gas_price, ccs_price):
        """Construct a cost object."""
        Common.__init__(self, discount)
        self.ccs_storage_per_t = ccs_price
        self.coal_price_per_gj = coal_price
        self.gas_price_per_gj = gas_price

        # Fixed O&M (FOM) costs
        # Note: These are the same for all years (2030, 2040, 2050),
        # so we can set them once here.
        self.fixed_om_costs.update({
            tech.Black_Coal: 53.2,
            tech.CCGT: 10.9,
            tech.CCGT_CCS: 16.4,
            tech.CentralReceiver: None,  # varies across years
            tech.Coal_CCS: 77.8,
            tech.OCGT: 10.2,
            tech.Behind_Meter_PV: 0,
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
            tech.OCGT: None,  # varies across years
            tech.Behind_Meter_PV: 0,
            tech.PV1Axis: 0,
            tech.Wind: 0})

        # Storage is expressed on a total cost basis (GenCost 2024, Sec. 2.8)
        # Figures are entered in the classes in $/kWh, but these are
        # converted to $/kW in capcost().
        self.totcost_per_kwh = {}
