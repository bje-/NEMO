# Copyright (C) 2011, 2012, 2014 Ben Elliston
# Copyright (C) 2014 The University of New South Wales
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""A National Electricity Market (NEM) simulation."""
import re

import datetime as dt
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

import configfile
import consts
import generators
import regions

# Demand is in 30 minute intervals. NOTE: the number of rows in the
# demand file now dictates the number of timesteps in the simulation.

# Generate a list of column numbers from [2, 4, .., 2*n]
# (ignore RRP columns)
columns = [(elt * 2) + 2 for elt in range(regions.numregions)]
cols = (0, 1) + tuple(columns)
demand = np.genfromtxt(configfile.get('demand', 'demand-trace'), comments='#', usecols=cols)
demand = demand.transpose()

# Check for date, time and n demand columns (for n regions).
assert demand.shape[0] == 2 + regions.numregions, demand.shape[0]
# The number of rows must be even.
assert demand.shape[1] % 2 == 0, "odd number of rows in half-hourly demand data"

# Find the start date of the demand data.
f = open(configfile.get('demand', 'demand-trace'))
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
# Demand is in every second column from columns 2 onwards.
hourly_demand = (demand[2::, ::2] + demand[2::, 1::2]) / 2
assert hourly_demand.shape[0] == regions.numregions


def default_generation_mix():
    """Return a default generator list.

    >>> g = default_generation_mix()
    >>> len(g)
    2
    """
    return [generators.CCGT(regions.nsw, 20000),
            generators.OCGT(regions.nsw, 20000)]


# Context objects are used throughout this module.
class Context:

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
        # NEM standard: 0.002% unserved energy
        self.relstd = 0.002
        self.generators = default_generation_mix()
        self.demand = hourly_demand.copy()
        self.timesteps = self.demand.shape[1]
        self.unserved = []
        self.unserved_energy = 0
        self.unserved_hours = 0
        self.unserved_percent = 0
        # System non-synchronous penetration limit
        self.nsp_limit = consts.nsp_limit
        self.exchanges = np.zeros((self.hours, regions.numregions, regions.numregions))

    def __str__(self):
        """A human-readable representation of the context.

        >>> import costs
        >>> import types
        >>> def foo(self, costs): return None
        >>> c = Context()
        >>> c.costs = costs.NullCosts()
        >>> c.verbose=1
        >>> f = types.MethodType(foo, c.generators[-1], Context)
        >>> c.generators[-1].summary = f
        >>> c.generators[-1].summary(None) is None
        True
        """
        s = ""
        if self.regions != regions.All:
            s += 'Regions: ' + str(self.regions) + '\n'
        if self.verbose:
            s += 'Generators:' + '\n'
            for g in self.generators:
                s += '\t' + str(g)
                if g.summary(self.costs) is not None:
                    s += '\n\t   ' + g.summary(self.costs) + '\n'
                else:
                    s += '\n'
        s += 'Timesteps: %d h\n' % self.hours
        s += 'Demand energy: %.1f TWh\n' % (self.demand.sum() / consts.twh)
        try:
            s += 'Spilled energy: %.1f TWh\n' % (self.spill.sum() / consts.twh)
            if self.spill.sum() > 0:
                s += 'Spilled hours: %d\n' % (self.spill.sum(axis=0) > 0).sum()
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
            s += 'min, max shortfalls: ' + str(self.shortfalls)
        return s


def _sim(context, starthour, endhour):
    # reset generator internal state
    for g in context.generators:
        g.reset()

    context.exchanges.fill(0)
    context.generation = np.zeros((len(context.generators), context.hours))
    context.lowest_merit_generator = np.zeros(context.hours, dtype=object)
    context.spill = np.zeros((len(context.generators), context.hours))

    # Extract generators in the regions of interest.
    gens = [g for g in context.generators if g.region in context.regions]
    # And storage-capable generators.
    storages = [g for g in gens if g.storage_p]

    connections = {}
    c = regions.connections
    for r in context.regions:
        connections[r] = []
        for (src, dest), path in zip(c.keys(), c.values()):
            if src is r and dest in context.regions and regions.in_regions_p(path, context.regions):
                connections[r].append(path)
        connections[r].sort()
        connections[r].sort(key=len)

    assert context.demand.shape == (regions.numregions, context.timesteps)
    demand_copy = context.demand.copy()

    # Zero out regions we don't care about.
    for rgn in [r for r in regions.All if r not in context.regions]:
        demand_copy[rgn] = 0

    for hr in xrange(starthour, endhour):
        hour_demand = demand_copy[::, hr]
        residual_hour_demand = hour_demand.sum()
        async_demand = residual_hour_demand * context.nsp_limit

        if context.verbose:
            print 'hour', hr, 'demand:', hour_demand

        # Dispatch power from each generator in merit order
        for gidx, g in enumerate(gens):
            if g.non_synchronous_p and async_demand < residual_hour_demand:
                gen, spl = g.step(hr, async_demand)
            else:
                gen, spl = g.step(hr, residual_hour_demand)
            assert gen <= residual_hour_demand, \
                "generation (%.2f) > demand (%.2f) for %s" % (gen, residual_hour_demand, g)
            context.generation[gidx, hr] = gen
            if gen == 0:
                continue

            if g.non_synchronous_p:
                async_demand -= gen
                assert async_demand > -0.1
                async_demand = max(0, async_demand)

            # This assumes a generator's opcosts are the same year
            # round, but OK for now.
            context.lowest_merit_generator[hr] = g

            residual_hour_demand -= gen
            # residual can go below zero due to rounding
            assert residual_hour_demand > -0.1
            residual_hour_demand = max(0, residual_hour_demand)

            if context.verbose:
                print 'GENERATOR:', g, 'generation =', context.generation[gidx, hr], 'spill =', \
                    spl, 'residual demand =', residual_hour_demand, 'async demand =', async_demand

            # distribute the generation across the regions (local region first)

            if context.track_exchanges:
                paths = connections[g.region]
                if context.verbose:
                    print 'PATHS:', paths
                for path in paths:
                    if not gen:
                        break

                    rgn = g.region if len(path) is 0 else path[-1][-1]
                    rgnidx = rgn.num
                    transfer = gen if gen < hour_demand[rgnidx] else hour_demand[rgnidx]

                    if transfer > 0:
                        if context.verbose:
                            print 'dispatch', int(transfer), 'to', rgn
                        if rgn is g.region:
                            context.exchanges[hr, rgnidx, rgnidx] += transfer
                        else:
                            # dispatch to another region
                            for src, dest in path:
                                context.exchanges[hr, src, dest] += transfer
                                if context.verbose:
                                    print src, '->', dest, '(%d)' % transfer
                                    assert regions.direct_p(src, dest)
                        hour_demand[rgnidx] -= transfer
                        gen -= transfer

            if spl > 0:
                for other in storages:
                    stored = other.store(hr, spl)
                    spl -= stored
                    assert spl >= 0

                    # show the energy transferred, not stored (this is where the loss is handled)
                    if context.verbose:
                        print 'STORE:', g.region, '->', other.region, '(%.1f)' % stored
                    for src, dest in regions.path(g.region, other.region):
                        context.exchanges[hr, src, dest] += stored
            context.spill[gidx, hr] = spl

        if context.verbose:
            if (hour_demand > 0).any():
                print 'hour', hr, 'residual:', hour_demand
    return context


def _generator_list(context):
    """Return a list of the generators of interest in this run."""
    return [g for g in context.generators if g.region in context.regions and g.capacity > 0]


def plot(context, spills=False, filename=None):
    """Produce a pretty plot of supply and demand."""
    spill = context.spill
    # aggregate demand
    demand = context.demand.sum(axis=0)

    plt.ylabel('Power (MW)')
    title = 'NEM supply/demand\nRegions: %s' % context.regions
    plt.suptitle(title)

    # The ::-1 slicing reverses the 'gens' list so that the legend
    # appears in "merit order".
    gen_list = _generator_list(context)[::-1]

    if len(gen_list) > 25:
        unique = []
        keep = []
        for g in gen_list:
            if g.__class__ not in unique:
                unique.append(g.__class__)
                # Replace the generator label with its class type.
                g.label = str(g.__class__).strip('<>').split()[0].split('.')[1]
                keep.append(g)
        gen_list = keep

    legend = plt.figlegend([Patch('black', 'red')] +
                           [g.patch for g in gen_list],
                           ['unserved'] + [g.label + ' (%.1f GW)' % (g.capacity / 1000) for g in gen_list],
                           'upper right')
    plt.setp(legend.get_texts(), fontsize='small')
    xdata = mdates.drange(context.startdate,
                          context.startdate + dt.timedelta(hours=context.hours),
                          dt.timedelta(hours=1))

    # Plot demand first.
    plt.plot(xdata, demand, color='black', linewidth=2)
    if spills:
        peakdemand = np.empty_like(demand)
        peakdemand.fill(demand.max())
        plt.plot(xdata, peakdemand, color='black', linestyle='dashed')

    accum = np.zeros(context.timesteps)
    prev = accum.copy()
    for g in _generator_list(context):
        idx = context.generators.index(g)
        accum += context.generation[idx]
        # Ensure total generation does not exceed demand in any timestep.
        assert(np.round(accum, 6) > np.round(demand, 6)).sum() == 0
        plt.plot(xdata, accum, color='black', linewidth=0.5)
        plt.fill_between(xdata, prev, accum, facecolor=g.patch.get_fc())
        prev = accum.copy()
    # Unmet demand is shaded red.
    plt.fill_between(xdata, accum, demand, facecolor='red')

    if spills:
        prev = demand.copy()
        for g in [g for g in context.generators if g.region in context.regions]:
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
        plt.plot([xvalue], [ymax - 200], "yv", markersize=15, color='red')

    if not filename:
        plt.show()  # pragma: no cover
    else:
        plt.savefig(filename)


def run(context, starthour=0, endhour=None):
    """Run the simulation (without a plot).

    >>> c = Context()
    >>> c.regions = (1,2)
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
    context.unserved_percent = float(context.unserved_energy / agg_demand.sum()) * 100

    shortfall = [agg_demand[hr] - context.accum[hr]
                 for hr in np.argwhere(context.unserved)]
    if len(shortfall) == 0:
        context.shortfalls = (None, None)
    else:
        context.shortfalls = (round(min(shortfall)), round(max(shortfall)))


def bids(context):
    """Show the bids for each time step."""
    return [g.opcost_per_mwh(context.costs) for g in
            context.lowest_merit_generator]


def revenue(context):
    """Total the revenue."""
    hourly_generation = context.generation.sum(axis=0)
    pairs = zip(hourly_generation, bids(context))
    result = reduce(lambda a, b: a + b, [g * b for g, b in pairs])
    return int(result)
