# -*- Python -*-
# Copyright (C) 2012, 2013 Ben Elliston
#
# replay.py -- replay NEM runs from a text file of generators
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

import optparse
import costs
import nem
import sys
import re

parser = optparse.OptionParser (version='1.0', description='Bug reports to: b.elliston@student.unsw.edu.au')
parser.add_option("-f", type='string', default=None, help='replay file')
parser.add_option("-v", action="store_true", default=False, help='verbose mode [default: False]')
parser.add_option("-x", action="store_true", default=False, help='Plot best individual at the end of run [default: False]')
parser.add_option("-s", "--spills", action="store_true", default=False, help='Plot spills [default: False]')
opts,args = parser.parse_args ()

if opts.f is None:
  parser.print_help ()
  sys.exit (1)

def set_generators (chromosome):
  "Set the generator list from the GA chromosome"
  i = 0
  for gen in context.generators:
    for setter, scale in gen.setters:
      setter (chromosome[i] * scale)
      i += 1
  # Check every parameter has been set.
  assert i == len (chromosome)

def run_one (chromosome):
  "annual cost of the system (in billion $)"
  assert len (chromosome) == 20
  context.costs = costs.AETA2030Low (0.05, 1.3, 11, 42)
  set_generators (chromosome)
  nem.run (context)
  context.verbose = opts.v
  print context

# Load a file like so:
#   Melbourne PV (VIC1), 0.0 GW
#     supplied 0.0 TWh
#   [...]

context = nem.Context ()
capacities = []
replayfile = open (opts.f)
for line in replayfile:
  if re.search ('GW$', line) and not re.search ('hydro', line):
    fields = line.split (' ')
    capacities.append (float (fields[-2]))
run_one (capacities)

if opts.x:
  print 'Press Enter to start graphical browser ',
  sys.stdin.readline ()
  nem.plot (context, spills=opts.spills)
