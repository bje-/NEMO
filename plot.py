# -*- Python -*-
# Copyright (C) 2010, 2011 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Useful plotting routines."""

import matplotlib.ticker as ticker
import matplotlib.pyplot as plt
from matplotlib import cm
import numpy as np


def format_date(x, pos=None):
    # pylint: disable=unused-argument
    """
    Format a date for matplotlib.

    >>> format_date(1)
    '01-01-00:30'
    """
    import datetime
    delta = datetime.timedelta(minutes=30 * x)
    t = datetime.datetime(1998, 1, 1) + delta
    return t.strftime('%m-%d-%H:%M')


def plot_timeseries(data, interval=1, style='o-', filename=None):
    """
    Plot a timeseries.

    >>> import os
    >>> plot_timeseries([1,2,3,4], filename='foo.png')
    >>> os.path.isfile('foo.png')
    True
    >>> os.unlink('foo.png')
    """
    plt.clf()
    ind = np.arange(0, len(data) * interval, interval)
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(ind, data, style)
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_date))
    fig.autofmt_xdate()
    if not filename:
        plt.show()
    else:
        plt.savefig(filename)


def plot_distribution(data, label, nbins=48, cumulative=False,
                      heading='Untitled', filename=None, orientation='vertical'):
    """Plot a frequency distribution."""
    fig = plt.figure()
    plt.title(heading)
    ax = fig.add_subplot(111)
    ax.hist(data, nbins, orientation=orientation, cumulative=cumulative)
    if orientation == 'vertical':
        ax.set_xlabel(label)
    else:
        ax.set_ylabel(label)

    if not filename:
        plt.show()
    else:
        plt.savefig(filename)


def plot_grid(data, filename=None, heading='Unspecified', ylabel='W/m$^2$',
              vmin=None, vmax=None, hsv=False, markers=None):
    """Plot a BoM solar irradiance grid."""
    plt.clf()
    plt.imshow(data, vmin=vmin, vmax=vmax)
    plt.axis('off')
    plt.axis('tight')
    plt.title(heading)
    if hsv:
        cb = plt.colorbar(cmap=cm.hsv)
    else:
        cb = plt.colorbar()
    cb.set_label(ylabel)
    if markers is not None:
        for marker in markers:
            ycoord, xcoord = marker.xy()
            plt.plot([xcoord], [ycoord], "y.", markersize=15, color='white')
    if not filename:
        plt.show()
    else:
        plt.savefig(filename)
