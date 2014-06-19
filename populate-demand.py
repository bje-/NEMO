#!/usr/bin/env python
# Load AEMO demand data for a year into the nem.h5 database.
#
# -*- Python -*-
# Copyright (C) 2010, 2011 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

from pylab import *
import optparse
import sys
import datetime
import tables

parser = optparse.OptionParser('populate-demand.py')
parser.add_option("--db", type='string', default='nem.h5', help='filename')
parser.add_option("--year", type='string', help='year of data set')
parser.add_option("--compressor", type='string', default='blosc', help='PyTable compressor')
parser.add_option("--complevel", type='int', default=6, help='PyTable compression level')

opts, args = parser.parse_args()

if not opts.year:
    parser.print_help()
    print
    sys.exit(1)

h5file = tables.openFile(opts.db, mode="r+")
print h5file
try:
    h5file.createGroup(h5file.root.aux, 'aemo%s' % opts.year)
except tables.exceptions.NodeError:
    pass

states = ['NSW', 'QLD', 'SA', 'TAS', 'VIC']
demand = np.zeros((len(states), 365 * 24 * 2))
rrp = np.zeros((len(states), 365 * 24 * 2))

f = open('%s.csv' % opts.year, 'r')
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

f = tables.Filters(complevel=opts.complevel, complib=opts.compressor)
h5file.createArray('/aux/aemo%s' % opts.year, 'demand', demand, "NEM %s demand" % opts.year)
h5file.createArray('/aux/aemo%s' % opts.year, 'rrp', rrp, "NEM %s regional reference prices" % opts.year)
h5file.flush()
