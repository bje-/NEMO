# Copyright (C) 2012, 2013, 2014 Ben Elliston
# Copyright (C) 2014 The University of New South Wales
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Evolutionary programming applied to NEM optimisations."""

from pyevolve import Consts
from pyevolve import G1DList
from pyevolve import GAllele
from pyevolve import GSimpleGA
from pyevolve import Initializators
from pyevolve import Migration
from pyevolve import Mutators
from pyevolve import Crossovers
from pyevolve import Selectors

import csv
import numpy as np
import argparse
import nem
import generators
import scenarios
import costs
import consts
import transmission

from mpi4py import MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()

parser = argparse.ArgumentParser(description='Bug reports to: b.elliston@unsw.edu.au')
parser.add_argument("-c", "--carbon-price", type=int, default=25, help='carbon price ($/t) [default: 25]')
parser.add_argument("-d", "--demand-modifier", type=str, action="append", help='demand modifier [default: unchanged]')
parser.add_argument("-f", "--frequency", type=int, default=10, help='frequency of stats output [default: 10]')
parser.add_argument("-g", "--generations", type=int, default=100, help='generations [default: 100]')
parser.add_argument("-j", "--jobs", type=int, default=1, help='number of worker processes [default: 1]')
parser.add_argument("-m", "--mutation-rate", type=float, default=0.02, help='mutation rate [default: 0.02]')
parser.add_argument("-p", "--population", type=int, default=100, help='population size [default: 100]')
parser.add_argument("-r", "--discount-rate", type=float, default=0.05, help='discount rate [default: 0.05]')
parser.add_argument("-s", "--supply-scenario", type=str, default='re100', help='generation mix scenario [default: \'re100\']')
parser.add_argument("-t", "--transmission", action="store_true", help="include transmission [default: False]")
parser.add_argument("-v", "--verbose", action="store_true", help="be verbose")
parser.add_argument("--bioenergy-limit", type=float, default=20, help='Limit on annual energy from bioenergy (TWh/y) [default: 20.0]')
parser.add_argument("--ccs-storage-costs", type=float, default=27, help='CCS storage costs ($/t) [default: 27]')
parser.add_argument("--coal-ccs-costs", type=float, help='override capital cost of coal CCS ($/kW)')
parser.add_argument("--coal-price", type=float, default=1.86, help='black coal price ($/GJ) [default: 1.86]')
parser.add_argument("--costs", type=str, default='AETA2013-in2030-mid', help='cost scenario [default: AETA2013-in2030-mid]')
parser.add_argument("--emissions-limit", type=float, help='CO2 emissions limit (Mt/y) [default: None]')
parser.add_argument("--fossil-limit", type=float, help='Fraction of energy from fossil fuel [default: None]')
parser.add_argument("--gas-price", type=float, default=11.0, help='gas price ($/GJ) [default: 11]')
parser.add_argument("--hydro-limit", type=int, default=12, help='Limit on annual energy from hydro (TWh/y) [default: 12]')
parser.add_argument("--nsp-limit", type=float, default=consts.nsp_limit,
                    help='Non-synchronous penetration limit [default: %.2f]' % consts.nsp_limit)
parser.add_argument("--trace-file", type=str, default=None, help='Filename for evaluation trace (comma separated) [default: None]')
parser.add_argument("--tx-costs", type=int, default=800, help='transmission costs ($/MW.km) [default: 800]')
parser.add_argument('--version', action='version', version='1.0')
args = parser.parse_args()
if rank == 0:
    print vars(args)

np.set_printoptions(precision=5)
context = nem.Context()

# Set the system non-synchronous penetration limit.
context.nsp_limit = args.nsp_limit
assert context.nsp_limit >= 0 and context.nsp_limit <= 1, \
    "NSP limit must be in the interval [0,1]"

cost_class = costs.cost_switch(args.costs)
context.costs = cost_class(args.discount_rate, args.coal_price, args.gas_price, args.ccs_storage_costs)
context.costs.carbon = args.carbon_price
context.costs.transmission = transmission.Transmission(args.tx_costs, args.discount_rate)
if args.coal_ccs_costs is not None:
    fom = context.costs.fixed_om_costs[generators.Coal_CCS]
    af = costs.annuity_factor(context.costs.lifetime, args.discount_rate)
    context.costs.capcost_per_kw_per_yr[generators.Coal_CCS] = args.coal_ccs_costs / af + fom

# Set up the scenario.
scenarios.supply_switch(args.supply_scenario)(context)
# Apply each demand modifier in the order given on the command line.
if args.demand_modifier is not None:
    for arg in args.demand_modifier:
        scenarios.demand_switch(arg)(context)

if args.verbose and rank == 0:
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
        score += (g.capcost(ctx.costs) * ctx.years) + g.opcost(ctx.costs)

    ### Penalty: unserved energy
    minuse = ctx.demand.sum() * (ctx.relstd / 100)
    use = max(0, ctx.unserved_energy - minuse)
    score += pow(use, 3)

    ### Penalty: total emissions
    if args.emissions_limit is not None:
        emissions = 0
        for g in ctx.generators:
            try:
                emissions += sum(g.hourly_power.values()) * g.intensity
            except AttributeError:
                # not all generators have an intensity attribute
                pass
        # exceedance in tonnes CO2-e
        emissions_exceedance = max(0, emissions - args.emissions_limit * pow(10, 6) * ctx.years)
        score += pow(emissions_exceedance, 3)

    ### Penalty: limit fossil to fraction of annual demand
    if args.fossil_limit is not None:
        fossil_energy = 0
        for g in ctx.generators:
            if isinstance(g, generators.Fossil):
                fossil_energy += sum(g.hourly_power.values())
        fossil_exceedance = max(0, fossil_energy - ctx.demand.sum() * args.fossil_limit * ctx.years)
        score += pow(fossil_exceedance, 3)

    ### Penalty: limit biofuel use
    biofuel_energy = 0
    for g in ctx.generators:
        if isinstance(g, generators.Biofuel):
            biofuel_energy += sum(g.hourly_power.values())
    biofuel_exceedance = max(0, biofuel_energy - args.bioenergy_limit * consts.twh * ctx.years)
    score += pow(biofuel_exceedance, 3)

    ### Penalty: limit hydro use
    hydro_energy = 0
    for g in ctx.generators:
        if isinstance(g, generators.Hydro):
            hydro_energy += sum(g.hourly_power.values())
    hydro_exceedance = max(0, hydro_energy - args.hydro_limit * consts.twh * ctx.years)
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

    # Express $/yr as an average $/MWh over the period
    return score / ctx.demand.sum()


def set_generators(chromosome):
    """Set the generator list from the GA chromosome."""
    i = 0
    for gen in context.generators:
        for (setter, _, _) in gen.setters:
            setter(chromosome[i])
            i += 1
    # Check every parameter has been set.
    assert i == len(chromosome), '%d != %d' % (i, len(chromosome))


def eval_func(chromosome):
    """Annual cost of the system (in billion $)."""
    set_generators(chromosome)
    nem.run(context)
    score = cost(context, transmission_p=args.transmission)
    if args.trace_file is not None:
        # write the score and individual to the trace file
        with open(args.trace_file, 'a') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([score] + list(chromosome))
    return score


def run():
    """Run the GA."""
    if args.verbose and rank == 0:
        print "objective: minimise", eval_func.__doc__

    numparams = sum([len(g.setters) for g in context.generators])
    genome = G1DList.G1DList(numparams)

    alleles = GAllele.GAlleles()
    for g in context.generators:
        for (_, rangemin, rangemax) in g.setters:
            a = GAllele.GAlleleRange(rangemin, rangemax, real=True)
            alleles.add(a)

    genome.evaluator.set(eval_func)
    genome.setParams(allele=alleles)
    genome.initializator.set(Initializators.G1DListInitializatorAllele)
    genome.mutator.set(Mutators.G1DListMutatorAlleleGaussian)
    genome.crossover.set(Crossovers.G1DListCrossoverUniform)

    ga = GSimpleGA.GSimpleGA(genome)
    mig = Migration.MPIMigration()
    mig.setMigrationRate(10)
    ga.setMigrationAdapter(mig)
    ga.setPopulationSize(args.population)
    ga.selector.set(Selectors.GTournamentSelector)
    ga.setElitism(True)
    ga.setGenerations(args.generations)
    ga.setMutationRate(args.mutation_rate)
    if args.jobs > 1:
        ga.setMultiProcessing(True, max_processes=args.jobs)
    ga.setMinimax(Consts.minimaxType["minimize"])
    ga.evolve(freq_stats=args.frequency)

    mig.selector.set(Selectors.GRankSelector)
    mig.gather_bests()

    if rank == 0:
        if mig.all_stars is not None:
            best = min(mig.all_stars, key=lambda(x): x.score)
        else:
            best = ga.bestIndividual()
        if args.verbose:
            print best
        else:
            print 'Score: %.2f $/MWh' % best.score
            print 'List:', best.getInternalList()

        set_generators(best.getInternalList())
        nem.run(context)
        context.verbose = True
        print context
        if args.transmission:
            print context.exchanges.max(axis=0)

if __name__ == '__main__':
    run()
