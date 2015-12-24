# Copyright (C) 2011, 2012 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Transmission model details."""
import polygons
from costs import annuity_factor


class Transmission:

    """An encapsulating class for transmission specific bits."""

    def __init__(self, cost_per_mw_km, discount, lifetime=50):
        """Construct transmission costs given cost per MW/km, discount rate and lifetime.

        >>> t = Transmission(30, 0.05)
        """
        af = annuity_factor(lifetime, discount)
        self.cost_matrix = polygons.distances * cost_per_mw_km / af
