# Copyright (C) 2011, 2012, 2014 Ben Elliston
# Copyright (C) 2014 The University of New South Wales
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""A National Electricity Market (NEM) simulation."""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.patches import Patch

import consts
import regions
import generators
import siteinfo

hours = 8760

# Demand is in 30 minute intervals. NOTE: the number of rows in the
# demand file now dictates the number of timesteps in the simulation.
demand = np.genfromtxt(siteinfo.demand_data, comments='#')
demand = demand.transpose()

# There must be 12 columns: date, time and ten demand/price columns (for 5 regions).
assert demand.shape[0] == 12

# The number of rows must be even.
assert demand.shape[1] % 2 == 0, "odd number of rows in half-hourly demand data"

# For hourly demand, average half-hours n and n+1.
# Demand is in every second column from columns 2 onwards.
regional_demand = (demand[2::2, ::2] + demand[2::2, 1::2]) / 2
assert regional_demand.shape[0] == 5


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
        # NEM standard: 0.002% unserved energy
        self.relstd = 0.002
        self.generators = default_generation_mix()
        self.demand = regional_demand.copy()
        self.timesteps = self.demand.shape[1]
        self.unserved = []
        self.unserved_energy = 0
        self.unserved_hours = 0
        self.unserved_percent = 0
        # System non-synchronous penetration limit
        self.nsp_limit = 1.0
        self.exchanges = np.zeros((hours, regions.numregions, regions.numregions))

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
        s += 'Demand energy: %.1f TWh\n' % (self.demand.sum() / consts.twh)
        s += 'Spilled energy: %.1f TWh\n' % (self.spill.sum() / consts.twh)

        if self.unserved_energy == 0:
            s += 'No unserved energy'
        elif self.unserved_energy > 0:
            s += 'Unserved energy: %.3f%%' % self.unserved_percent + '\n'
            if self.unserved_percent > self.relstd:
                s += 'WARNING: NEM reliability standard exceeded\n'
            s += 'Unserved total hours: ' + str(self.unserved_hours) + '\n'
            s += 'min, max shortfalls: ' + str(self.shortfalls)

        if self.spill.sum() > 0:
            s += '\n' + 'spilled hours = ' + str((self.spill.sum(axis=0) > 0).sum())
        return s


def _sim(context, starthour, endhour):
    # reset generator internal state
    for g in context.generators:
        g.reset()

    context.exchanges.fill(0)
    context.generation = np.zeros((len(context.generators), hours))
    context.spill = np.zeros((len(context.generators), hours))

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

    assert context.demand.shape == (5, context.timesteps)
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
            if not gen:
                continue

            if g.non_synchronous_p:
                async_demand -= gen
                assert async_demand > -0.1
                async_demand = max(0, async_demand)

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


def plot(context, spills=False, filename=None, xlimit=None):
    """Produce a pretty plot of supply and demand."""
    spill = context.spill
    # aggregate demand
    demand = context.demand.sum(axis=0)

    fig = plt.figure()
    plt.ylabel('MW')
    plt.xlabel('Hour')
    title = 'NEM supply/demand for 2010\nRegions: %s' % str(context.regions)
    plt.suptitle(title)
    plt.xlim(0, context.timesteps)
    ymax = (spill.max() + demand.max()) * 1.05 if spills else demand.max() * 1.05
    plt.ylim(0, ymax)

    if xlimit is not None:
        plt.xlim(xlimit)

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

    f = plt.figlegend([Patch('black', 'red')] +
                      [g.patch for g in gen_list],
                      ['unserved'] + [g.label + ' (%.1f GW)' % (g.capacity / 1000) for g in gen_list],
                      'upper right')
    plt.setp(f.get_texts(), fontsize='small')

    ax = fig.add_subplot(111)
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(_format_date))
    fig.autofmt_xdate()

    # Plot demand first.
    xdata = np.arange(context.timesteps)
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

    for h in np.argwhere(context.unserved):
        plt.plot([h[0]], [ymax], "yv", markersize=15, color='red')

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
    return context


def _format_date(x, pos=None):
    """Pretty printer for dates/times.

    >>> _format_date(0)
    'Jan 01 00h'
    """
    # pylint: disable=unused-argument
    import datetime
    delta = datetime.timedelta(hours=x)
    t = datetime.datetime(2010, 1, 1) + delta
    return t.strftime('%b %d %Hh')
