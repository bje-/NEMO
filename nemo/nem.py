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
        MSG = f'timeout fetching {url}'
        raise TimeoutError(MSG) from exc
    if not resp.ok:
        MSG = f'HTTP {resp.status_code}: {url}'
        raise ConnectionError(MSG)
    traceinput = io.StringIO(resp.text)

demand = pd.read_csv(traceinput, comment='#', sep=',')
# combine Date and Time columns into a new Date_Time column, make this
# the index column and then drop the original Date and Time columns
datetime_values = pd.to_datetime(demand['Date'] + ' ' + demand['Time'])
demand.insert(loc=0, column='Date_Time', value=datetime_values)
demand = demand.set_index('Date_Time')
demand = demand.drop(columns=['Date', 'Time'])

# Check for date, time and n demand columns (for n regions).
if len(demand.columns) != regions.NUMREGIONS:
    raise AssertionError

# The number of rows must be even.
MSG = "odd number of rows in half-hourly demand data"
if len(demand) % 2 != 0:
    raise AssertionError(MSG)

# Check demand data starts at midnight
startdate = demand.index[0]
MSG = 'demand data must start at midnight'
if (startdate.hour, startdate.minute, startdate.second) != (0, 30, 0):
    raise AssertionError(MSG)

# Calculate hourly demand, averaging half-hours n and n+1.
hourly_regional_demand = demand.resample('h', closed='right').mean()

# Now put the demand into polygon resolution according to the load
# apportioning figures given in each region's polygons field.
numsteps = len(hourly_regional_demand)
hourly_demand = pd.DataFrame(index=hourly_regional_demand.index,
                             data=np.zeros((numsteps, polygons.NUMPOLYGONS)))

for rgn, weights in [(r.id, r.polygons) for r in regions.All]:
    for polygon, share in weights.items():
        hourly_demand[polygon - 1] = hourly_regional_demand[rgn] * share
