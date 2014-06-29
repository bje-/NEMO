# -*- Python -*-
# Copyright (C) 2012, 2013, 2014 Ben Elliston
#
# evolve.py -- evolutionary exploration of the NEM
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Evolutionary programming applied to NEM optimisations."""

import pyevolve
import os

if __name__ == '__main__':
    pyevolve.logEnable(os.getenv('HOME') + '/pyevolve.log')

from pyevolve import Consts
from pyevolve import G1DList
from pyevolve import GSimpleGA
from pyevolve import Initializators
from pyevolve import Migration
from pyevolve import Mutators
from pyevolve import Crossovers

import numpy as np
import argparse
import sys
import nem
import scenarios
import costs
import consts
import transmission

from mpi4py import MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()

parser = argparse.ArgumentParser(description='Bug reports to: b.elliston@unsw.edu.au')
parser.add_argument('--version', action='version', version='1.0')
parser.add_argument("-d", "--demand-modifier", type=str, action="append", help='demand modifier [default: unchanged]')
parser.add_argument("-f", "--frequency", type=int, default=10, help='frequency of stats output [default: 10]')
parser.add_argument("-g", "--generations", type=int, default=100, help='generations [default: 100]')
parser.add_argument("-m", "--mutation-rate", type=float, default=0.02, help='mutation rate [default: 0.02]')
parser.add_argument("-p", "--population", type=int, default=100, help='population size [default: 100]')
parser.add_argument("-q", "--quiet", action="store_true", help='be quiet')
parser.add_argument("-r", "--discount-rate", type=float, default=0.05, help='discount rate [default: 0.05]')
parser.add_argument("-s", "--supply-scenario", type=str, default='re100', help='generation mix scenario [default: \'re100\']')
parser.add_argument("-t", "--transmission", action="store_true", help="include transmission [default: False]")
parser.add_argument("-c", "--carbon-price", type=int, default=25, help='carbon price ($/t) [default: 25]')
parser.add_argument("-x", action="store_true", help='Plot best individual at the end of run [default: False]')
parser.add_argument("--coal-price", type=float, default=1.86, help='black coal price ($/GJ) [default: 1.86]')
parser.add_argument("--gas-price", type=float, default=11.0, help='gas price ($/GJ) [default: 11]')
parser.add_argument("--ccs-storage-costs", type=float, default=27, help='CCS storage costs ($/t) [default: 27]')
parser.add_argument("--emissions-limit", type=float, help='CO2 emissions limit (Mt) [default: None]')
parser.add_argument("--fossil-limit", type=float, help='Fraction of energy from fossil fuel [default: None]')
parser.add_argument("--coal-ccs-costs", type=float, help='override capital cost of coal CCS ($/kW)')
parser.add_argument("--tx-costs", type=int, default=800, help='transmission costs ($/MW.km) [default: 800]')
parser.add_argument("--low-cost", action="store_true", default=True, help='Use low technology costs [default]')
parser.add_argument("--high-cost", action="store_false", dest="low_cost", help='Use high technology costs')
parser.add_argument("--spills", action="store_true", help='Plot spills [default: False]')
args = parser.parse_args()
if rank == 0:
    print vars(args)

np.set_printoptions(precision=5)
context = nem.Context()

if args.low_cost:
    context.costs = costs.AETA2012_2030Low(args.discount_rate, args.coal_price, args.gas_price, args.ccs_storage_costs)
else:
    context.costs = costs.AETA2012_2030High(args.discount_rate, args.coal_price, args.gas_price, args.ccs_storage_costs)
context.costs.carbon = args.carbon_price
context.costs.transmission = transmission.Transmission(args.tx_costs, args.discount_rate)
if args.coal_ccs_costs is not None:
    fom = context.costs.fixed_om_costs[nem.generators.Coal_CCS]
    af = costs.annuity_factor(costs.AETA2012_2030.lifetime, args.discount_rate)
    context.costs.capcost_per_kw_per_yr[nem.generators.Coal_CCS] = args.coal_ccs_costs / af + fom

# Set up the scenario.
scenarios.supply_switch(args.supply_scenario)(context)
# Apply each demand modifier in the order given on the command line.
if args.demand_modifier is not None:
    for arg in args.demand_modifier:
        scenarios.demand_switch(arg)(context)

if not args.quiet and rank == 0:
    docstring = scenarios.supply_switch(args.supply_scenario).__doc__
    assert docstring is not None
    # Prune off any doctest test from the docstring.
    docstring = docstring.split('\n')[0]
    print "supply scenario: %s (%s)" % (args.supply_scenario, docstring)
    print context.generators


def cost(ctx, transmission_p):
    """Sum up the costs."""
    score = 0

    for g in ctx.generators:
        score += g.capcost(ctx.costs) + g.opcost(ctx.costs)

    ### Penalty: unserved energy
    minuse = ctx.demand.sum() * (ctx.relstd / 100)
    use = max(0, ctx.unserved_energy - minuse)
    score += pow(use, 3)

    ### Penalty: total emissions
    if args.emissions_limit is not None:
        emissions = 0
        for g in ctx.generators:
            try:
                emissions += g.hourly_power.sum() * g.intensity
            except AttributeError:
                # not all generators have an intensity attribute
                pass
        # exceedance in tonnes CO2-e
        emissions_exceedance = max(0, emissions - args.emissions_limit * pow(10, 6))
        score += pow(emissions_exceedance, 3)

    ### Penalty: limit fossil to fraction of annual demand
    if args.fossil_limit is not None:
        fossil_energy = 0
        for g in ctx.generators:
            if g.__class__ is nem.generators.CCGT or \
               g.__class__ is nem.generators.OCGT or \
               g.__class__ is nem.generators.Coal_CCS or \
               g.__class__ is nem.generators.CCGT_CCS or \
               g.__class__ is nem.generators.Black_Coal:
                fossil_energy += g.hourly_power.sum()
        fossil_exceedance = max(0, fossil_energy - ctx.demand.sum() * args.fossil_limit)
        score += pow(fossil_exceedance, 3)

    ### Penalty: limit biofuel use
    biofuel_energy = 0
    for g in ctx.generators:
        if g.__class__ is nem.generators.Biofuel:
            biofuel_energy += g.hourly_power.sum()
    biofuel_exceedance = max(0, biofuel_energy - 20 * consts.twh)
    score += pow(biofuel_exceedance, 3)

    ### Penalty: limit hydro use
    hydro_energy = 0
    for g in ctx.generators:
        if g.__class__ is nem.generators.Hydro or g.__class__ is nem.generators.PumpedHydro:
            hydro_energy += g.hourly_power.sum()
    hydro_exceedance = max(0, hydro_energy - 12 * consts.twh)
    score += pow(hydro_exceedance, 3)

    if transmission_p:
        maxexchanges = ctx.exchanges.max(axis=0)
        for i in range(5):
            # zero the diagonal entries
            maxexchanges[i, i] = 0

        for i in range(5):
            # then put the max (upper, lower) into lower
            # and zero the upper entries
            for j in range(i):
                maxexchanges[i, j] = max(maxexchanges[i, j], maxexchanges[j, i])
                maxexchanges[j, i] = 0
        txscore = (maxexchanges * ctx.costs.transmission.cost_matrix).sum()
        score += txscore

    return score / pow(10, 9)


def set_generators(chromosome):
    """Set the generator list from the GA chromosome."""
    i = 0
    for gen in context.generators:
        for setter, scale in gen.setters:
            setter(chromosome[i] * scale)
            i += 1
    # Check every parameter has been set.
    assert i == len(chromosome)


def eval_func(chromosome):
    """Annual cost of the system (in billion $)."""
    set_generators(chromosome)
    nem.run(context)
    score = cost(context, transmission_p=args.transmission)
    return score


def run():
    """Run the GA."""
    if rank == 0:
        print "objective: minimise", eval_func.__doc__

    numparams = sum([len(g.setters) for g in context.generators])
    genome = G1DList.G1DList(numparams)

    genome.evaluator.set(eval_func)
    genome.setParams(rangemin=0, rangemax=40)
    genome.initializator.set(Initializators.G1DListInitializatorReal)
    genome.mutator.set(Mutators.G1DListMutatorRealGaussian)
    if numparams == 1:
        genome.crossover.set(Crossovers.G1DListCrossoverUniform)

    ga = GSimpleGA.GSimpleGA(genome)
    mig = Migration.MPIMigration()
    mig.setMigrationRate(2)
    ga.setMigrationAdapter(mig)
    ga.setPopulationSize(args.population)
    ga.setElitism(True)
    ga.setGenerations(args.generations)
    ga.setMutationRate(args.mutation_rate)
    ga.setMultiProcessing(True)
    ga.setMinimax(Consts.minimaxType["minimize"])
    ga.evolve(freq_stats=args.frequency)

    if not args.quiet and rank == 0:
        best = ga.bestIndividual()
        print best

        set_generators(best.getInternalList())
        nem.run(context)
        context.verbose = True
        print context
        if args.transmission:
            print context.exchanges.max(axis=0)

    if args.x and rank == 0:  # pragma: no cover
        print 'Press Enter to start graphical browser ',
        sys.stdin.readline()
        nem.plot(context, spills=args.spills)

    # Force database closure to avoid pytables output.
    nem.h5file.close()

if __name__ == '__main__':
    import doctest
    doctest.testmod()
    run()
