# Copyright (C) 2012, 2013, 2014 Ben Elliston
# Copyright (C) 2014, 2015 The University of New South Wales
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Evolutionary programming applied to NEM optimisations."""

from deap import algorithms
from deap import base
from deap import creator
from deap import tools
from deap import cma
from scoop import futures

import os
import sys
import csv
import numpy as np
import argparse
import nem
import generators
import scenarios
import costs
import consts
import transmission

parser = argparse.ArgumentParser(description='Bug reports to: b.elliston@unsw.edu.au')
parser.add_argument("-c", "--carbon-price", type=int, default=25, help='carbon price ($/t) [default: 25]')
parser.add_argument("-d", "--demand-modifier", type=str, action="append", help='demand modifier [default: unchanged]')
parser.add_argument("-g", "--generations", type=int, default=100, help='generations [default: 100]')
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
parser.add_argument("--hydro-limit", type=float, default=12, help='Limit on annual energy from hydro (TWh/y) [default: 12]')
parser.add_argument("--lambda", type=int, dest='lambda_', default=None, help='CMA-ES lambda value [default: 10*N]')
parser.add_argument("--list-scenarios", action="store_true")
parser.add_argument("--min-regional-generation", type=float, default=None,
                    help='minimum share of energy generated intra-region [default: None]')
parser.add_argument("--nsp-limit", type=float, default=consts.nsp_limit,
                    help='Non-synchronous penetration limit [default: %.2f]' % consts.nsp_limit)
parser.add_argument("--reliability-std", type=float, default=None, help='reliability standard (%% unserved)')
parser.add_argument("--seed", type=int, default=None, help='seed for random number generator [default: None]')
parser.add_argument("--sigma", type=float, default=2., help='CMA-ES sigma value [default: 2.0]')
parser.add_argument("--trace-file", type=str, default=None, help='Filename for evaluation trace (comma separated) [default: None]')
parser.add_argument("--tx-costs", type=int, default=800, help='transmission costs ($/MW.km) [default: 800]')
parser.add_argument('--version', action='version', version='1.0')
args = parser.parse_args()

if __name__ == '__main__' and args.list_scenarios:
    for key in sorted(scenarios.supply_scenarios):
        descr = scenarios.supply_scenarios[key].__doc__
        print '%20s' % key, '\t', descr.split('\n')[0]
    print
    sys.exit(0)

if __name__ == '__main__':
    print vars(args)

np.set_printoptions(precision=5)
context = nem.Context()

# Set the system non-synchronous penetration limit.
context.nsp_limit = args.nsp_limit
assert 0 <= context.nsp_limit <= 1, \
    "NSP limit must be in the interval [0,1]"

# Override the reliability standard (if the user gives this option).
if args.reliability_std is not None:
    context.relstd = args.reliability_std

# Likewise for the minimum share of regional generation.
context.min_regional_generation = args.min_regional_generation
assert context.min_regional_generation is None or \
    (0 <= context.min_regional_generation <= 1), \
    "Minimum regional generation must be in the interval [0,1]"

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

if args.verbose and __name__ == '__main__':
    docstring = scenarios.supply_switch(args.supply_scenario).__doc__
    assert docstring is not None
    # Prune off any doctest test from the docstring.
    docstring = docstring.split('\n')[0]
    print "supply scenario: %s (%s)" % (args.supply_scenario, docstring)
    print context.generators

if args.trace_file is not None:
    try:
        os.unlink(args.trace_file)
    except OSError:
        pass


def cost(ctx, transmission_p):
    """Sum up the costs."""
    score = 0
    for g in ctx.generators:
        score += (g.capcost(ctx.costs) * ctx.years) + g.opcost(ctx.costs)

    penalty = 0
    reason = 0

    ### Penalty: unserved energy
    minuse = ctx.demand.sum() * (ctx.relstd / 100)
    use = max(0, ctx.unserved_energy - minuse)
    if use > 0:
        reason |= 1
    penalty += pow(use, 3)

    ### Penalty: minimum share of regional generation
    if ctx.min_regional_generation is not None:
        regional_generation_shortfall = 0
        for rgn in ctx.regions:
            regional_generation = 0
            for g in ctx.generators:
                if g.region() is rgn:
                    regional_generation += sum(g.hourly_power.values())
            min_regional_generation = sum(context.demand[rgn]) * ctx.min_regional_generation
            regional_generation_shortfall += max(0, min_regional_generation - regional_generation)
        penalty += pow(regional_generation_shortfall, 3)

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
        if emissions_exceedance > 0:
            reason |= 2
        penalty += pow(emissions_exceedance, 3)

    ### Penalty: limit fossil to fraction of annual demand
    if args.fossil_limit is not None:
        fossil_energy = 0
        for g in ctx.generators:
            if isinstance(g, generators.Fossil):
                fossil_energy += sum(g.hourly_power.values())
        fossil_exceedance = max(0, fossil_energy - ctx.demand.sum() * args.fossil_limit * ctx.years)
        if fossil_exceedance > 0:
            reason |= 4
        penalty += pow(fossil_exceedance, 3)

    ### Penalty: limit biofuel use
    biofuel_energy = 0
    for g in ctx.generators:
        if isinstance(g, generators.Biofuel):
            biofuel_energy += sum(g.hourly_power.values())
    biofuel_exceedance = max(0, biofuel_energy - args.bioenergy_limit * consts.twh * ctx.years)
    if biofuel_exceedance > 0:
        reason |= 8
    penalty += pow(biofuel_exceedance, 3)

    ### Penalty: limit hydro use
    hydro_energy = 0
    for g in ctx.generators:
        if isinstance(g, generators.Hydro) and \
           not isinstance(g, generators.PumpedHydro):
            hydro_energy += sum(g.hourly_power.values())
    hydro_exceedance = max(0, hydro_energy - args.hydro_limit * consts.twh * ctx.years)
    if hydro_exceedance > 0:
        reason |= 16
    penalty += pow(hydro_exceedance, 3)

    if transmission_p:
        maxexchanges = ctx.exchanges.max(axis=0)
        np.fill_diagonal(maxexchanges, 0)
        for i in range(1, maxexchanges.shape[0]):
            # then put the max (upper, lower) into lower
            # and zero the upper entries
            for j in range(i):
                maxexchanges[i, j] = max(maxexchanges[i, j], maxexchanges[j, i])
                maxexchanges[j, i] = 0
        # ignore row 0 and column 0 of maxexchanges
        txscore = (maxexchanges[1:, 1:] * ctx.costs.transmission.cost_matrix[1:, 1:]).sum()
        score += txscore

    # Express $/yr as an average $/MWh over the period
    return score / ctx.demand.sum(), penalty / ctx.demand.sum(), reason


def set_generators(chromosome):
    """Set the generator list from the chromosome."""
    i = 0
    for gen in context.generators:
        for (setter, min_cap, max_cap) in gen.setters:
            newval = chromosome[i]
            assert newval >= min_cap, \
                'capacity under %.3f GW min. build' % min_cap
            assert newval <= max_cap, \
                'capacity over %.3f GW max. build' % max_cap
            setter(newval)
            i += 1
    # Check every parameter has been set.
    assert i == len(chromosome), '%d != %d' % (i, len(chromosome))


def eval_func(chromosome):
    """Annual cost of the system (in billion $)."""
    set_generators(chromosome)
    nem.run(context)
    score, penalty, reason = cost(context, transmission_p=args.transmission)
    if args.trace_file is not None:
        # write the score and individual to the trace file
        with open(args.trace_file, 'a') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([score, penalty, reason] + list(chromosome))
    return score + penalty,


def repair_func():
    """Decorator to repair constraint-violating individuals."""
    def decorator(func):
        def wrapper(*argums, **kargs):
            indivs = func(*argums, **kargs)
            for indiv in indivs:
                i = 0
                for gen in context.generators:
                    for (_, min_cap, max_cap) in gen.setters:
                        # enforce the range (min_cap, max_cap)
                        indiv[i] = max(min(indiv[i], max_cap), min_cap)
                        i += 1
            return indivs
        return wrapper
    return decorator


creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", list, fitness=creator.FitnessMin)
toolbox = base.Toolbox()
toolbox.register("map", futures.map)

numparams = sum([len(g.setters) for g in context.generators])
if args.lambda_ is None:
    lam = 10 * numparams
else:
    lam = args.lambda_

strategy = cma.Strategy(centroid=[10] * numparams, sigma=args.sigma,
                        lambda_=lam)

toolbox.register("generate", strategy.generate, creator.Individual)
toolbox.decorate("generate", repair_func())
toolbox.register("update", strategy.update)
toolbox.register("evaluate", eval_func)


def run():
    """Run the evolution."""
    if args.verbose and __name__ == '__main__':
        print "objective: minimise", eval_func.__doc__

    if args.seed is not None:
        np.random.seed(args.seed)
    hof = tools.HallOfFame(1)
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("min", np.min)

    algorithms.eaGenerateUpdate(toolbox, ngen=args.generations, stats=stats,
                                halloffame=hof, verbose=True)

    (score,) = hof[0].fitness.values
    print 'Score: %.2f $/MWh' % score
    print 'List:', hof[0]

    set_generators(hof[0])
    nem.run(context)
    context.verbose = True
    print context
    if args.transmission:
        x = context.exchanges.max(axis=0)
        print np.array_str(x, precision=1, suppress_small=True)
        np.savetxt('exchanges.csv', x, fmt='%.1f', delimiter=',')


if __name__ == '__main__':
    run()
