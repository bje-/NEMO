#!/usr/bin/env python
#
# -*- Python -*-
# Copyright (C) 2011 Marton Hidas
# Copyright (C) 2011, 2012 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

import numpy as np
import timeseries as ts
from generators import Generator, Wind
from latlong import LatLong
from nem import h5file
from datetime import datetime
from hour import Hour
Hour.origin = datetime(2010,1,1)  # reset time origin

# set up module parameters
gentable = h5file.root.aux.windfarmperf2010.data
interval = 5  # averaging interval for time-series (min)
_tsStore = {}
verbose = False

# Create time array and calculate index ranges for seasonal time-series
tslen = 365 * 24 * 60/interval
timeh = np.arange(tslen) * interval/60.
timed = timeh / 24.
q = tslen/4
summer = range(q)
autumn = range(q, 2*q)
winter = range(2*q, 3*q)
spring = range(3*q, tslen)

# class to represent a wind farm
class WindFarm(Wind):
    "Class to represent a single wind farm"
    def __init__(self, duid, name, region, latitude, longitude, capacity):
        Generator.__init__(self, region, capacity, label='wind')
        self.duid = duid
        self.name = name
        self.location = LatLong((latitude, longitude))
        self.generation = None
        self.interval = None
        self.startgen = -1

    def __str__(self):
        return '%s, %s (%.0f MW)' % (self.name, self.region, self.capacity)

    def info(self):
        "Return all basic info about the wind farm in a tuple"
        return (self.duid, self.name, self.region, self.location, 
                self.capacity, self.startgen, self.interval)

    def setGen(self, generation, interval):
        "Set generation time-series (and sampling interval) in the object."
        self.generation = generation
        self.interval = interval
        for i in range(len(generation)):
            if generation[i] > 0: break
        self.startgen = i


def load (regions = ['NSW', 'QLD', 'SA', 'TAS', 'VIC']):
    # read in windfarm info from file
    global farms
    global nfarms
    global farmIds
    farms = {}
    farmIds = []
    f = open('/home/bje/unsw/thesis/data/windfarm.info.csv')
    for line in f:
        if line[0] in ('#', '\n'): continue
        [duid, name, reg, lat, lon, cap, cf] = line.split(',')
        # Only pick out wind farms in the selected regions.
        if reg not in regions: continue
        duid = duid.upper()
        name = name.replace('Wind Farm', 'WF')
        wf = WindFarm(duid, name, reg, float(lat), float(lon), float(cap))
        farms[duid] = wf
        farmIds.append(duid)
        if verbose: print wf
    farmIds =  tuple(farmIds)   # tuple of wind-farm DUIDS (same order as in file)
    nfarms = len(farmIds)

def generation (duid=None, interval=interval):
    """
    As for gen_all() but returns a single time-series, which is the
    sum over all wind farms, or (if duid is given) the output of a
    single wind farm.
    """
    # use gen_all() to get all the time-series
    series_all = gen_all(interval)
    # extract what we want
    if duid:
        fi = farmIds.index(duid)
        return series_all[fi]
    else:
        return series_all.sum(0)


def gen_all(interval=interval):
    """
    Reads the data from windfarmperformance.info for 2010 and returns
    a 2-d array containing the time-series of average power (MW)
    supplied to the NEM by each wind farm in intevals of the given
    length (minutes). Negative power values are counted as zero.
    """
    if interval % 5 > 0 and verbose: 
        print 'WARNING: Results are only accurate if interval is a multiple of 5!'
    global _tsStore
    if _tsStore.has_key(interval):       # check if we've worked this out before
        return _tsStore[interval]
    t0 = gentable[0]['time']
    nslot = (gentable[-1]['time'] - t0) / (60*interval) + 1
    series = np.zeros((nfarms, nslot))
    unknown = []
    for row in gentable.where('power>0'):
        if row['duid'] in unknown: continue
        try: fi = farmIds.index(row['duid'])
        except: 
            if verbose:
                print 'WARNING: unknown DUID: ', row['duid']
            unknown.append(row['duid'])
            continue
	# Time minus starting time divided by averaging interval
        slot = (row['time'] - t0) / (60*interval)
        # MWh contributed to the current time slot
        series[fi, slot] += row['power'] / 12.
    # now convert series from MWh in interval to average power
    series /= interval/60.

    # interpolate over gaps in data (intervals where total power = 0)
    gaps = np.where (series.sum (axis=0) == 0)[0]
    for f in range(nfarms):
        series[f] = ts.fillgaps(series[f], gaps)

    # cache output within module for fast future reference
        # _tsStore[interval] = series

    # store generation timeseries within each windfarm object (also sets index of first non-zero generation)
    for fi, duid in enumerate(farmIds):
        farms[duid].setGen(series[fi], interval)

    return series


def wind_farm_p (duid):
    """
    Return True if the DUID is a wind farm.
    The full DUID list is taken from the windfarmperformance.info website.
    """
    return duid in farmIds


#### Print some stats

def _statline(series, duid, region, cap, start, lull_lim, lull_len, form):
    s = series[start:]
    mean, sdev, lo, hi = ts.stats(s)
    lst, llen = ts.lulls(s, cap*lull_lim, lull_len)
    if llen:
        lmax = max(llen)
        lnum = len(llen)
    else: 
        lmax, lnum = 0, 0
    print form % (duid, region, cap, mean/cap, sdev/cap, start, lmax, lnum) 

def print_stats(allseries, lull_lim=0.2, lull_len=1):
    print '%10s'*8 % ('DUID', 'REGION', 'CAPACITY', 'MEAN/CAP', 'STD/CAP', 'START', 'LULL_MAX', 'LULL_NUM')
    form  = '%10s%10s %9d %9.2f %9.2f %9d %9d %9d'
    totalcapacity = 0
    for fi, duid in enumerate(farmIds):
        (dd, name, region, loc, cap, start, _) = farms[duid].info()
        totalcapacity += cap
        _statline(allseries[fi], duid, region, cap, start, lull_lim, lull_len, form)
    # work out same stats for the total power time-series    
    print '-'*80
    _statline(allseries.sum(0), 'TOTAL', '', totalcapacity, 0, lull_lim, lull_len, form)


### Work out and plot PDFs

def PDFall(allseries, bins=100, save=True):
    """
    Calculate and plot probability distribution functions for all wind
    farms, saving the plots to individual files.
    """
    capsum = 0
    pdf = []
    cdf = []
    for fi, duid in enumerate(farmIds):
        (dd, name, reg, loc, cap, start, _) = farms[duid].info()
        series = allseries[fi, start:]
        capsum += cap
        title = '%s, %s  (%dMW)' % (name, reg, cap)
        if save: save = 'pdf_wind_%s.pdf' % duid.lower()
        bins, p, c = ts.powerPDF(series, cap, title, bins, save=save)
        pdf.append(p)    # save PDFs for return value
        cdf.append(c)
    if save: save = 'pdf_wind_total.pdf'
    ts.powerPDF(allseries.sum(0), capsum, 
             'Total wind power (Capacity %dMW)' % capsum,
             bins, save=save)
    pdf = np.array(pdf)
    cdf = np.array(cdf)
    return bins, pdf, cdf


## Look at cross-correlations between time-series

def cor_all(allseries):
    """
    For each pair of time-series, find the maximum cross-correlation
    value and corresponding lag.
    """
    nser, npt = allseries.shape
    cortab = np.zeros((nser,nser))
    for i in range(nser):
        print farms[farmIds[i]].name
        for j in range(i):
            lag, cor = ts.ncorr(allseries[i], allseries[j])
            m = cor.argmax()
            cortab[i,j] = cor[m]
            cortab[j,i] = lag[m] * interval/60.
            # print '\t%s - max:%.2f  lag:%.2f hr' % (farms[farmIds[j]].name, cor[m], cortab[j,i])
            #print 

    return cortab


def cor_print(cortab):
    "Print results from cor_all()"
    nf, nf = cortab.shape
    assert nf==nfarms 
    print '%35s  %8s  %8s' % (' ', 'max corr', 'lag')
    for i, fi in enumerate(farmIds):
        print '%s, %s correlated with' % (farms[fi].name, farms[fi].region)
        for j in range(i+1, nfarms):
            print '%30s,%4s  %8.2f  %8.2f hr' % (farms[farmIds[j]].name, farms[farmIds[j]].region, cortab[i,j], cortab[j,i])
        print 
    
    return

# Load wind farms from all regions by default.
load ()
