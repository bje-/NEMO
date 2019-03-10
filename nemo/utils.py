# Copyright (C) 2017 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Utilities eg. plotting."""

import pandas as pd
import numpy as np

from matplotlib.patches import Patch
import matplotlib.pyplot as plt
from nemo import configfile
from nemo.configfile import configparser
from nemo.anywh import anyWh


def _generator_list(context):
    """Return a list of the generators of interest in this run."""
    return [g for g in context.generators if g.region() in context.regions and g.capacity > 0]


def _legend(context):
    """Draw the legend."""

    # ::-1 slicing reverses the list so that the legend appears in "merit order".
    gens = _generator_list(context)[::-1]
    labels = []
    patches = []

    if len(gens) > 20:
        unique = []
        for g in gens:
            if type(g) not in unique:  # pylint: disable=unidiomatic-typecheck
                unique.append(type(g))
                # Replace the generator label with its class.
                genclass = str(type(g)).strip('<>').replace("'", "")
                labels.append(genclass.split()[1].split('.')[1])
                patches.append(g.patch)
    else:
        for g in gens:
            labels.append(g.label + ' (%s)' % anyWh(g.capacity, 'W'))
            patches.append(g.patch)

    legend = plt.figlegend([Patch('black', 'red')] + patches,
                           ['unserved'] + labels,
                           'upper right')
    plt.setp(legend.get_texts(), fontsize='small')


def plot(context, spills=False, filename=None, showlegend=True, xlim=None):
    """Produce a pretty plot of supply and demand."""
    # aggregate demand
    demand = context.demand.sum(axis=1)

    plt.clf()
    plt.ylabel('Power (MW)')
    try:
        title = configfile.get('plot', 'title')
    except (configparser.NoSectionError, configparser.NoOptionError):
        title = 'Supply/demand balance'
    try:
        title += '\n' + configfile.get('plot', 'subtitle')
    except (configfile.configparser.NoSectionError, configfile.configparser.NoOptionError):
        pass
    plt.suptitle(title)

    if showlegend:
        _legend(context)

    # Plot demand first.
    plt.plot(demand.index, demand, color='black', linewidth=3 if spills else 2)

    accum = pd.Series(data=0, index=demand.index)
    prev = accum.copy()
    for g in _generator_list(context):
        idx = context.generators.index(g)
        accum += context.generation[idx]
        # Ensure accumulated generation does not exceed demand in any timestep.
        # (Due to rounding, accum can be close to demand.)
        assert all(np.logical_or(accum < demand, np.isclose(accum, demand)))
        plt.plot(accum.index, accum, color='black', linewidth=0.5)
        plt.fill_between(accum.index, prev, accum,
                         facecolor=g.patch.get_fc(),
                         hatch=g.patch.get_hatch())
        prev = accum.copy()
    # Unmet demand is shaded red.
    plt.fill_between(accum.index, accum, demand, facecolor='red')

    if spills:
        prev = demand.copy()
        for g in list(g for g in context.generators if g.region() in context.regions):
            idx = context.generators.index(g)
            accum += context.spill[idx]
            plt.plot(accum.index, accum, color='black', linewidth=0.5)
            plt.fill_between(prev.index, prev, accum, facecolor=g.patch.get_fc(), alpha=0.3)
            prev = accum.copy()

    plt.gca().set_xlim(xlim)  # set_xlim accepts None
    plt.gca().xaxis_date()
    plt.gcf().autofmt_xdate()

    _, ymax = plt.gca().get_ylim()
    plt.plot(context.unserved.index, [ymax] * len(context.unserved),
             "yv", markersize=10, color='red', markeredgecolor='black')

    if not filename:
        plt.show()  # pragma: no cover
    else:
        plt.savefig(filename)
