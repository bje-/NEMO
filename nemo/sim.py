# Copyright (C) 2017, 2019 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""The core of the simulation engine."""

from math import isclose

import numpy as np
import pandas as pd

from nemo import regions


def _sim(context, date_range):
    # reset generator internal state
    for gen in context.generators:
        gen.reset()

    generation = np.zeros((len(date_range), len(context.generators)))
    spill = np.zeros((len(date_range), len(context.generators)))

    # Extract generators in the regions of interest.
    gens = [g for g in context.generators if g.region() in context.regions]

    # Zero out polygon demands we don't care about.
    for rgn in [r for r in regions.All if r not in context.regions]:
        for poly in rgn.polygons:
            context.demand[poly - 1] = 0

    # We are free to scribble all over demand_copy. Use ndarray for speed.
    demand_copy = context.demand.copy().values
    residual_demand = demand_copy.sum(axis=1)

    for hour, date in enumerate(date_range):
        hour_demand = demand_copy[hour]
        residual_hour_demand = residual_demand[hour]

        if context.verbose:
            print('STEP:', date)
            print('DEMAND:', {a: round(b, 2) for a, b in
                              enumerate(hour_demand)})

        _dispatch(context, hour, residual_hour_demand, gens, generation, spill)

        if context.verbose:
            print('ENDSTEP:', date)

    # Change the numpy arrays to dataframes for human consumption
    context.generation = pd.DataFrame(index=date_range, data=generation)
    context.spill = pd.DataFrame(index=date_range, data=spill)


def _store_spills(context, hour, gen, generators, spl):
    """Store spills from a generator into any storage."""
    assert spl > 0, f'{spl} is <= 0'
    for other in list(g for g in generators if g.storage_p):
        stored = other.store(hour, spl)
        spl -= stored
        if spl < 0 and isclose(spl, 0, abs_tol=1e-6):
            spl = 0
        assert spl >= 0

        # energy stored <= energy transferred, according to store's RTE
        if context.verbose:
            # show the energy transferred, not stored
            print('STORE:', gen, '->', other, f'({stored:.1f})')

        if spl == 0:
            # early exit
            break
    return spl


def _dispatch(context, hour, residual_hour_demand, gens, generation, spill):
    """Dispatch power from each generator in merit (list) order."""
    # async_demand is the maximum amount of the demand in this
    # hour that can be met from non-synchronous
    # generation. Non-synchronous generation in excess of this
    # value must be spilled.
    async_demand = residual_hour_demand * context.nsp_limit

    for gidx, generator in enumerate(gens):
        if not generator.synchronous_p and async_demand < residual_hour_demand:
            gen, spl = generator.step(hour, async_demand)
        else:
            gen, spl = generator.step(hour, residual_hour_demand)
        assert gen < residual_hour_demand or \
            isclose(gen, residual_hour_demand), \
            f"generation ({gen:.4f}) > demand " + \
            f"({residual_hour_demand:.4f}) for {generator}"
        generation[hour, gidx] = gen

        if not generator.synchronous_p:
            async_demand -= gen
            assert async_demand > 0 or isclose(async_demand, 0, abs_tol=1e-6)
            async_demand = max(0, async_demand)

        residual_hour_demand -= gen
        assert residual_hour_demand > 0 or \
            isclose(residual_hour_demand, 0, abs_tol=1e-6)
        residual_hour_demand = max(0, residual_hour_demand)

        if context.verbose:
            print(f'GENERATOR: {generator},',
                  f'generation: {gen:.1f}',
                  f'spill: {spl:.1f}',
                  f'residual-demand: {residual_hour_demand:.1f}',
                  f'async-demand: {async_demand:.1f}')

        if spl > 0:
            spill[hour, gidx] = \
                _store_spills(context, hour, generator, gens, spl)


def run(context, starthour=None, endhour=None):
    """Run the simulation."""
    if not isinstance(context.regions, list):
        raise TypeError

    if starthour is None:
        starthour = context.demand.index.min()
    if endhour is None:
        endhour = context.demand.index.max()
    date_range = pd.date_range(starthour, endhour, freq='H')

    _sim(context, date_range)

    # Calculate unserved energy.
    agg_demand = context.demand.sum(axis=1)
    agg_generation = context.generation.sum(axis=1)
    unserved = agg_demand - agg_generation
    # Ignore unserved events very close to 0 (rounding errors)
    context.unserved = unserved[~np.isclose(unserved, 0)]
