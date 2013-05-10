# -*- Python -*-
# Copyright (C) 2012 Ben Elliston
#
# evolve.py -- evolutionary exploration of the NEM
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

from pyevolve import Consts
from pyevolve import G1DList
from pyevolve import GSimpleGA
from pyevolve import Initializators
from pyevolve import Mutators
from pyevolve import Crossovers

import numpy as np
import optparse
import nem
import scenarios
import costs
import transmission

parser = optparse.OptionParser (version='1.0', description='Bug reports to: b.elliston@student.unsw.edu.au')
parser.add_option("-d", "--demand-scenario", type='string', default='unchanged', help='demand modification scenario [default: no change]')
parser.add_option("-f", "--frequency", type='int', default=10, help='frequency of stats output [default: 10]')
parser.add_option("-g", "--generations", type='int', default=100, help='generations [default: 100]')
parser.add_option("-p", "--population", type='int', default=100, help='population size [default: 100]')
parser.add_option("-r", "--discount-rate", type='float', default=0.05, help='discount rate [default: 0.05]')
parser.add_option("-s", "--supply-scenario", type='string', default='re100', help='generation mix scenario [default: \'re100\']')
parser.add_option("-t", "--transmission", action="store_true", default=False, help="include transmission [default: False]")
parser.add_option("-c", "--carbon-price", type='int', default=23, help='carbon price ($/t) [default: 23]')
parser.add_option("-x", action="store_true", default=False, help='Plot best individual at the end of run [default: False]')
parser.add_option("--coal-price", type='float', default=1.3, help='black coal price ($/GJ) [default: 1.30]')
parser.add_option("--gas-price", type='float', default=11.0, help='gas price ($/GJ) [default: 11]')
parser.add_option("--ccs-storage-costs", type='float', default=42, help='CCS storage costs ($/t) [default: 42]')
parser.add_option("--coal-ccs-costs", type='float', default=None, help='override capital cost of coal CCS ($/kW)')
parser.add_option("--tx-costs", type='int', default=800, help='transmission costs ($/MW.km) [default: 800]')
parser.add_option("--high-cost", action="store_false", dest="low_cost", help='Use low cost scenario [default: low]')
parser.add_option("--low-cost", action="store_true", default=True, help='Use high cost scenario')
parser.add_option("--spills", action="store_true", default=False, help='Plot spills [default: False]')

opts,args = parser.parse_args ()
print opts

np.set_printoptions (precision=5)
context = nem.Context ()

if opts.low_cost:
  context.costs = costs.AETA2030Low (opts.discount_rate, opts.coal_price, opts.gas_price, opts.ccs_storage_costs)
else:
  context.costs = costs.AETA2030High (opts.discount_rate, opts.coal_price, opts.gas_price, opts.ccs_storage_costs)
context.costs.carbon = opts.carbon_price
context.costs.transmission = transmission.Transmission (opts.tx_costs, opts.discount_rate)
if opts.coal_ccs_costs:
  fom = context.costs.fixed_om_costs[nem.generators.Coal_CCS]
  af = costs.annuity_factor (costs.AETA2030.lifetime, opts.discount_rate)
  context.costs.capcost_per_kw_per_yr[nem.generators.Coal_CCS] = opts.coal_ccs_costs / af + fom

# Set up the scenario.
scenarios.supply_switch (opts.supply_scenario) (context)
scenarios.demand_switch (opts.demand_scenario) (context)
print context.generators

def cost (context, transmission_p):
  "sum up the costs"
  score = 0

  for g in context.generators:
    score += g.capcost (context.costs) + g.opcost (context.costs)

  ### Penalty: unserved energy
  minuse = context.demand_energy * (context.relstd / 100)
  use = max (0, context.unserved_energy - minuse)
  score += pow (use, 3)

  ### Penalty: limit biofuel use
  biofuel_energy = 0
  for g in context.generators:
    if g.__class__ is nem.generators.Biofuel:
      biofuel_energy += g.hourly_power.sum ()
  biofuel_exceedance = max (0, biofuel_energy - 20*nem.twh)
  score += pow (biofuel_exceedance, 3)

  ### Penalty: limit hydro use
  hydro_energy = 0
  for g in context.generators:
    if g.__class__ is nem.generators.Hydro or g.__class__ is nem.generators.PumpedHydro:
      hydro_energy += g.hourly_power.sum ()
  hydro_exceedance = max (0, hydro_energy - 12*twh)
  score += pow (hydro_exceedance, 3)

  if transmission_p:
    maxexchanges = context.exchanges.max (axis=0)
    for i in range (5):
      # zero the diagonal entries
      maxexchanges[i,i] = 0

    for i in range (5):
      # then put the max (upper, lower) into lower
      # and zero the upper entries
      for j in range (i):
        maxexchanges[i,j] = max (maxexchanges[i,j], maxexchanges[j,i])
        maxexchanges[j,i] = 0
    txscore = (maxexchanges * context.costs.transmission.cost_matrix).sum ()
    score += txscore

  return score / pow (10,9)

def set_generators (chromosome):
  "Set the generator list from the GA chromosome"
  i = 0
  for gen in context.generators:
    for setter, scale in gen.setters:
      setter (chromosome[i] * scale)
      i += 1
  # Check every parameter has been set.
  assert i == len (chromosome)

def eval_func (chromosome):
  "annual cost of the system (in billion $)"
  set_generators (chromosome)
  nem.run (context)
  score = cost (context, transmission_p=opts.transmission)
  return score

def run ():
  print "objective: minimise", eval_func.__doc__

  numparams = sum ([len (g.setters) for g in context.generators])
  genome = G1DList.G1DList (numparams)

  genome.evaluator.set (eval_func)
  genome.setParams (rangemin=0, rangemax=40)
  genome.initializator.set(Initializators.G1DListInitializatorReal)
  genome.mutator.set(Mutators.G1DListMutatorRealGaussian)
  if numparams == 1:
    genome.crossover.set (Crossovers.G1DListCrossoverUniform)

  ga = GSimpleGA.GSimpleGA (genome)
  ga.setPopulationSize (opts.population)
  ga.setElitism (True)
  ga.setGenerations (opts.generations)
  ga.setMutationRate (0.1)
  ga.setMultiProcessing (True)
  ga.setMinimax (Consts.minimaxType["minimize"])
  ga.evolve (freq_stats=opts.frequency)

  best = ga.bestIndividual ()
  print best

  set_generators (best.getInternalList ())
  nem.run (context)
  context.verbose = True
  print context
  if opts.transmission:
	    print context.exchanges.max (axis=0)

  if opts.x:
    nem.plot (context, spills=opts.spills)

if __name__ == '__main__':
  run ()
