# -*- Python -*-
# Copyright (C) 2010, 2011, 2014 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Load AEMO demand data for a year into the HDF5 database."""

import argparse
import tables
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument("--db", type=str, default='nem.h5', help='HDF5 database filename')
parser.add_argument("--year", type=str, help='year of data set', required=True)
parser.add_argument("--compressor", type=str, default='blosc', help='PyTable compressor')
parser.add_argument("--complevel", type=int, default=6, help='PyTable compression level')
args = parser.parse_args()

h5file = tables.openFile(args.db, mode="r+")
print h5file
try:
    h5file.createGroup(h5file.root.aux, 'aemo%s' % args.year)
except tables.exceptions.NodeError:
    pass

states = ['NSW', 'QLD', 'SA', 'TAS', 'VIC']
demand = np.zeros((len(states), 365 * 24 * 2))
rrp = np.zeros((len(states), 365 * 24 * 2))

f = open('%s.csv' % args.year, 'r')
periods = [0, 0, 0, 0, 0]
for line in f:
    # eg. NSW1,2009/01/01 00:30:00,7535,18.38
    x = line.split(',')
    state = x[0].rstrip('1')
    try:
        stcode = states.index(state)
    except ValueError:
        print 'Warning: %s not a valide state; skipping' % state
        continue
    period = periods[stcode]
    demand[stcode, period] = x[2]
    rrp[stcode, period] = x[3]
    periods[stcode] = periods[stcode] + 1

f = tables.Filters(complevel=args.complevel, complib=args.compressor)
h5file.createArray('/aux/aemo%s' % args.year, 'demand', demand, "NEM %s demand" % args.year)
h5file.createArray('/aux/aemo%s' % args.year, 'rrp', rrp, "NEM %s regional reference prices" % args.year)
h5file.flush()
