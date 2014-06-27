# -*- Python -*-
# Copyright (C) 2011, 2014 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Collect statistics on missing, zero and non-zero values in BoM data."""

import sys
import datetime
import numpy as np
import hashlib

maxcols = 839
maxrows = 679
np.set_printoptions(threshold=np.nan)


def readfile(fname):
    """Process a single file."""
    f = open(fname, 'r')

    h = hashlib.sha1()
    h.update(f.read())
    digest = h.hexdigest()
    if digest == 'fc542b04d4fb3993d39324af074c3642ba70b34e' \
       or digest == 'b7bd75f88b8ec8fd4c7ded7cc167d3158b1e5c8b':
        f.close()
        return

    f.seek(0)
    contents = f.readlines()
    f.close()

    for row in range(maxrows):
        values = contents[row + 6].split()

        t1 = [int(v) == '-999' for v in values]
        t2 = [int(v) == '0' for v in values]
        t3 = [int(v) != '0' and int(v) != '-999' for v in values]

        nodata[row] = nodata[row] + t1
        zero[row] = zero[row] + t2
        nonzero[row] = nonzero[row] + t3

date = datetime.date(1998, 1, 1)
lastDate = datetime.date(2010, 3, 31)
lastGMS5 = datetime.date(2001, 6, 30)

nodata = np.zeros((maxrows, maxcols))
zero = np.zeros((maxrows, maxcols))
nonzero = np.zeros((maxrows, maxcols))

print date

while True:
    for hour in range(0, 23):

        # Skip these -- they are known to never exist.
        if hour > 11 and hour < 18:
            continue

        # Sample filename: solar_dni_20091230_21UT.txt
        filename = str(date.year) + '/solar_' + sys.argv[1] + '_' + \
            date.strftime("%Y%m%d") + '_%02d' % hour + 'UT.txt'

        try:
            data = readfile(filename)
        except IOError:
            continue

    if date == lastDate:
        break

    # Skip the dates between GMS5 and GOES-9 service.
    if date == lastGMS5:
        date = datetime.date(2003, 7, 1)
    else:
        date = date + datetime.timedelta(days=1)
    print date

    dataset = sys.argv[1]
    np.savetxt('%s-nodata.txt' % dataset, nodata, fmt='%d', delimiter=',')
    np.savetxt('%s-zero.txt' % dataset, zero, fmt='%d', delimiter=',')
    np.savetxt('%s-nonzero.txt' % dataset, nonzero, fmt='%d', delimiter=',')
