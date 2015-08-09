# Copyright (C) 2012, 2013, 2014 Ben Elliston
# Copyright (C) 2014 The University of New South Wales
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Replay NEM runs from a text file of generators."""
import argparse
import re

import consts
import costs
import nem
import scenarios


parser = argparse.ArgumentParser(description='Bug reports to: b.elliston@unsw.edu.au')
parser.add_argument("-f", type=str, help='replay file', required=True)
parser.add_argument("-v", action="store_true", help='verbose mode')
parser.add_argument("-x", action="store_true", help='producing a balancing plot')
parser.add_argument("-s", "--supply-scenario", type=str, help='scenario name', default='re100')
parser.add_argument("--nsp-limit", type=float, default=consts.nsp_limit,
                    help='Non-synchronous penetration limit [default: %.2f]' % consts.nsp_limit)
parser.add_argument("--spills", action="store_true", help='plot spills')
args = parser.parse_args()


def set_generators(chromosome):
    """Set the generator list from the GA chromosome."""
    i = 0
    for gen in context.generators:
        for (setter, _, _) in gen.setters:
            setter(chromosome[i])
            i += 1
    # Check every parameter has been set.
    assert i == len(chromosome), '%d != %d' % (i, len(chromosome))


def run_one(chromosome):
    """Annual cost of the system (in billion $)."""
    context.costs = costs.AETA2013_2030Mid(0.05, 1.86, 11, 27)
    context.costs.carbon = 0
    set_generators(chromosome)
    context.verbose = 0
    nem.run(context)
    context.verbose = args.v
    print context

context = nem.Context()
context.nsp_limit = args.nsp_limit
assert context.nsp_limit >= 0 and context.nsp_limit <= 1, \
    "NSP limit must be in the interval [0,1]"
scenarios.supply_switch(args.supply_scenario)(context)
capacities = []
replayfile = open(args.f)
for line in replayfile:
    if re.search(r'^\s*$', line):
        continue
    if re.search(r'^\s*#', line):
        print line,
        continue
    if not re.search(r'^\s*List:\s*\[.*\]\s*.?$', line):
        print 'skipping malformed input:', line
        continue
    m = re.match(r'^\s*List:\s*\[(.*)\]\s*.?$', line)
    capacities = m.group(1).split(',')
    capacities = [float(elt) for elt in capacities]  # str -> float
    run_one(capacities)
    print

    if args.x:  # pragma: no cover
        nem.plot(context, spills=args.spills)
