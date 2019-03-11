#!/usr/bin/env python3
#
# Copyright (C) 2012, 2013, 2014 Ben Elliston
# Copyright (C) 2014, 2015 The University of New South Wales
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Replay runs from a text file of generators."""
import argparse
import json
import re
import numpy as np

import nemo
from nemo import costs
from nemo import scenarios
from nemo import utils

parser = argparse.ArgumentParser(description='Bug reports to: nemo-devel@lists.ozlabs.org')
parser.add_argument("-f", type=str, help='filename of results file (default: results.json)', metavar='FILE', required=True)
parser.add_argument("--no-legend", action="store_false", help="hide legend")
parser.add_argument("-t", "--transmission", action="store_true", help="show region exchanges [default: False]")
parser.add_argument("-v", action="count", help='verbose mode')
parser.add_argument("-x", action="store_true", help='producing a balancing plot')
parser.add_argument("--spills", action="store_true", help='plot surplus generation')
args = parser.parse_args()


def run_one(bundle):
    """Run a single simulation."""
    options = bundle['options']

    context = nemo.Context()
    context.nsp_limit = options['nsp_limit']
    assert 0 <= context.nsp_limit <= 1

    scenario = options['supply_scenario']
    scenarios.supply_switch(scenario)(context)
    print('scenario', scenario)

    # Apply each demand modifier argument (if any) in the given order.
    for arg in options['demand_modifier']:
        scenarios.demand_switch(arg)(context)

    cost_class = costs.cost_switch(options['costs'])
    context.costs = cost_class(options['discount_rate'],
                               options['coal_price'], options['gas_price'],
                               options['ccs_storage_costs'])
    context.costs.carbon = options['carbon_price']

    capacities = bundle['parameters']
    context.set_capacities(capacities)

    context.track_exchanges = args.transmission
    context.verbose = args.v > 1
    nemo.run(context)
    context.verbose = args.v > 0
    print(context)
    if args.transmission:
        np.set_printoptions(precision=3)
        x = context.exchanges.max(axis=0)
        print(np.array_str(x, precision=1, suppress_small=True))
        with open('exchanges.json', 'w') as f:
            json.dump(x.tolist(), f)
    print()

    if args.x:  # pragma: no cover
        utils.plot(context, spills=args.spills, showlegend=args.no_legend)


with open(args.f) as resultsfile:
    for line in resultsfile:
        if re.search(r'^\s*$', line):
            continue
        if re.search(r'^\s*#', line):
            print(line, end=' ')
            continue
        try:
            bundle = json.loads(line)
        except ValueError:
            print('skipping malformed input:', line)
            continue
        run_one(bundle)
