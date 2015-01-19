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
import csv
import math
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
parser.add_argument("--hydro-limit", type=int, default=12, help='Limit on annual energy from hydro (TWh/y) [default: 12]')
parser.add_argument("--lambda", type=int, dest='lambda_', default=None, help='CMA-ES lambda value [default: 4+3*log(N)]')
parser.add_argument("--nsp-limit", type=float, default=consts.nsp_limit,
                    help='Non-synchronous penetration limit [default: %.2f]' % consts.nsp_limit)
parser.add_argument("--seed", type=int, default=None, help='seed for random number generator [default: None]')
parser.add_argument("--sigma", type=float, default=2., help='CMA-ES sigma value [default: 2.0]')
parser.add_argument("--trace-file", type=str, default=None, help='Filename for evaluation trace (comma separated) [default: None]')
parser.add_argument("--tx-costs", type=int, default=800, help='transmission costs ($/MW.km) [default: 800]')
parser.add_argument('--version', action='version', version='1.0')
args = parser.parse_args()
if __name__ == '__main__':
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
        if isinstance(g, generators.Hydro):
            hydro_energy += sum(g.hourly_power.values())
    hydro_exceedance = max(0, hydro_energy - args.hydro_limit * consts.twh * ctx.years)
    if hydro_exceedance > 0:
        reason |= 16
    penalty += pow(hydro_exceedance, 3)

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
    return score / ctx.demand.sum(), penalty / ctx.demand.sum(), reason


def set_generators(chromosome):
    """Set the generator list from the GA chromosome."""
    i = 0
    for gen in context.generators:
        newval = chromosome[i]
        for (setter, min_cap, max_cap) in gen.setters:
            if newval < min_cap:
                raise ValueError(min_cap - newval, 'capacity too low')
            if newval > max_cap:
                raise ValueError(newval - max_cap, 'capacity too high')
            setter(newval)
            i += 1
    # Check every parameter has been set.
    assert i == len(chromosome), '%d != %d' % (i, len(chromosome))


def eval_func(chromosome):
    """Annual cost of the system (in billion $)."""
    try:
        set_generators(chromosome)
    except ValueError, (delta, msg):
        return 1000 + delta * 1000,
    negativeCount = sum([True for x in chromosome if x < 0])
    if negativeCount > 0:
        # Penalise negative capacities in the chromosome
        return pow(negativeCount, 2) * 1000,
    nem.run(context)
    score, penalty, reason = cost(context, transmission_p=args.transmission)
    if args.trace_file is not None:
        # write the score and individual to the trace file
        with open(args.trace_file, 'a') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([score, penalty, reason] + list(chromosome))
    return score + penalty,


creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", list, fitness=creator.FitnessMin)
toolbox = base.Toolbox()
toolbox.register("map", futures.map)

numparams = sum([len(g.setters) for g in context.generators])
if args.lambda_ is None:
    # Use default DEAP CMA-ES lambda value.
    lam = int(4 + 3 * math.log(numparams))
else:
    lam = args.lambda_

strategy = cma.Strategy(centroid=[10] * numparams, sigma=args.sigma,
                        lambda_=lam)

toolbox.register("generate", strategy.generate, creator.Individual)
toolbox.register("update", strategy.update)
toolbox.register("evaluate", eval_func)


def run():
    """Run the GA."""
    if args.verbose and __name__ == '__main__':
        print "objective: minimise", eval_func.__doc__

    if args.seed is not None:
        np.random.seed(args.seed)
    hof = tools.HallOfFame(1)
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", np.mean)
    stats.register("std", np.std)
    stats.register("min", np.min)
    stats.register("max", np.max)

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
        print context.exchanges.max(axis=0)


if __name__ == '__main__':
    run()
