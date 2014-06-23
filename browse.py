#!/usr/bin/env python
#
# -*- Python -*-
# Copyright (C) 2010, 2011, 2014 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

from config import *
from plot import *
from hour import Hour
from latlong import LatLong

import datetime
from datetime import datetime as date
import numpy.ma as ma
import argparse
import socket
import tables
import string
import sys

from pylab import *
import config

parser = argparse.ArgumentParser()
parser.add_argument("--db", type=str, default='nem.h5', help='HDF5 database filename')
args = parser.parse_args()
h5file = tables.openFile(args.db, mode='r')
print h5file
config.ghi = h5file.root.ghi
config.dni = h5file.root.dni
ghi = config.ghi
dni = config.dni
config.maxentries = ghi.shape[0]
config.maxrows = dni.shape[1]
config.maxcols = dni.shape[2]
config.dims = (config.maxrows, config.maxcols)
config.demand = h5file.root.aux.aemo2009.demand


def grid(arr, dt):
    h = Hour(dt)

    # if arr == config.ghi:
    #   missing = config.missing_ghi
    # else:
    #   missing = config.missing_dni

    # Block out these two anomalous grids as nodata:
    # solar_ghi_20021231_20UT.txt
    # solar_ghi_20021231_22UT.txt
    if arr == config.ghi and \
       (h == Hour(date(2002, 12, 31, 20)) or h == Hour(date(2002, 12, 31, 22))):
        t = np.empty(config.dims, dtype='int16')
        t.fill(nodata)
        return ma.masked_equal(t, nodata)
    return ma.masked_equal(arr[h], nodata)


def browse(location):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(('localhost', 4000))
    except:
        print 'connection failed'
        return
    if isinstance(location, tuple):
        # Grid variant.
        locn = LatLong(location)
        query = str(locn)
    else:
        query = str(location)
    query = string.strip(query, '()')
    query = string.replace(query, ' ', '')
    print query
    sock.send(query)
    sock.close()


def timeseries(locn, dataset=config.ghi):
    row = locn.xy()[0]
    col = locn.xy()[1]
    # Get all of the data at this location.
    # data = ma.masked_equal (config.ghi[::,row,col], nodata)
    data = dataset[::, row, col]
    return data


def empty_p(grid):
    """
    Predicate that returns True if the grid contains only nodata values.
    """
    if type(grid) == ma.core.MaskedArray:
        return ma.count_masked(grid) == config.maxrows * config.maxcols
    else:
        return (grid == config.nodata).all()


def find_missing(arr):
    """
    Find missing grids in arr.  Returns two lists: the missing hour
    numbers and a per-hour summary (24 elements).
    """
    missing = []
    for i in range(arr.shape[0] - 2):
        if not empty_p(arr[i]) and empty_p(arr[i + 1]) and \
           not empty_p(arr[i + 2]):
            missing.append(i + 1)
    return missing


def in_date_range_p(hr):
    """
    Predicate function that returns True if hr is in the range of dates
    listed in the BoM metadata documents.
    """
    h1 = Hour(date(1998, 01, 01))
    h2 = Hour(date(2001, 06, 30))
    h3 = Hour(date(2003, 07, 01))
    h4 = Hour(date(2009, 12, 31))

    return (hr >= h1 and hr <= h2) or (hr >= h3 and hr <= h4)

# This is a nice complete grid to use for the nodata mask.
ozmask = grid(config.ghi, 3).mask
