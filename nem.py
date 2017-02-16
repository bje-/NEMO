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
from matplotlib.patches import Patch
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import urllib2

import configfile
from configfile import ConfigParser
import consts
import generators
import regions
import polygons

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


def default_generation_mix():
    """Return a default generator list.

    >>> g = default_generation_mix()
    >>> len(g)
    2
    """
    return [generators.CCGT(polygons.wildcard, 20000),
            generators.OCGT(polygons.wildcard, 20000)]


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
        self.generators = default_generation_mix()
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


def _sim(context, starthour, endhour):
    # reset generator internal state
    for g in context.generators:
        g.reset()

    context.exchanges.fill(0)
    context.generation = np.zeros((len(context.generators), context.hours))
    context.spill = np.zeros((len(context.generators), context.hours))

    # Extract generators in the regions of interest.
    gens = [g for g in context.generators if g.region() in context.regions]
    # And storage-capable generators.
    storages = [g for g in gens if g.storage_p]

    if context.track_exchanges:
        for g in gens:
            # every generator must be in a polygon
            assert g.polygon is not None, 'every generator must be assigned a polygon'

        selected_polygons = []
        for r in context.regions:
            if r.polygons is not None:
                selected_polygons += r.polygons

        # pull out the polygons with non-zero load in each region
        loads = [k for r in context.regions for (k, v) in r.polygons.iteritems() if v > 0]
        connections = {}
        for poly in range(1, polygons.numpolygons + 1):
            # use a list comprehension to filter the connections down to bits of interest
            connections[poly] = [path for (src, dest), path in
                                 polygons.connections.iteritems() if src is poly and
                                 dest in loads and
                                 polygons.subset(path, selected_polygons)]
            connections[poly].sort(key=polygons.pathlen)

    assert context.demand.shape == (polygons.numpolygons, context.timesteps)

    # Zero out polygon demands we don't care about.
    for rgn in [r for r in regions.All if r not in context.regions]:
        for poly in rgn.polygons:
            context.demand[poly - 1] = 0

    # We are free to scribble all over demand_copy.
    demand_copy = context.demand.copy()

    for hr in xrange(starthour, endhour):
        hour_demand = demand_copy[::, hr]
        residual_hour_demand = hour_demand.sum()
        # async_demand is the maximum amount of the demand in this
        # hour that can be met from non-synchronous
        # generation. Non-synchronous generation in excess of this
        # value must be spilled.
        async_demand = residual_hour_demand * context.nsp_limit

        if context.verbose:
            print 'HOUR:', hr, 'demand', hour_demand

        # Dispatch power from each generator in merit order
        for gidx, g in enumerate(gens):
            if g.non_synchronous_p and async_demand < residual_hour_demand:
                gen, spl = g.step(hr, async_demand)
            else:
                gen, spl = g.step(hr, residual_hour_demand)
            assert gen <= residual_hour_demand, \
                "generation (%.2f) > demand (%.2f) for %s" % (gen, residual_hour_demand, g)
            context.generation[gidx, hr] = gen

            if g.non_synchronous_p:
                async_demand -= gen
                assert async_demand > -0.1
                async_demand = max(0, async_demand)

            residual_hour_demand -= gen
            # residual can go below zero due to rounding
            assert residual_hour_demand > -0.1
            residual_hour_demand = max(0, residual_hour_demand)

            if context.verbose:
                print 'GENERATOR: %s,' % g, 'generation: %.1f' % context.generation[gidx, hr], \
                    'spill: %.1f' % spl, 'residual-demand: %.1f' % residual_hour_demand, \
                    'async-demand: %.1f' % async_demand

            # distribute the generation across the regions (local region first)

            if context.track_exchanges:
                paths = connections[g.polygon]
                if context.verbose:
                    print 'PATHS:', paths
                for path in paths:
                    if not gen:
                        break

                    poly = g.polygon if len(path) is 0 else path[-1][-1]
                    polyidx = poly - 1
                    transfer = gen if gen < hour_demand[polyidx] else hour_demand[polyidx]

                    if transfer > 0:
                        if context.verbose:
                            print 'DISPATCH:', int(transfer), 'to polygon', poly
                        if poly is g.polygon:
                            context.add_exchange(hr, poly, poly, transfer)
                        else:
                            # dispatch to another region
                            for src, dest in path:
                                context.add_exchange(hr, src, dest, transfer)
                                if context.verbose:
                                    print 'FLOW: polygon', src, '-> polygon', dest, '(%d)' % transfer
                                    assert polygons.direct_p(src, dest)
                        hour_demand[polyidx] -= transfer
                        gen -= transfer

            if spl > 0:
                for other in storages:
                    stored = other.store(hr, spl)
                    spl -= stored
                    assert spl >= 0

                    # energy stored <= energy transferred, according to store's RTE
                    if context.verbose:
                        # show the energy transferred, not stored
                        print 'STORE:', g.polygon, '->', other.polygon, '(%.1f)' % stored
                    for src, dest in polygons.path(g.polygon, other.polygon):
                        context.add_exchange(hr, src, dest, stored)
            context.spill[gidx, hr] = spl

        if context.verbose:
            if (hour_demand > 0).any():
                print 'hour', hr, 'residual:', hour_demand
    return context


def _generator_list(context):
    """Return a list of the generators of interest in this run."""
    return [g for g in context.generators if g.region() in context.regions and g.capacity > 0]


def _legend(context):
    """Draw the legend."""

    # ::-1 slicing reverses the list so that the legend appears in "merit order".
    gens = _generator_list(context)[::-1]
    labels = []
    patches = []

    if len(gens) > 20:
        unique = []
        for g in gens:
            if type(g) not in unique:
                unique.append(type(g))
                # Replace the generator label with its class.
                genclass = str(type(g)).strip('<>').replace("'", "")
                labels.append(genclass.split()[1].split('.')[1])
                patches.append(g.patch)
    else:
        for g in gens:
            labels.append(g.label + ' (%.1f GW)' % (g.capacity / 1000.))
            patches.append(g.patch)

    legend = plt.figlegend([Patch('black', 'red')] + patches,
                           ['unserved'] + labels,
                           'upper right')
    plt.setp(legend.get_texts(), fontsize='small')


def plot(context, spills=False, filename=None, showlegend=True):
    """Produce a pretty plot of supply and demand."""
    spill = context.spill
    # aggregate demand
    demand = context.demand.sum(axis=0)

    plt.ylabel('Power (MW)')
    try:
        title = configfile.get('plot', 'title')
    except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
        title = 'Supply/demand balance'
    try:
        subtitle = configfile.get('plot', 'subtitle')
        title += '\n' + subtitle
    except (configfile.ConfigParser.NoSectionError, configfile.ConfigParser.NoOptionError):
        pass
    plt.suptitle(title)

    if showlegend:
        _legend(context)
    xdata = mdates.drange(context.startdate,
                          context.startdate + dt.timedelta(hours=context.hours),
                          dt.timedelta(hours=1))

    # Plot demand first.
    plt.plot(xdata, demand, color='black', linewidth=3 if spills else 2)
    if spills:
        peakdemand = np.empty_like(demand)
        peakdemand.fill(demand.max())
        plt.plot(xdata, peakdemand, color='black', linestyle='dashed')

    accum = np.zeros(context.timesteps)
    prev = accum.copy()
    for g in _generator_list(context):
        idx = context.generators.index(g)
        accum += context.generation[idx]
        # Ensure accumulated generation does not exceed demand in any timestep.
        # (Due to rounding, accum can be close to demand.)
        assert np.all(np.logical_or(accum < demand, np.isclose(accum, demand)))
        plt.plot(xdata, accum, color='black', linewidth=0.5)
        plt.fill_between(xdata, prev, accum, facecolor=g.patch.get_fc(),
                         hatch=g.patch.get_hatch())
        prev = accum.copy()
    # Unmet demand is shaded red.
    plt.fill_between(xdata, accum, demand, facecolor='red')

    if spills:
        prev = demand.copy()
        for g in [g for g in context.generators if g.region() in context.regions]:
            idx = context.generators.index(g)
            accum += spill[idx]
            plt.plot(xdata, accum, color='black')
            plt.fill_between(xdata, prev, accum, facecolor=g.patch.get_fc(), alpha=0.3)
            prev = accum.copy()

    plt.gca().xaxis_date()
    plt.gcf().autofmt_xdate()

    for hr in np.argwhere(context.unserved):
        unserved_dt = context.startdate + dt.timedelta(hours=hr[0])
        xvalue = mdates.date2num(unserved_dt)
        _, ymax = plt.gca().get_ylim()
        plt.plot([xvalue], [ymax * 0.99], "yv", markersize=15, color='red')

    if not filename:
        plt.show()  # pragma: no cover
    else:
        plt.savefig(filename)


def run(context, starthour=0, endhour=None):
    """Run the simulation (without a plot).

    >>> c = Context()
    >>> c.regions = None
    >>> run(c)
    Traceback (most recent call last):
      ...
    ValueError: regions is not a list
    """
    if not isinstance(context.regions, list):
        raise ValueError('regions is not a list')

    if endhour is None:
        endhour = context.timesteps

    _sim(context, starthour, endhour)

    # Calculate some summary statistics.
    agg_demand = context.demand.sum(axis=0)
    context.accum = context.generation.sum(axis=0)
    context.unserved_energy = (agg_demand - context.accum).sum()
    context.unserved_energy = max(0, round(context.unserved_energy, 0))
    context.unserved = (agg_demand - context.accum) > 0.1
    context.unserved_hours = context.unserved.sum()
    total_demand = agg_demand.sum()
    if total_demand > 0:
        context.unserved_percent = context.unserved_energy / agg_demand.sum() * 100
    else:
        context.unserved_percent = 0.

    shortfall = [agg_demand[hr] - context.accum[hr]
                 for hr in np.argwhere(context.unserved)]
    if len(shortfall) == 0:
        context.shortfalls = (None, None)
    else:
        context.shortfalls = (round(min(shortfall)), round(max(shortfall)))
