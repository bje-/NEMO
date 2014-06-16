#!/usr/bin/python
#
# A utility to populate a new HDF5 file. -*- Python -*-

import sys
import time
import datetime
import numpy as np
import tables
import optparse
import bz2
import os

# 1998 to 2011 inclusive
startDate = datetime.datetime(1998, 1, 1)
endDate = datetime.datetime(2012, 1, 1)
maxentries = (endDate - startDate).days * 24
maxcols = 839
maxrows = 679


def readfile(filename):
  try:
    file = bz2.BZ2File(filename + '.bz2', 'r')
  except IOError:
    file = open(filename, 'r')
  contents = file.readlines()
  file.close()
  mat = np.empty((maxrows, maxcols), dtype='int16')
  for row in range(maxrows):
    mat[row] = contents[row + 6].split()
  return mat

# Command line processing.

parser = optparse.OptionParser('fill-h5')
parser.add_option("--prefix", type='string', default='', help='directory where SOLAR_DATA is')
parser.add_option("--compressor", type='string', default='blosc', help='PyTable compressor')
parser.add_option("--complevel", type='int', default=6, help='PyTable compression level')
parser.add_option("--init", action="store_true", default=False, help='initialise a new HDF5 database')
opts, args = parser.parse_args()

if opts.prefix == '':
  print >>sys.stderr, 'must supply prefix'
  sys.exit(1)

# Check that the opts.grid directory exists
if not os.path.isdir(opts.prefix):
    print >>sys.stderr, 'error: %s is not a directory' % opts.prefix
    sys.exit(1)

if opts.init:
  h5file = tables.openFile("nem.h5", mode='w', title="Simulated NEM data")
else:
  h5file = tables.openFile("nem.h5", mode='r+')

f = tables.Filters(complevel=opts.complevel, complib=opts.compressor)
try:
  ghi = h5file.createCArray(h5file.root, 'ghi', tables.Int16Atom(), shape=(maxentries, maxrows, maxcols), filters=f)
  dni = h5file.createCArray(h5file.root, 'dni', tables.Int16Atom(), shape=(maxentries, maxrows, maxcols), filters=f)
except tables.exceptions.NodeError:
  # tables already exist
  ghi = h5file.root.ghi
  dni = h5file.root.dni

print 'pre-filling arrays with nodata values'
chunksz = 10000
nodata = np.empty((chunksz, maxrows, maxcols), dtype='int16')
nodata.fill(-999)
for i in range(0, maxentries, chunksz):
  print i
  if maxentries - i < chunksz:
    dim = maxentries - i
  else:
    dim = chunksz
  ghi[i:i + dim] = nodata[0:dim]
  dni[i:i + dim] = nodata[0:dim]

for type in ['ghi', 'dni']:
  date = startDate
  if type == 'ghi':
    arr = h5file.root.ghi
    prefix = opts.prefix + '/HOURLY_GHI/ALL/solar_ghi_'
  else:
    arr = h5file.root.dni
    prefix = opts.prefix + '/HOURLY_DNI/ALL/solar_dni_'

  hour = 0
  while date < endDate:
    if date.hour == 0:
      print type, date, time.asctime()

    # Skip these; they are known to never exist.
    if date.hour == 12:
      hour = hour + 6
      date = date + datetime.timedelta(hours=6)
      continue

    # Sample filename: solar_dni_20091230_21UT.txt
    filename = prefix + date.strftime("%Y%m%d_%HUT.txt")
    try:
      temp = readfile(filename)
      arr[hour] = temp
    except IOError:
      # File doesn't exist.
      pass

    hour = hour + 1
    date = date + datetime.timedelta(hours=1)
  h5file.flush()
sys.exit(0)
