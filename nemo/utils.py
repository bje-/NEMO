# Copyright (C) 2017 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Utility functions (eg, plotting)."""

import locale
from datetime import timedelta
from itertools import tee

import matplotlib.pyplot as plt
import pandas as pd
import pint
from matplotlib.patches import Patch
from pandas.plotting import register_matplotlib_converters

from nemo import configfile
from nemo.configfile import configparser

# Needed for currency formatting.
locale.setlocale(locale.LC_ALL, '')

# Default to abbreviated units when formatting.
# Caching is not yet the default.
ureg = pint.UnitRegistry(cache_folder=':auto:')
ureg.default_format = '.2f~P'

# The maximum number of generators before we only show a consolidated
# list of generator types and not individual generator names.
MAX_LEGEND_GENERATORS = 20

# The maximum number of generators before we only show the generator
# traces as a consolidated set (and not indiviudal traces). This
# speeds up the plotting dramatically.
MAX_PLOT_GENERATORS = 50

# Future versions of pandas will require us to explicitly register
# matplotlib converters, so do it here now.
register_matplotlib_converters()


def thousands(value):
    """
    Format a value with thousands separator(s).

    No doctest provided as the result will be locale specific.
    """
    return locale.format_string('%d', value, grouping=True)


def currency(value):
    """
    Format a value into currency with thousands separator(s).

    If there are zero cents, remove .00 for brevity.  No doctest
    provided as the result will be locale specific.
    """
    cents = locale.localeconv()['mon_decimal_point'] + '00'
    return locale.currency(round(value), grouping=True).replace(cents, '')


def _generator_list(context):
    """Return a list of the generators of interest in this run."""
    return [g for g in context.generators
            if g.region() in context.regions and g.capacity > 0]


def _pairwise(lst):
    """Return pairwise elements of a list.

    An implementation of pairwise() appears in the Python 3.10
    itertools module. At some point, we can switch to the standard
    library version and remove this definition.

    >>> list(_pairwise([1,2,3,4,5]))
    [(1, 2), (2, 3), (3, 4), (4, 5)]

    """
    iter1, iter2 = tee(lst)
    next(iter2, None)
    return zip(iter1, iter2)


def _legend(context):
    """Draw the legend."""
    # ::-1 slicing reverses the list so that the legend appears in merit order
    gens = _generator_list(context)[::-1]
    labels = []
    patches = []

    if len(gens) > MAX_LEGEND_GENERATORS:
        unique = []
        for gen in gens:
            if type(gen) not in unique:
                unique.append(type(gen))
                labels.append(gen.__class__.__name__)
                patches.append(gen.patch)
    else:
        for gen in gens:
            capacity = (gen.capacity * ureg.MW).to_compact()
            labels.append(gen.label + f' ({capacity:.2f~P})')
            patches.append(gen.patch)

    red_patch = Patch(facecolor='red', edgecolor='black')
    legend = plt.figlegend([red_patch] + patches,
                           ['unserved'] + labels,
                           loc='upper right')
    plt.setp(legend.get_texts(), fontsize='small')


def _plot_areas(context, category, prev=None, alpha=None):
    assert category in ['generation', 'spill']

    demand = context.demand.sum(axis=1)
    timeseries = getattr(context, category)
    genlist = _generator_list(context)
    numgens = len(genlist)

    accum = prev.copy()
    for gen, nextgen in _pairwise(genlist + [None]):
        index = context.generators.index(gen)
        accum += timeseries[index]
        if type(gen) is type(nextgen) and numgens > MAX_PLOT_GENERATORS:
            # don't plot individual traces lines when there are too
            # many generators
            continue
        plt.plot(accum.index, accum, color='black', linewidth=0.4,
                 linestyle='--')
        plt.fill_between(prev.index, prev, accum,
                         facecolor=gen.patch.get_fc(), alpha=alpha)
        prev = accum.copy()

    # Unmet demand is shaded red.
    if category == 'generation':
        plt.fill_between(accum.index, accum, demand, facecolor='red')


def _figure(context, spills, showlegend, xlim):
    """Provide a helper function for plot() to faciltiate testing."""
    # aggregate demand
    demand = context.demand.sum(axis=1)

    plt.clf()
    plt.ylabel('Power (MW)')
    try:
        title = configfile.get('plot', 'title')
    except (configparser.NoSectionError, configparser.NoOptionError):
        title = 'Energy balance'
    try:
        title += '\n' + configfile.get('plot', 'subtitle')
    except (configfile.configparser.NoSectionError,
            configfile.configparser.NoOptionError):
        pass
    plt.suptitle(title)

    if showlegend:
        _legend(context)

    # Plot demand first.
    plt.plot(demand.index, demand, color='black', linewidth=2)

    # Plot generation.
    zeros = pd.Series(data=0, index=demand.index)
    _plot_areas(context, 'generation', prev=zeros)

    # Optionally plot spills.
    if spills:
        _plot_areas(context, 'spill', prev=demand, alpha=0.3)

    plt.gca().set_xlim(xlim)  # set_xlim accepts None
    plt.gca().xaxis_date()
    plt.gcf().autofmt_xdate()

    _, ymax = plt.gca().get_ylim()
    plt.plot(context.unserved.index, [ymax] * len(context.unserved),
             "v", markersize=10, color='red', markeredgecolor='black')


def plot(context, spills=False, filename=None, showlegend=True, xlim=None):
    """Produce a pretty plot of supply and demand."""
    if xlim is None:
        starttime = context.demand.index[0]
        ninety_days = 24 * 90
        if context.timesteps() > ninety_days:
            endtime = starttime + timedelta(days=90)
        else:
            endtime = context.demand.index[-1]
            timerange = (starttime, endtime)
    else:
        timerange = xlim

    _figure(context, spills, showlegend, timerange)
    if not filename:
        plt.show()
    else:
        plt.savefig(filename)
