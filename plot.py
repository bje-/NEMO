# -*- Python -*-
# Copyright (C) 2010, 2011 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

from pylab import *
import matplotlib.ticker as ticker


def format_date(x, pos=None):
    import datetime
    delta = datetime.timedelta(minutes=30 * x)
    t = datetime.datetime(1998, 1, 1) + delta
    return t.strftime('%m-%d-%H:%M-')


def plot_timeseries(data, interval=1, style='o-', filename=None):
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
      savefig(filename)


def plot_distribution(data, label, nbins=48, cumulative=False,
                      heading='Untitled', filename=None, orientation='vertical'):
  fig = figure()
  title(heading)
  ax = fig.add_subplot(111)
  n, bins, patches = ax.hist(data, nbins,
                             orientation=orientation, cumulative=cumulative)
  if orientation == 'vertical':
    ax.set_xlabel(label)
  else:
    ax.set_ylabel(label)

  if not filename:
    show()
  else:
    savefig(filename)


def plot_grid(data, filename=None, heading='Unspecified', ylabel='W/m$^2$',
              vmin=None, vmax=None, hsv=False, markers=[]):
  clf()
  imshow(data, vmin=vmin, vmax=vmax)
  axis('off')
  axis('tight')
  title(heading)
  if hsv:
      cb = colorbar(cmap=cm.hsv)
  else:
      cb = colorbar()
  cb.set_label(ylabel)
  for marker in markers:
    ycoord, xcoord = marker.xy()
    plot([xcoord], [ycoord], "y.", markersize=15, color='white')
  if not filename:
    show()
  else:
    savefig(filename)
