# Copyright (C) 2024 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Collaboration on Energy and Environmental Markets (CEEM) costs."""

from nemo import generators as tech

from .aeta import AETA2012_2030Mid

# We use class names here that upset Pylint.
# pylint: disable=invalid-name


class CEEM2016_2030(AETA2012_2030Mid):
    """CEEM 2016 custom costs.

    These custom costs were produced by CEEM -- AETA (2013) mid costs
    with CO2CRC Power Generation Technology Report 2030 capital costs
    for utility-scale PV.
    """

    def __init__(self, discount, coal_price, gas_price, ccs_storage_costs):
        """Construct a cost object."""
        AETA2012_2030Mid.__init__(self, discount, coal_price, gas_price,
                                  ccs_storage_costs)

        # CO2CRC Power Generation Technology Report (p. 253) gives a
        # narrow range of $1,108 to $1,218 per kW. Meet half-way.
        self.capcost_per_kw[tech.PV1Axis] = 1255
