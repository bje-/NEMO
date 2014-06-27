# -*- Python -*-
# Copyright (C) 2011, 2014 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Load AEMO non-scheduled generation data into the HDF5 database."""

import argparse
import time
import tables

parser = argparse.ArgumentParser()
parser.add_argument("--db", type=str, default='nem.h5', help='HDF5 database filename')
parser.add_argument("--year", type=str, help='year of data set', required=True)
parser.add_argument("--compressor", type=str, default='blosc', help='PyTable compressor')
parser.add_argument("--complevel", type=int, default=6, help='PyTable compression level')
args = parser.parse_args()

h5file = tables.openFile(args.db, mode="r+")
print h5file
try:
    h5file.createGroup(h5file.root, 'aux')
except tables.exceptions.NodeError:
    pass

try:
    h5file.createGroup(h5file.root.aux, 'aemo%s' % args.year)
except tables.exceptions.NodeError:
    print 'group aemo%s already exists' % args.year


class DispatchInterval(tables.IsDescription):

    """Record format for dispatch data."""

    time = tables.Time32Col(pos=0)
    duid = tables.StringCol(8, pos=1)
    power = tables.Float32Col(pos=2)

f = tables.Filters(complevel=args.complevel, complib=args.compressor)
table = h5file.createTable('/aux/aemo%s' % args.year, 'nonsched', DispatchInterval,
                           "NEM %s non-scheduled generation" % args.year, filters=f)
dispatch = table.row

f = open('%s.csv' % args.year, 'r')
for count, line in enumerate(f):
    # eg. D,METER_DATA,GEN_DUID,1,"2008/12/31 04:05:00",CATHROCK,7.645,"2008/12/31 04:05:00"

    # Basic sanity check.
    if line[0:24] != 'D,METER_DATA,GEN_DUID,1,':
        print 'Warning: suspicious line %d: %s', count, line

    fields = line.split(',')
    timestamp = fields[4].strip('"')
    if timestamp[0:4] != args.year:
        print 'skipping line out of date range: ', timestamp, fields[5]
        continue

    t = time.mktime(time.strptime(timestamp, "%Y/%m/%d %H:%M:%S"))
    # All NEM times are UTC+10.
    t -= 60 * 60 * 10

    dispatch['time'] = t
    dispatch['duid'] = fields[5]
    dispatch['power'] = float(fields[6])
    dispatch.append()

h5file.flush()
f.close()
