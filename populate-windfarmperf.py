#!/usr/bin/env python
# Load wind generation data from http://windfarmperformance.info for a
# year into the database.
#
# -*- Python -*-
# Copyright (C) 2011, 2014 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

import argparse
import string
import time
import tables

parser = argparse.ArgumentParser()
parser.add_argument("--db", type=str, default='nem.h5', help='HDF5 database filename')
parser.add_argument("--year", type=str, help='year of data set', required=True)
parser.add_argument("--compressor", type=str, default='blosc', help='PyTable compressor')
parser.add_argument("--complevel", type=int, default=6, help='PyTable compression level')
args = parser.parse_args()

h5file = tables.openFile(args.db, mode='r+')
print h5file
try:
    h5file.createGroup(h5file.root, 'aux')
except tables.exceptions.NodeError:
    pass

try:
    h5file.createGroup(h5file.root.aux, 'windfarmperf%s' % args.year)
except tables.exceptions.NodeError:
    print 'group windfarmperf%s already exists' % args.year


class DispatchInterval(tables.IsDescription):
    time = tables.Time32Col(pos=0)
    duid = tables.StringCol(8, pos=1)
    power = tables.Float32Col(pos=2)

f = tables.Filters(complevel=args.complevel, complib=args.compressor)
table = h5file.createTable('/aux/windfarmperf%s' % args.year, 'data', DispatchInterval,
                           "windfarmperformance.info %s wind generation" % args.year, filters=f)
dispatch = table.row

for month in range(12):
    f = open('aemo_wind_%s%02d.csv' % (args.year, month + 1), 'r')
    for count, line in enumerate(f):
        line = line.strip()
        # "timestamp","woolnth1","captl_wf","cathrock", ...
        if count == 0:
            line = string.upper(line)
            line = string.replace(line, '"', '')
            duids = line.split(',')[1:]
        else:
            fields = line.split(',')
            timestamp = fields[0].strip('"')
            if timestamp[0:4] != args.year:
                print 'skipping line out of date range: ', timestamp
                continue
            t = time.mktime(time.strptime(timestamp, "%Y-%m-%d %H:%M:%S"))
            # All NEM times are UTC+10.
            t -= 60 * 60 * 10
            for duid, power in zip(duids, fields[1:]):
                if power == '':
                    # no record
                    continue
                dispatch['time'] = t
                dispatch['duid'] = duid
                dispatch['power'] = float(power)
                dispatch.append()
    f.close()
h5file.flush()
