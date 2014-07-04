# Copyright (C) 2011, 2014 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Load a BoM AWS data set into the HDF5 database under /aux."""

import argparse
import tables

parser = argparse.ArgumentParser()
parser.add_argument("--db", type=str, default='nem.h5', help='HDF5 database filename')
parser.add_argument("--compressor", type=str, default='blosc', help='PyTable compressor')
parser.add_argument("--complevel", type=int, default=6, help='PyTable compression level')
args = parser.parse_args()

h5file = tables.openFile(args.db, mode="r+")


class WeatherStation(tables.IsDescription):

    """Record format for weather stations."""

    stationid = tables.UInt32Col(pos=0)
    latitude = tables.Float32Col(pos=1)
    longitude = tables.Float32Col(pos=2)
    state = tables.StringCol(3, pos=3)
    name = tables.StringCol(40, pos=4)
    raincode = tables.StringCol(4, pos=5)


class WeatherObservation(tables.IsDescription):

    """Record format for weather observations."""

    stationid = tables.UInt32Col(pos=0)
    year = tables.UInt16Col(pos=1)
    month = tables.UInt8Col(pos=2)
    day = tables.UInt8Col(pos=3)
    hour = tables.UInt8Col(pos=4)
    minute = tables.UInt8Col(pos=5)
    drybulb = tables.Float32Col(pos=6, dflt=-999)
    wetbulb = tables.Float32Col(pos=7, dflt=-999)
    dewpoint = tables.Float32Col(pos=8, dflt=-999)
    relhumidity = tables.Int8Col(pos=9, dflt=-99)
    windspd = tables.Float32Col(pos=10, dflt=-999)
    winddir = tables.Int16Col(pos=11, dflt=-99)
    windgust = tables.Float32Col(pos=12, dflt=-999)
    mslp = tables.Float32Col(pos=13, dflt=-999)
    slp = tables.Float32Col(pos=14, dflt=-999)
    flag = tables.Int8Col(pos=15, dflt=-1)

try:
    h5file.createGroup(h5file.root, 'aux')
except tables.exceptions.NodeError:
    pass

filt = tables.Filters(complevel=args.complevel, complib=args.compressor)
try:
    table = h5file.createTable('/aux', 'weather', WeatherObservation,
                               "BoM weather observations", filters=filt)
except tables.exceptions.NodeError:
    table = h5file.root.aux.weather
obs = table.row

f = open('all.txt', 'r')
for count, line in enumerate(f):
    # hm, 48237,2010,01,01,00,00, 20.6, 19.3, 18.5, 88,  4.6, 50,  6.2,1012.1, 987.1, 1,#
    # Basic sanity check.
    if line[0:3] != 'hm,':
        print 'Skipping suspicious line %d: %s' % (count, line)
        continue

    if count % 10000 == 0:
        print '%d done' % count

    fields = line.split(',')
    obs['stationid'] = int(fields[1])
    obs['year'] = int(fields[2])
    obs['month'] = int(fields[3])
    obs['day'] = int(fields[4])
    obs['hour'] = int(fields[5])
    obs['minute'] = int(fields[6])
    if fields[7].strip():
        obs['drybulb'] = float(fields[7])
    if fields[8].strip():
        obs['wetbulb'] = float(fields[8])
    if fields[9].strip():
        obs['dewpoint'] = float(fields[9])
    if fields[10].strip():
        obs['relhumidity'] = float(fields[10])
    if fields[11].strip():
        obs['windspd'] = float(fields[11])
    if fields[12].strip():
        obs['winddir'] = int(fields[12])
    if fields[13].strip():
        obs['windgust'] = float(fields[13])
    if fields[14].strip():
        obs['mslp'] = float(fields[14])
    if fields[15].strip():
        obs['slp'] = float(fields[15])
    if fields[16].strip():
        obs['flag'] = float(fields[16])
    obs.append()
f.close()
table.flush()

try:
    table = h5file.createTable('/aux', 'wstations', WeatherStation,
                               "BoM weather stations", filters=filt)
except tables.exceptions.NodeError:
    table = h5file.root.aux.stations
stn = table.row

print 'populating weather stations'
f = open('stations.txt', 'r')
for count, line in enumerate(f):
    # st,046012,46  ,WILCANNIA AERODROME AWS                 ,01/2000,       ,-31.5194, 143.3850,GPS            ,NSW, ...
    # Basic sanity check.
    if line[0:3] != 'st,':
        print 'Skipping suspicious line %d: %s' % (count, line)
        continue

    if count % 100 == 0:
        print '%d done' % count

    fields = line.split(',')
    stn['stationid'] = int(fields[1])
    stn['raincode'] = fields[2].strip()
    stn['name'] = fields[3].strip()
    stn['latitude'] = float(fields[6])
    stn['longitude'] = float(fields[7])
    stn['state'] = fields[9].strip()
    stn.append()
f.close()

h5file.flush()
