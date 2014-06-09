#!/usr/bin/env python
# Load AEMO non-scheduled generation data for a year into the nem.h5 database.
#
# -*- Python -*-
# Copyright (C) 2011 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

from pylab import *
import optparse
import sys
import time
import datetime
import tables

parser = optparse.OptionParser ('populate-nonsched.py')
parser.add_option("--db", type='string', default='nem.h5', help='filename')
parser.add_option("--year", type='string', help='year of data set')
parser.add_option("--compressor", type='string', default='blosc', help='PyTable compressor')
parser.add_option("--complevel", type='int', default=6, help='PyTable compression level')

opts,args = parser.parse_args ()

if not opts.year:
    parser.print_help ()
    print
    sys.exit (1)

h5file = tables.openFile(opts.db, mode = "r+")
print h5file
try:
  h5file.createGroup(h5file.root, 'aux')
except tables.exceptions.NodeError:
  pass

try:
  h5file.createGroup(h5file.root.aux, 'aemo%s' % opts.year)
except tables.exceptions.NodeError:
  print 'group aemo%s already exists' % opts.year
  pass

class DispatchInterval(tables.IsDescription):
    time = tables.Time32Col(pos=0)
    duid = tables.StringCol(8,pos=1)
    power = tables.Float32Col (pos=2)

f = tables.Filters (complevel=opts.complevel, complib=opts.compressor)
table = h5file.createTable('/aux/aemo%s' % opts.year, 'nonsched', DispatchInterval, \
                               "NEM %s non-scheduled generation" % opts.year, filters=f)
dispatch = table.row

f = open ('%s.csv' % opts.year, 'r')
for count, line in enumerate (f):
  # eg. D,METER_DATA,GEN_DUID,1,"2008/12/31 04:05:00",CATHROCK,7.645,"2008/12/31 04:05:00"

  # Basic sanity check.
  if line[0:24] != 'D,METER_DATA,GEN_DUID,1,':
      print 'Warning: suspicious line %d: %s', count, line

  fields = line.split (',')
  timestamp = fields[4].strip ('"')
  if timestamp[0:4] != opts.year:
    print 'skipping line out of date range: ', timestamp, fields[5]
    continue

  t = time.mktime (time.strptime (timestamp, "%Y/%m/%d %H:%M:%S"))
  # All NEM times are UTC+10.
  t -= 60 * 60 * 10

  dispatch['time'] = t
  dispatch['duid'] = fields[5]
  dispatch['power'] = float (fields[6])
  dispatch.append ()

h5file.flush ()
f.close ()
