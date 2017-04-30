# Copyright (C) 2017 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""The simulation engine."""

import numpy as np
import polygons
import regions


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


def run(context, starthour=0, endhour=None):
    """Run the simulation (without a plot).

    >>> from nem import Context
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
