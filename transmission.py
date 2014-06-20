# -*- Python -*-
# Copyright (C) 2011, 2012 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

import regions
from costs import annuity_factor


class Transmission:
    def __init__(self, cost_per_mw_km, discount, lifetime=50):
        af = annuity_factor(lifetime, discount)
        self.cost_matrix = regions.distances * cost_per_mw_km / af
