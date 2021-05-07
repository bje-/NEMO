# Copyright (C) 2021 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Penalty functions for the optimisation."""

from nemo import generators

_reason_labels = ['unserved', 'emissions', 'fossil', 'bioenergy',
                  'hydro', 'reserves', 'min-regional-gen']

reasons = {}
for i, label in enumerate(_reason_labels):
    reasons[label] = 1 << i

# Conversion factor between MWh and TWh.
_twh = pow(10., 6)


def unserved(ctx, _):
    """Penalty: unserved energy."""
    minuse = ctx.total_demand() * (ctx.relstd / 100)
    use = max(0, ctx.unserved_energy() - minuse)
    reason = reasons['unserved'] if use > 0 else 0
    return pow(use, 3), reason


def reserves(ctx, args):
    """Penalty: minimum reserves."""
    pen, reas = 0, 0
    for time in range(ctx.timesteps):
        reserve, spilled = 0, 0
        for gen in ctx.generators:
            try:
                spilled += gen.series_spilled[time]
            except KeyError:
                # non-variable generators may not have spill data
                pass

            # Calculate headroom for each generator, except pumped hydro and
            # CST -- tricky to calculate capacity
            if isinstance(gen, generators.Fuelled) and not \
               isinstance(gen, generators.PumpedHydro) and not \
               isinstance(gen, generators.CST):
                reserve += gen.capacity - gen.series_power[time]

        if reserve + spilled < args.reserves:
            reas |= reasons['reserves']
            pen += pow(args.reserves - reserve + spilled, 3)
    return pen, reas


def min_regional(ctx, _):
    """Penalty: minimum share of regional generation."""
    regional_generation_shortfall = 0
    for rgn in ctx.regions:
        regional_demand = 0
        for poly in rgn.polygons:
            regional_demand += ctx.demand[poly - 1].sum()
        regional_generation = 0
        for gen in ctx.generators:
            if gen.region() is rgn:
                regional_generation += sum(gen.series_power.values())
        min_regional_generation = regional_demand * ctx.min_regional_generation
        regional_generation_shortfall += max(0, min_regional_generation - regional_generation)
    reason = reasons['min-regional-gen'] if regional_generation_shortfall > 0 else 0
    return pow(regional_generation_shortfall, 3), reason


def emissions(ctx, args):
    """Penalty: total emissions."""
    total_emissions = 0
    for gen in ctx.generators:
        if hasattr(gen, 'intensity'):
            total_emissions += sum(gen.series_power.values()) * gen.intensity
    # exceedance in tonnes CO2-e
    emissions_exceedance = max(0, total_emissions - args.emissions_limit * pow(10, 6) * ctx.years)
    reason = reasons['emissions'] if emissions_exceedance > 0 else 0
    return pow(emissions_exceedance, 3), reason


def fossil(ctx, args):
    """Penalty: limit fossil to fraction of annual demand."""
    fossil_energy = 0
    for gen in ctx.generators:
        if isinstance(gen, generators.Fossil):
            fossil_energy += sum(gen.series_power.values())
    fossil_exceedance = max(0, fossil_energy - ctx.total_demand() * args.fossil_limit * ctx.years)
    reason = reasons['fossil'] if fossil_exceedance > 0 else 0
    return pow(fossil_exceedance, 3), reason


def bioenergy(ctx, args):
    """Penalty: limit biofuel use."""
    biofuel_energy = 0
    for gen in ctx.generators:
        if isinstance(gen, generators.Biofuel):
            biofuel_energy += sum(gen.series_power.values())
    biofuel_exceedance = max(0, biofuel_energy - args.bioenergy_limit * _twh * ctx.years)
    reason = reasons['bioenergy'] if biofuel_exceedance > 0 else 0
    return pow(biofuel_exceedance, 3), reason


def hydro(ctx, args):
    """Penalty: limit hydro use."""
    hydro_energy = 0
    for gen in ctx.generators:
        if isinstance(gen, generators.Hydro) and \
           not isinstance(gen, generators.PumpedHydro):
            hydro_energy += sum(gen.series_power.values())
    hydro_exceedance = max(0, hydro_energy - args.hydro_limit * _twh * ctx.years)
    reason = reasons['hydro'] if hydro_exceedance > 0 else 0
    return pow(hydro_exceedance, 3), reason
