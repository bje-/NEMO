# Copyright (C) 2014 The University of New South Wales
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Configuration file processing (eg, filenames)."""

import ConfigParser

config = ConfigParser.ConfigParser()
config.read('default.cfg')

cst_data = config.get('generation', 'cst-trace')
wind_data = config.get('generation', 'wind-trace')
pv1axis_data = config.get('generation', 'pv1axis-trace')
demand_data = config.get('demand', 'demand-trace')
