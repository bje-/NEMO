# Copyright (C) 2024 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Costs common to all cost classes."""

from nemo import generators as tech


class Common:
    """Costs common to all cost classes (eg, existing hydro)."""

    def __init__(self, discount):
        """Initialise common costs.

        Derived costs can call update() on these dicts.
        """
        self.discount_rate = discount

        # bioenergy costs taken from CSIRO energy storage report for AEMO
        self.bioenergy_price_per_gj = 12
        self.diesel_price_per_litre = 1.50

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
