# Copyright (C) 2011, 2012 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Transmission model details."""
import numpy as np
from nemo.polygons import distances
from nemo.costs import annuity_factor


class Transmission():

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
        >>> caps = np.empty_like(distances[1:, 1:])
        >>> caps.fill(100)
        >>> costmat = t.cost_matrix(caps)
        >>> from nemo import polygons
        >>> d = polygons.dist(1, 2)
        >>> expected_value = (800 * 100 * d) / t.af
        >>> assert int(costmat[0, 1]) == int(expected_value)
        >>> costmat.min()
        0.0
        >>> costmat.max().round()
        15143974.0
        """
        return self.cost_per_mw_km(capacities) * capacities * distances[1:, 1:] / self.af
