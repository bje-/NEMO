# -*- Python -*-
# Copyright (C) 2012, 2013 Ben Elliston
#
# replay.py -- replay NEM runs from a text file of generators
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

import numpy as np
import evolve
import nem
import sys

if len (sys.argv) != 2:
  print 'Usage: %s FILE' % (sys.argv[0])
  sys.exit (1)

np.set_printoptions (precision=0)

def eval_func (chromosome):
  "annual cost of the system (in billion $)"

  context = nem.Context ()
  for i, capacity in enumerate (chromosome[:-5]):
    context.generators[i].set_capacity (capacity * 1000)
  # the last five genes go into the last five generator slots
  # skip all the hydro stuff
  for i, capacity in enumerate (chromosome[-5:]):
    context.generators[-5+i].set_capacity (capacity * 1000)

  nem.run (context)
  newscore = evolve.cost (context, False)
  if newscore > 100:
    print 'WARNING: high score:', newscore

  m = context.exchanges.max (axis=0)
  for i in range (5):
    m[i,i] = 0
  return m

# Load the top 24 into a list of lists.
runs = np.genfromtxt (sys.argv[1])
results = np.zeros ((runs.shape[0],5,5))
for i, soln in enumerate (runs):
  results[i] = eval_func (soln[1:])
  # print results[i]

# What is this?
print '--- RESULTS for res.data ---'
r = ['NSW1', 'QLD1', 'SA1', 'TAS1', 'VIC1']
for i in range (5):
  for j in range (5):
    # iterate over each region pair
    print j, results[i,j].mean (0), results[i,j].min (0), results[i,j].max (0), r[j]
  print; print

print '--- RESULTS for .data ---'
evolve.scoreTx=True
for i, soln in enumerate (runs):
  # use the original evaluation function (cost)
  newscore = evolve.eval_func (soln[1:])
  print soln[0], newscore
