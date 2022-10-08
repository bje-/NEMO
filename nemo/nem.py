# Copyright (C) 2011, 2012, 2014 Ben Elliston
# Copyright (C) 2014, 2015, 2016 The University of New South Wales
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""A National Electricity Market (NEM) simulation."""

import io

import numpy as np
import pandas as pd
import requests

from nemo import configfile, polygons, regions

# Demand is in 30 minute intervals. NOTE: the number of rows in the
# demand file now dictates the number of timesteps in the simulation.

url = configfile.get('demand', 'demand-trace')

if not url.startswith('http'):
    # Local file path
    traceinput = url
else:
    try:
        resp = requests.request('GET', url, timeout=5)
    except requests.exceptions.Timeout as exc:
        raise TimeoutError(f'timeout fetching {url}') from exc
    if not resp.ok:
        raise ConnectionError(f'HTTP {resp.status_code}: {url}')
    traceinput = io.StringIO(resp.text)

demand = pd.read_csv(traceinput, comment='#', sep=',',
                     parse_dates=[['Date', 'Time']], index_col='Date_Time')

# Check for date, time and n demand columns (for n regions).
assert len(demand.columns) == regions.NUMREGIONS
# The number of rows must be even.
assert len(demand) % 2 == 0, "odd number of rows in half-hourly demand data"

# Check demand data starts at midnight
startdate = demand.index[0]
assert (startdate.hour, startdate.minute, startdate.second) == (0, 30, 0), \
    'demand data must start at midnight'

# Calculate hourly demand, averaging half-hours n and n+1.
hourly_regional_demand = demand.resample('H', closed='right').mean()

# Now put the demand into polygon resolution according to the load
# apportioning figures given in each region's polygons field.
numsteps = len(hourly_regional_demand)
hourly_demand = pd.DataFrame(index=hourly_regional_demand.index,
                             data=np.zeros((numsteps, polygons.NUMPOLYGONS)))

for rgn, weights in [(r.id, r.polygons) for r in regions.All]:
    for polygon, share in weights.items():
        hourly_demand[polygon - 1] = hourly_regional_demand[rgn] * share
