# Copyright (C) 2017 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Utility functions (eg, plotting)."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pint
from matplotlib.patches import Patch
from pandas.plotting import register_matplotlib_converters

from nemo import configfile
from nemo.configfile import configparser

# Future versions of pandas will require us to explicitly register
# matplotlib converters, so do it here now.
register_matplotlib_converters()

# SI units
ureg = pint.UnitRegistry()


def _generator_list(context):
    """Return a list of the generators of interest in this run."""
    return [g for g in context.generators
            if g.region() in context.regions and g.capacity > 0]


def _legend(context):
    """Draw the legend."""
    # ::-1 slicing reverses the list so that the legend appears in merit order
    gens = _generator_list(context)[::-1]
    labels = []
    patches = []

    if len(gens) > 20:
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
    plt.plot(demand.index, demand, color='black', linewidth=3 if spills else 2)

    accum = pd.Series(data=0, index=demand.index)
    prev = accum.copy()
    for gen in _generator_list(context):
        idx = context.generators.index(gen)
        accum += context.generation[idx]
        # Ensure accumulated generation does not exceed demand in any timestep.
        # (Due to rounding, accum can be close to demand.)
        assert all(np.logical_or(accum < demand, np.isclose(accum, demand)))
        plt.plot(accum.index, accum, color='black', linewidth=0.4,
                 linestyle='--')
        plt.fill_between(accum.index, prev, accum,
                         facecolor=gen.patch.get_fc(),
                         hatch=gen.patch.get_hatch())
        prev = accum.copy()
    # Unmet demand is shaded red.
    plt.fill_between(accum.index, accum, demand, facecolor='red')

    if spills:
        prev = demand.copy()
        for gen in list(g for g in context.generators if
                        g.region() in context.regions):
            idx = context.generators.index(gen)
            accum += context.spill[idx]
            plt.plot(accum.index, accum, color='black', linewidth=0.4,
                     linestyle='--')
            plt.fill_between(prev.index, prev, accum,
                             facecolor=gen.patch.get_fc(), alpha=0.3)
            prev = accum.copy()

    plt.gca().set_xlim(xlim)  # set_xlim accepts None
    plt.gca().xaxis_date()
    plt.gcf().autofmt_xdate()

    _, ymax = plt.gca().get_ylim()
    plt.plot(context.unserved.index, [ymax] * len(context.unserved),
             "v", markersize=10, color='red', markeredgecolor='black')


def plot(context, spills=False, filename=None, showlegend=True, xlim=None):
    """Produce a pretty plot of supply and demand."""
    _figure(context, spills, showlegend, xlim)
    if not filename:
        plt.show()
    else:
        plt.savefig(filename)
