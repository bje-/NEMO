# Copyright (C) 2011, 2012, 2014 Ben Elliston
# Copyright (C) 2014, 2015, 2016 The University of New South Wales
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""A National Electricity Market (NEM) simulation."""
import re

import datetime as dt
import json
from itertools import groupby
import numpy as np
import urllib2

import configfile
import consts
import generators
import regions
import polygons
from sim import run

# Demand is in 30 minute intervals. NOTE: the number of rows in the
# demand file now dictates the number of timesteps in the simulation.

# Generate a list of column numbers
cols = tuple(range(regions.numregions + 2))
urlobj = urllib2.urlopen(configfile.get('demand', 'demand-trace'))
demand = np.genfromtxt(urlobj, comments='#', usecols=cols)
demand = demand.transpose()

# Check for date, time and n demand columns (for n regions).
assert demand.shape[0] == 2 + regions.numregions, demand.shape[0]
# The number of rows must be even.
assert demand.shape[1] % 2 == 0, "odd number of rows in half-hourly demand data"

# Find the start date of the demand data.
f = urllib2.urlopen(configfile.get('demand', 'demand-trace'))
for line in f:
    if re.search(r'^\s*#', line):
        continue
    cols = line.split()
    year, month, day = cols[0].split('/')
    startdate = dt.datetime(int(year), int(month), int(day))
    assert cols[1] == '00:30:00', 'demand data must start at midnight'
    break
f.close()

# For hourly demand, average half-hours n and n+1.
# Demand figures appear in column 2 onwards.
hourly_regional_demand = (demand[2::, ::2] + demand[2::, 1::2]) / 2
assert hourly_regional_demand.shape[0] == regions.numregions

# Now put the demand into polygon resolution according to the load
# apportioning figures given in each region's polygons field.
numsteps = hourly_regional_demand.shape[1]
hourly_demand = np.zeros((polygons.numpolygons, numsteps))
rgns = [r.polygons for r in regions.All]
for i, weights in enumerate(rgns):
    for polygon, share in zip(weights, weights.values()):
        hourly_demand[polygon - 1] = hourly_regional_demand[i] * share


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
        self.hours = demand.shape[1] / 2
        # Estimate the number of years from the number of simulation hours.
        if self.hours == 8760 or self.hours == 8784:
            self.years = 1
        else:
            self.years = self.hours / (365.25 * 24)

        self.relstd = 0.002  # 0.002% unserved energy
        self.generators = [generators.CCGT(polygons.wildcard, 20000),
                           generators.OCGT(polygons.wildcard, 20000)]
        self.demand = hourly_demand.copy()
        self.timesteps = self.demand.shape[1]
        self.unserved = []
        self.unserved_energy = 0
        self.unserved_hours = 0
        self.unserved_percent = 0
        # System non-synchronous penetration limit
        self.nsp_limit = float(configfile.get('limits', 'nonsync-penetration'))
        self.exchanges = np.zeros((self.hours, polygons.numpolygons, polygons.numpolygons))

    def add_exchange(self, hour, src, dest, transfer):
        """Note energy transfer from SRC to DEST in HOUR."""
        self.exchanges[hour, src - 1, dest - 1] += transfer

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
        s += 'Demand energy: %.1f TWh\n' % (self.demand.sum() / consts.twh)
        try:
            s += 'Unused surplus energy: %.1f TWh\n' % (self.spill.sum() / consts.twh)
            if self.spill.sum() > 0:
                s += 'Timesteps with unused surplus energy: %d\n' % (self.spill.sum(axis=0) > 0).sum()
        except AttributeError:
            # there may be no 'spill' attribute yet
            pass

        if self.unserved_energy == 0:
            s += 'No unserved energy'
        elif self.unserved_energy > 0:
            s += 'Unserved energy: %.3f%%' % self.unserved_percent + '\n'
            if self.unserved_percent > self.relstd:
                s += 'WARNING: NEM reliability standard exceeded\n'
            s += 'Unserved total hours: ' + str(self.unserved_hours) + '\n'
            unserved_events = [g for g, _ in groupby(self.unserved, lambda x: bool(x) is True) if g]
            s += 'Number of unserved energy events: ' + str(len(unserved_events)) + '\n'
            s += 'min, max shortfalls: ' + str(self.shortfalls)
        return s

    class JSONEncoder(json.JSONEncoder):
        """A custom encoder for Context objects."""
        def default(self, obj):  # pylint: disable=E0202
            if isinstance(obj, Context):
                result = []
                for g in obj.generators:
                    tech = str(type(g)).split('.')[1]
                    result += [{'label': g.label, 'polygon': g.polygon,
                                'capacity': g.capacity, 'technology': tech}]
                return result
            else:
                # Let the base class default method raise any TypeError
                return json.JSONEncoder.default(self, obj)
