# Copyright (C) 2011, 2012 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Transmission model details."""
import numpy as np
from polygons import distances
from costs import annuity_factor


class Transmission:

    """An encapsulating class for transmission specific bits."""

    def __init__(self, costfn, discount, lifetime=50):
        """Construct transmission costs given a cost function, discount rate and lifetime.

        >>> t = Transmission(0.05, 30)
        """
        # Vectorise the cost function so that we can call it with a matrix argument.
        self.cost_per_mw_km = np.vectorize(costfn)
        self.af = annuity_factor(lifetime, discount)

    def cost_matrix(self, capacities):
        """Return the cost matrix given a capacity matrix.

        >>> t = Transmission(lambda x: 800, 0.05, 30)
        >>> caps = np.empty_like(distances)
        >>> caps.fill(100)
        >>> costmat = t.cost_matrix(caps)
        >>> costmat[1:, 1:].min()
        0.0
        >>> costmat[1:, 1:].max().round()
        15143974.0
        """
        return self.cost_per_mw_km(capacities) * capacities * distances / self.af
