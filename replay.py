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
parser.add_option("-x", action="store_true", default=False, help='producing a balancing plot [default: False]')
parser.add_option("-s", "--spills", action="store_true", default=False, help='plot spills [default: False]')
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

  for i in range (8760):
    print int (context.spill[::,i].sum ())

context = nem.Context ()
capacities = []
replayfile = open (opts.f)
for line in replayfile:
  if re.search ('^\s*$', line):
    continue
  if re.search ('^\s*#', line):
    print line,
    continue
  if not re.search ('^\s*List:\s*\[.*\].?$', line) and opts.v:
    print 'skipping malformed input:', line
    continue
  m = re.match (r"^\s*List:\s*\[(.*)\].?$", line)
  capacities = m.group(1).split (',')
  capacities = map (float, capacities)  # str -> float
  run_one (capacities)
  print

  if opts.x:
    print 'Press Enter to start graphical browser ',
    sys.stdin.readline ()
    nem.plot (context, spills=opts.spills)
