# -*- Python -*-
# Copyright (C) 2012, 2013 Ben Elliston
#
# replay.py -- replay NEM runs from a text file of generators
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

import argparse
import costs
import nem
import sys
import re

parser = argparse.ArgumentParser(description='Bug reports to: b.elliston@student.unsw.edu.au')
parser.add_argument("-f", type=str, help='replay file', required=True)
parser.add_argument("-v", action="store_true", help='verbose mode')
parser.add_argument("-x", action="store_true", help='producing a balancing plot')
parser.add_argument("-s", "--spills", action="store_true", help='plot spills')
args = parser.parse_args()


def set_generators(chromosome):
    "Set the generator list from the GA chromosome"
    i = 0
    for gen in context.generators:
        for setter, scale in gen.setters:
            setter(chromosome[i] * scale)
            i += 1
    # Check every parameter has been set.
    assert i == len(chromosome)


def run_one(chromosome):
    "annual cost of the system (in billion $)"
    assert len(chromosome) == 20
    context.costs = costs.AETA2012_2030Low(0.05, 1.3, 11, 42)
    set_generators(chromosome)
    nem.run(context)
    context.verbose = opts.v
    print context

    for i in range(nem.hours):
        print int(context.spill[::, i].sum())

context = nem.Context()
capacities = []
replayfile = open(opts.f)
for line in replayfile:
    if re.search('^\s*$', line):
        continue
    if re.search('^\s*#', line):
        print line,
        continue
    if not re.search('^\s*List:\s*\[.*\].?$', line) and opts.v:
        print 'skipping malformed input:', line
        continue
    m = re.match(r"^\s*List:\s*\[(.*)\].?$", line)
    capacities = m.group(1).split(',')
    capacities = map(float, capacities)  # str -> float
    run_one(capacities)
    print

    if opts.x:
        print 'Press Enter to start graphical browser ',
        sys.stdin.readline()
        nem.plot(context, spills=opts.spills)
