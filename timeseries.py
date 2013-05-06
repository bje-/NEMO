#!/usr/bin/env python26
#
# -*- Python -*-
# Copyright (C) 2011  Marton Hidas
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# Functions for time-series analysis.

import numpy as np
import matplotlib.pyplot as plt


def stats(series, show=False, form='%5.0f'*4):
    """
    Calculate basic statistics on the given time-series. Returns
    the following values in a tuple:
    * mean
    * standard deviation
    * minimum & maximum value
    If 'show' is True, the values are also printed, using the format 
    in 'form'.
    """
    assert series.ndim == 1, 'Need a 1-dimensional array.'
    mean = np.mean(series)
    sdev = np.std(series)
    smin = min(series)
    smax = max(series)
    if show: print form % (mean, sdev, smin, smax)
    return mean, sdev, smin, smax


def lulls(series, threshold, minlength=0):
    """
    Return a tuple of lists, the first containing the indicies into
    the given series at which the value first falls below the given
    threshold, and the second the number of consecutive values that
    are below the threshold. If minlength is given, only lulls of at
    least that length are included.
    """
    start = []
    length = []
    prev = True  # previous status (up/down)
    for i, v in enumerate(series):
        up = (v >= threshold)
        if up == prev: continue   # no change, go to next
        if up:                    # end of lull
            if i-st >= minlength:
                start.append(st)
                length.append(i-st)
        else:                     # start of lull
            st = i
        prev = up
    return start, length


def powerPDF(series, capacity, title='', bins=100, 
             norm_pow=True, norm_prob=True, save=None):
    """
    Calculate and plot probability distribution function for a single
    power time-series. Optionally save the plot to the name file.
    """
    # we get the odd value slightly over capacity, need to cap
    s = np.where(series<=capacity, series, capacity)
    if norm_pow: 
        s /= capacity
        r = (0, 1)
        xlab = 'Power output [fraction of full capacity]'
    else:
        r = (0, capacity)
        xlab = 'Power [MW]  (full capacity %sMW)' % capacity
    if norm_prob:
        ylab1 = 'Probability density'
        ylab2 = 'Cumulative probability'
    else:
        ylab1 = 'Frequency (hours/year)'
        ylab2 = 'Cumulative hours/year'
    # plot PDF in upper panel
    plt.clf()
    plt.subplot(211)
    pdf, bins, _ = plt.hist(s, bins, r, normed=norm_prob, histtype='step')
    plt.title(title)
    plt.ylabel(ylab1)
    # plot cumulative histogram in lower panel
    plt.subplot(212)
    cdf, _, _ = plt.hist(s, bins, cumulative=1, normed=norm_prob, 
                        histtype='step')
    if norm_prob: plt.ylim(0, 1) # otherwise it sometimes goes up to 1.2
    plt.xlabel(xlab)
    plt.ylabel(ylab2)
    # save plot
    if save: plt.savefig(save)
    return bins, pdf, cdf


def variability(series, timescales, capacity=1):
    """
    Analyse variability on a range of timescales.  For each given
    timescale (in units of the index into series), plot a cumulative
    probability distribution of the magnitude of changes over that
    timescale. If capacity is given, give changes as a fraction of it.
    """
    s = np.array(series)/capacity
    ns = len(s)
    plt.clf()
    plt.hold(True)
    for dt in timescales:
        ds = s[dt:] - s[:(ns-dt)]
        plt.hist(ds, bins=100, normed=True, histtype='step')


def ncorr(x, y):
    """
    Normalised cross-correlation function of x and y. Equivalent to:
       numpy.correlate(X, Y, mode='same') / ( X.std() * Y.std() * len(X) )
       where X = x - x.mean()
             Y = y - y.mean()
    Input arrays should be the same length.
    Returns tuple (lags, corr).
    """
    xlen = len(x)
    if xlen <> len(y): print 'ncor WARNING: arrays of different length.'
    X = x - x.mean()
    Y = y - y.mean()
    corr = np.correlate(X, Y, mode='same') / ( X.std() * Y.std() * len(X) )
    lags = np.arange(xlen) - xlen/2
    return lags, corr


def fillgaps(series, gaps=None, time=None):
    """
    Find gaps (zero values) in series and fill them in with
    interpolated values. The gaps argument can specify exactly which
    array indices to fill in (even if not zero), otherwise all zero
    values are filled.  If time array is not given, series is assumed
    to be sampled at uniform time intervals.  Only fills gaps between
    the first and last non-zero value in series.
    """
    # Make a copy of series and set up time array
    s = np.array(series)
    npt = len(s)
    if not time: time = np.arange(npt)
    assert len(time)==npt, 'Time array different size to series!'

    # find gaps
    if gaps<>None:
        # use all other indices as 'good' values
        good = list( set(range(npt)) - set(gaps) )
        good.sort()
    else:
        good = s.nonzero()[0]       # all non-zero values are good
        gaps = (s==0).nonzero()[0]  # the missing values

    if len(gaps)==0: return series  # no gaps

    # calculate interpolated values
    sint = np.interp(time[gaps], time[good], s[good], left=0, right=0) 

    # insert them into the series
    for i, z in enumerate(gaps): s[z] = sint[i]

    changed = sint.nonzero()[0]
    # print 'fillgaps interpolated ', len(changed), ' values'

    return s
