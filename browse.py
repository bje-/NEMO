# Copyright (C) 2010, 2011, 2014 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""A tool to browse the gridded solar database."""

from datetime import datetime as date
import numpy.ma as ma
import argparse
import tables
import numpy as np

from hour import Hour
import config

parser = argparse.ArgumentParser()
parser.add_argument("--db", type=str, default='nem.h5', help='HDF5 database filename')
args = parser.parse_args()

h5file = tables.openFile(args.db, mode='r')
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
    """Return the grid for hour `dt' in the dataset `arr' (GHI or DNI)."""
    h = Hour(dt)

    # Block out these two anomalous grids as nodata:
    # solar_ghi_20021231_20UT.txt
    # solar_ghi_20021231_22UT.txt
    if arr == config.ghi and \
       (h == Hour(date(2002, 12, 31, 20)) or h == Hour(date(2002, 12, 31, 22))):
        t = np.empty(config.dims, dtype='int16')
        t.fill(config.nodata)
        return ma.masked_equal(t, config.nodata)
    return ma.masked_equal(arr[h], config.nodata)


def timeseries(locn, dataset=config.ghi):
    """Get all of the data at location `locn'."""
    row, col = locn.xy()
    data = dataset[::, row, col]
    return data


def empty_p(grd):
    """True if the grid `grd' contains only nodata values."""
    if type(grd) == ma.core.MaskedArray:
        return ma.count_masked(grd) == config.maxrows * config.maxcols
    else:
        return (grd == config.nodata).all()


def find_missing(arr):
    """Find missing grids in `arr'.

    Returns two lists: the missing hour numbers and a per-hour summary
    (24 elements).
    """
    missing = []
    for i in range(arr.shape[0] - 2):
        if not empty_p(arr[i]) and empty_p(arr[i + 1]) and \
           not empty_p(arr[i + 2]):
            missing.append(i + 1)
    return missing


if __name__ == '__main__':
    import doctest
    doctest.testmod()
