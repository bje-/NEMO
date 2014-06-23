#!/usr/bin/python
#
# Collect statistics on missing, zero and non-zero values.

import sys
import datetime
import numpy as np
import hashlib

maxcols = 839
maxrows = 679
np.set_printoptions(threshold=np.nan)


def nodata_p(x):
    return int(x == '-999')


def zero_p(x):
    return int(x == '0')


def nonzero_p(x):
    return int(x != '0' and x != '-999')


def readfile(fname):
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

        t1 = map(nodata_p, values)
        t2 = map(zero_p, values)
        t3 = map(nonzero_p, values)

        nodata[row] = nodata[row] + t1
        zero[row] = zero[row] + t2
        nonzero[row] = nonzero[row] + t3

date = datetime.date(1998, 1, 1)
lastDate = datetime.date(2010, 3, 31)
lastGMS5 = datetime.date(2001, 6, 30)

nodata = np.zeros((maxrows, maxcols))
zero = np.zeros((maxrows, maxcols))
nonzero = np.zeros((maxrows, maxcols))

count = 0
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
    np.savetxt('/home/bje/%s-nodata.txt' % dataset, nodata, fmt='%d', delimiter=',')
    np.savetxt('/home/bje/%s-zero.txt' % dataset, zero, fmt='%d', delimiter=',')
    np.savetxt('/home/bje/%s-nonzero.txt' % dataset, nonzero, fmt='%d', delimiter=',')
