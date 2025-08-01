# Copyright (C) 2017, 2019 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""The core of the simulation engine."""

import logging
from math import isclose

import numpy as np
import pandas as pd

from nemo import regions

log = logging.getLogger(__name__)


def _sim(context, date_range):
    # pylint: disable=too-many-locals
    # reset generator internal state
    for gen in context.generators:
        gen.reset()

    # clear possible cached value
    context.storages = None
    log_enabled = log.isEnabledFor(logging.INFO)

    timesteps = len(date_range)
    generation = np.zeros((timesteps, len(context.generators)))
    spill = np.zeros((timesteps, len(context.generators)))

    # Extract generators in the regions of interest.
    gens = [generator for generator in context.generators if
            generator.region() in context.regions]

    # Zero out polygon demands we don't care about.
    for rgn in [region for region in regions.All if region not in
                context.regions]:
        for poly in rgn.polygons:
            context.demand[poly - 1] = 0

    # We are free to scribble all over demand_copy. Use ndarray for speed.
    demand_copy = context.demand.copy().to_numpy()
    residual_demand = demand_copy.sum(axis=1)

    for hour in range(timesteps):
        hour_demand = demand_copy[hour]
        residual_hour_demand = residual_demand[hour]

        # This avoids expensive argument evaluations
        if log_enabled:
            log.info('STEP: %s', date_range[hour])
            demand = {a: float(round(b, 2)) for
                      a, b in enumerate(hour_demand)}
            log.info('DEMAND: %s', demand)

        _dispatch(context, hour, residual_hour_demand, gens, generation, spill)

        if log_enabled:
            log.info('ENDSTEP: %s', date_range[hour])

    # Change the numpy arrays to dataframes for human consumption
    context.generation = pd.DataFrame(index=date_range, data=generation)
    context.spill = pd.DataFrame(index=date_range, data=spill)


def _store_spills(context, hour, source_generator, generators, spill):
    """Store spills from a generator into any storage."""
    log_enabled = log.isEnabledFor(logging.INFO)

    if spill <= 0:
        msg = f'{spill} is <= 0'
        raise AssertionError(msg)
    if context.storages is None:
        # compute this just once and cache it in the context object
        context.storages = [generator for generator in generators if
                            generator.storage_p]
    for storage_generator in context.storages:
        stored_energy = storage_generator.store(hour, spill)
        spill -= stored_energy
        if spill < 0:
            if isclose(spill, 0, abs_tol=1e-6):
                spill = 0
            else:
                raise AssertionError(spill)

        # energy stored <= energy transferred, according to store's RTE
        if log_enabled:
            log.info('STORE: %s -> %s (%.1f)', source_generator,
                     storage_generator, stored_energy)

        if spill == 0:
            # early exit
            break
    return spill


def _dispatch(context, hour, residual_hour_demand, gens, generation, spill):
    """Dispatch power from each generator in merit (list) order."""
    # async_demand is the maximum amount of the demand in this
    # hour that can be met from non-synchronous
    # generation. Non-synchronous generation in excess of this
    # value must be spilled.
    async_demand = residual_hour_demand * context.nsp_limit
    log_enabled = log.isEnabledFor(logging.INFO)

    for gidx, generator in enumerate(gens):
        if not generator.synchronous_p and async_demand < residual_hour_demand:
            gen, spl = generator.step(hour, async_demand)
        else:
            gen, spl = generator.step(hour, residual_hour_demand)
        if gen > residual_hour_demand and \
           not isclose(gen, residual_hour_demand):  # pragma: no cover
            msg = (f"generation ({gen:.4f}) > demand "
                   f"({residual_hour_demand:.4f}) for {generator}")
            raise AssertionError(msg)
        generation[hour, gidx] = gen

        if not generator.synchronous_p:
            async_demand -= gen
            if async_demand < -1e-6:
                raise AssertionError(async_demand)
            async_demand = max(async_demand, 0)

        residual_hour_demand -= gen
        if residual_hour_demand < -1e-6:
            raise AssertionError(residual_hour_demand)
        residual_hour_demand = max(residual_hour_demand, 0)

        if log_enabled:
            log.info(('GENERATOR: %s, generation: %.1f, spill: %.1f, '
                      'residual-demand: %.1f, async-demand: %.1f'),
                     generator, gen, spl, residual_hour_demand,
                     async_demand)

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
    date_range = pd.date_range(starthour, endhour, freq='h')

    _sim(context, date_range)

    # Calculate unserved energy.
    agg_demand = context.demand.sum(axis=1)
    agg_generation = context.generation.sum(axis=1)
    unserved = agg_demand - agg_generation
    # Ignore unserved events very close to 0 (rounding errors)
    context.unserved = unserved[~np.isclose(unserved, 0)]
