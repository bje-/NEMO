# Copyright (C) 2011, 2012, 2014 Ben Elliston
# Copyright (C) 2014, 2015, 2016 The University of New South Wales
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""A National Electricity Market (NEM) simulation."""
import re

import json
import urllib2
import numpy as np
import pandas as pd

import configfile
import consts
import generators
import regions
import polygons
from sim import run

# Demand is in 30 minute intervals. NOTE: the number of rows in the
# demand file now dictates the number of timesteps in the simulation.

urlobj = urllib2.urlopen(configfile.get('demand', 'demand-trace'))
demand = pd.read_csv(urlobj, comment='#', sep=',',
                     parse_dates=[['Date', 'Time']], index_col='Date_Time')

# Check for date, time and n demand columns (for n regions).
assert len(demand.columns) == regions.numregions
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
                             data=np.zeros((numsteps, polygons.numpolygons)))

for rgn, weights in [(r.id, r.polygons) for r in regions.All]:
    for polygon, share in weights.iteritems():
        hourly_demand[polygon - 1] = hourly_regional_demand[rgn] * share


# Context objects are used throughout this module.
class Context(object):

    """All state is kept in a Context object."""

    def __init__(self):
        """Initialise a default context."""
        self.verbose = False
        self.track_exchanges = False
        self.regions = regions.All
        self.startdate = startdate
        # Number of timesteps is determined by the number of demand rows.
        self.hours = len(hourly_regional_demand)
        # Estimate the number of years from the number of simulation hours.
        if self.hours == 8760 or self.hours == 8784:
            self.years = 1
        else:
            self.years = self.hours / (365.25 * 24)

        self.relstd = 0.002  # 0.002% unserved energy
        self.generators = [generators.CCGT(polygons.wildcard, 20000),
                           generators.OCGT(polygons.wildcard, 20000)]
        self.demand = hourly_demand.copy()
        self.timesteps = len(self.demand)
        self.unserved = pd.DataFrame()
        # System non-synchronous penetration limit
        self.nsp_limit = float(configfile.get('limits', 'nonsync-penetration'))
        self.exchanges = np.zeros((self.hours, polygons.numpolygons, polygons.numpolygons))

    def total_demand(self):
        """Return the total demand from the data frame."""
        return self.demand.values.sum()

    def unserved_energy(self):
        """Return the total unserved energy."""
        return self.unserved.sum()

    def unserved_percent(self):
        """Return the total unserved energy as a percentage of total demand."""
        try:
            return self.unserved_energy() / self.total_demand() * 100
        except ZeroDivisionError:
            return np.nan

    def add_exchange(self, hour, src, dest, transfer):
        """Note energy transfer from SRC to DEST in HOUR."""
        self.exchanges[hour, src - 1, dest - 1] += transfer

    def set_capacities(self, caps):
        """Set generator capacities from a list."""
        n = 0
        for gen in self.generators:
            for (setter, min_cap, max_cap) in gen.setters:
                # keep parameters within bounds
                newval = max(min(caps[n], max_cap), min_cap)
                setter(newval)
                n += 1
        # Check every parameter has been set.
        assert n == len(caps), '%d != %d' % (n, len(caps))

    def __str__(self):
        """A human-readable representation of the context."""
        s = ""
        if self.regions != regions.All:
            s += 'Regions: ' + str(self.regions) + '\n'
        if self.verbose:
            s += 'Generators:' + '\n'
            for g in self.generators:
                s += '\t' + str(g)
                summary = g.summary(self)
                if summary is not None:
                    s += '\n\t   ' + summary + '\n'
                else:
                    s += '\n'
        s += 'Timesteps: %d h\n' % self.hours
        s += 'Demand energy: %.1f TWh\n' % (self.total_demand() / consts.twh)
        if hasattr(self, 'spill'):
            s += 'Unused surplus energy: %.1f TWh\n' % (self.spill.values.sum() / consts.twh)
            if self.spill.values.sum() > 0:
                spill_series = self.spill[self.spill.sum(axis=1) > 0]
                s += 'Timesteps with unused surplus energy: %d\n' % len(spill_series)

        if len(self.unserved) == 0:
            s += 'No unserved energy'
        else:
            s += 'Unserved energy: %.3f%%' % self.unserved_percent() + '\n'
            if self.unserved_percent() > self.relstd * 1.001:
                s += 'WARNING: reliability standard exceeded\n'
            s += 'Unserved total hours: ' + str(len(self.unserved)) + '\n'

            # A subtle trick: generate a date range and then substract
            # it from the timestamps of unserved events.  This will
            # produce a run of time detlas (for each consecutive hour,
            # the time delta between this timestamp and the
            # corresponding row from the range will be
            # constant). Group by the deltas.
            rng = pd.date_range(self.unserved.index[0], periods=len(self.unserved.index), freq='H')
            unserved_events = [k for k, g in self.unserved.groupby(self.unserved.index - rng)]
            s += 'Number of unserved energy events: ' + str(len(unserved_events)) + '\n'
            if len(self.unserved) > 0:
                shortfalls = round(self.unserved.min()), round(self.unserved.max())
                s += 'Shortfalls (min, max): ' + str(shortfalls)
        return s

    class JSONEncoder(json.JSONEncoder):
        """A custom encoder for Context objects."""
        def default(self, obj):  # pylint: disable=E0202
            if isinstance(obj, Context):
                result = []
                for g in obj.generators:
                    tech = re.sub(r"<class 'generators\.(.*)'>",
                                  r'\1', str(type(g)))
                    result += [{'label': g.label, 'polygon': g.polygon,
                                'capacity': g.capacity, 'technology': tech}]
                return result
