# nem.py: a Python National Electricity Market simulation
#
# -*- Python -*-
# Copyright (C) 2011, 2012 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

import re
import string
import numpy as np
import tables

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.patches import Patch

import regions
import generators
from generators import PV, Wind, CST, PumpedHydro, Hydro, Biofuel

regions.count = 0
generators.count = 0
hours = 8760
twh = 1000 * 1000

h5file = tables.openFile('/home/bje/unsw/thesis/data/nem.h5', mode='r')
pvdata = '/home/bje/Windows/sam-pv.csv'
cstdata = '/home/bje/Windows/sam-cst-15h-sm2.5.csv'
fielddata = '/home/bje/Windows/field.csv'

capfactor = {CST: 0.60, Wind: 0.30, PV: 0.16, Hydro: None, PumpedHydro: None, Biofuel: None}
energy_fraction = {CST: 0.40, Wind: 0.30, PV: 0.10, Hydro: None, PumpedHydro: None, Biofuel: None}
popns = {'SE Qld': 2.97, 'Canberra': 0.358, 'Sydney': 4.58, 'Melbourne': 4.08, 'Adelaide': 1.20}

demand = h5file.root.aux.aemo2010.demand[::]
# Demand is in 30 minute intervals.
assert demand.shape == (5, 2 * hours)
# For hourly, average half-hours n and n+1.
regional_demand = (demand[::, ::2] + demand[::, 1::2]) / 2
del demand


# Read BoM station data.
def _import_bom_stations(filename):
    f = open(filename)
    stns = {}
    for line in f:
        fields = line.split(',')
        stncode = fields[1]
        state = fields[9].strip()
        location = fields[3].strip()
        location = string.capwords(location)
        location = string.replace(location, 'Aws', 'AWS')
        stns[stncode] = (location, state)
    f.close()
    return stns
stns = _import_bom_stations('Stations.txt')


def default_generation_mix():
    result = []
    # This list is in merit order.
    for g in [PV, Wind, CST, Hydro, PumpedHydro, Biofuel]:
        if capfactor[g] is not None:
            capacity = \
                (regional_demand.sum() * energy_fraction[g]) / (capfactor[g] * hours)
        if g == PumpedHydro:
            # QLD: Wivenhoe (http://www.csenergy.com.au/content-%28168%29-wivenhoe.htm)
            result.append(PumpedHydro(regions.qld, 500, 5000, label='QLD1 pumped-hydro'))
            # NSW: Tumut 3 (6x250), Bendeela (2x80) and Kangaroo Valley (2x40)
            result.append(PumpedHydro(regions.nsw, 1740, 15000, label='NSW1 pumped-hydro'))
        elif g == Hydro:
            # Ignore the one small hydro plant in SA.
            result.append(Hydro(regions.tas, 2740, label=regions.tas.id + ' hydro'))
            result.append(Hydro(regions.nsw, 1160, label=regions.nsw.id + ' hydro'))
            result.append(Hydro(regions.vic, 960, label=regions.vic.id + ' hydro'))
        elif g == Biofuel:
            # 24 GW biofuelled gas turbines (fixed)
            # distribute 24GW of biofuelled turbines across all regions
            # the region list is in order of approximate demand
            for r in regions.all:
                result.append(Biofuel(r, 24000 / regions.numregions, label=r.id + ' GT'))
        elif g == PV:
            # Calculate proportions across major cities.
            pv = {}
            total_popn = sum(popns.values())
            for city in popns.keys():
                pv[city] = (popns[city] / total_popn) * capacity
            result.append(g(regions.vic, pv['Melbourne'], pvdata, 0, label='Melbourne PV'))
            result.append(g(regions.nsw, pv['Sydney'], pvdata, 1, label='Sydney PV'))
            result.append(g(regions.qld, pv['SE Qld'], pvdata, 2, label='SE Qld PV'))
            result.append(g(regions.nsw, pv['Canberra'], pvdata, 3, label='Canberra PV'))
            result.append(g(regions.sa, pv['Adelaide'], pvdata, 4, label='Adelaide PV'))
        elif g == CST:
            line1 = open(cstdata).readline()
            # Pull out all of the station numbers, in column order.
            sites = re.compile(r'\d{6}').findall(line1)
            # Divide evenly among locations.
            capacity /= len(sites)
            for i, site in enumerate(sites):
                aws, state = stns[site]
                region = regions.find(state)
                result.append(CST(region, capacity, 2.5, 15, fielddata, i, label=aws + ' SCST'))
        elif g == Wind:
            # 25% of NEM wind is in Vic, 59% in SA, 9% in NSW and 7% in Tas.
            result.append(g(regions.vic, capacity * 0.25, h5file, label='VIC wind'))
            result.append(g(regions.sa, capacity * 0.59, h5file, label='SA wind'))
            result.append(g(regions.nsw, capacity * 0.09, h5file, label='NSW wind'))
            result.append(g(regions.tas, capacity * 0.07, h5file, label='TAS wind'))
        else:
            raise(ValueError)

    # You can't modify these capacities.
    for g in result:
        if g.__class__ is Hydro or g.__class__ is PumpedHydro:
            g.setters = []

    return result


# Context objects are used throughout this module.
class Context:
    def __init__(self):
        self.verbose = False
        self.regions = regions.all
        # NEM standard: 0.002% unserved energy
        self.relstd = 0.002
        self.generators = default_generation_mix()
        self.demand = regional_demand.copy()
        self.spilled_energy = 0
        self.unserved = []
        self.unserved_energy = 0
        self.unserved_hours = 0
        self.unserved_percent = 0

    def demand_twh(self):
        "Return the total annual demand in TWh"
        return self.demand.sum() / twh

    def __str__(self):
        s = 'Regions: ' + str(self.regions) + '\n'
        if self.verbose:
            s += 'Generators:' + '\n'
            for g in self.generators:
                s += '\t' + str(g)
                if g.summary(self.costs) is not None:
                    s += '\n\t   ' + g.summary(self.costs) + '\n'
                else:
                    s += '\n'
        s += 'Demand energy: %.1f TWh\n' % (self.demand.sum() / twh)
        s += 'Spilled energy: %.1f TWh\n' % (self.spilled_energy / twh)

        if self.unserved_energy == 0:
            s += 'No unserved energy'
        elif self.unserved_energy > 0:
            s += 'Unserved energy: %.3f%%' % self.unserved_percent + '\n'
            if self.unserved_percent > self.relstd:
                s += 'WARNING: NEM reliability standard exceeded\n'
            s += 'Unserved total hours: ' + str(self.unserved_hours) + '\n'
            s += 'min, max shortfalls: ' + str(self.shortfalls)

        if self.spilled_energy > 0:
            try:
                s += '\n' + 'spilled hours = ' + str((self.spill.sum(axis=0) > 0).sum())
            except AttributeError:
                pass
        return s


def _path_in_regions_p(path, context):
    print 'path_in_regions_p:', path
    if path is []:
        return True
    for (src, dest) in path:
        if src not in context.regions or dest not in context.regions:
            return False
    return True


def _sim(context, starthour, endhour):
    genlookup = {}
    for i, g in enumerate(context.generators):
        # reset generator internal state
        g.reset()
        genlookup[g] = i

    connections = {}
    c = regions.connections
    for r in context.regions:
        connections[r] = []
        for (src, dest), path in zip(c.keys(), c.values()):
            if src is r and dest in context.regions and regions.in_regions_p(path, context.regions):
                connections[r].append(path)
        connections[r].sort()
        connections[r].sort(key=lambda s: len(s))

    assert context.demand.shape == (5, hours)
    context.generation = np.zeros((len(context.generators), hours))
    context.spill = np.zeros((len(context.generators), hours))
    context.exchanges = np.zeros((hours, regions.numregions, regions.numregions))
    demand_copy = context.demand.copy()

    # Zero out regions we don't care about.
    for r in [r for r in regions.all if r not in context.regions]:
        demand_copy[r] = 0

    # Extract generators in the regions of interest.
    gens = [g for g in context.generators if g.region in context.regions]

    for hr in xrange(starthour, endhour):
        hour_demand = demand_copy[::, hr]
        residual_hour_demand = hour_demand.sum()

        if context.verbose:
            print 'hour', hr, 'demand:', hour_demand

        # Dispatch power from each generator in merit order
        for g in gens:
            gidx = genlookup[g]
            gen, context.spill[gidx, hr] = g.step(hr, residual_hour_demand)
            context.generation[gidx, hr] = gen
            if not gen:
                continue

            residual_hour_demand -= gen
            # residual can go below zero due to rounding
            assert residual_hour_demand > -0.1
            residual_hour_demand = max(0, residual_hour_demand)

            if context.verbose:
                print 'GENERATOR:', g, 'generation =', context.generation[gidx, hr], 'spill =', \
                    context.spill[gidx, hr], 'residual demand =', residual_hour_demand

            # distribute the generation across the regions (local region first)

            paths = connections[g.region]
            if context.verbose:
                print 'PATHS:', paths

            for path in paths:
                if not gen:
                    break

                rgn = g.region if len(path) is 0 else path[-1][-1]
                rgnidx = rgn._num
                transfer = gen if gen < hour_demand[rgnidx] else hour_demand[rgnidx]

                if transfer:
                    if context.verbose:
                        print 'dispatch', int(transfer), 'to', rgn
                    if rgn is g.region:
                        context.exchanges[hr, rgnidx, rgnidx] += transfer
                    else:
                        # dispatch to another region
                        for src, dest in path:
                            context.exchanges[hr, src, dest] += transfer
                            if context.verbose:
                                print src, '->', dest, '(%d)' % transfer
                                assert regions.direct_p(src, dest)
                    hour_demand[rgnidx] -= transfer
                    gen -= transfer

                if context.spill[gidx, hr]:
                    for other in [g2 for g2 in gens if g2 is not g and g2.storage_p]:
                        stored = other.store(hr, context.spill[gidx, hr])
                        # show the energy transferred, not stored (this is where the loss is handled)
                        if context.verbose:
                            print 'STORE:', g.region, '->', other.region, '(%.1f)' % stored
                        for src, dest in regions.path(g.region, other.region):
                            context.exchanges[hr, src, dest] += stored
                        context.spill[gidx, hr] -= stored
                        assert context.spill[gidx, hr] >= 0

        if context.verbose:
            if (hour_demand > 0).any():
                print 'hour', hr, 'residual:', hour_demand
    return context


def plot(context, spills=False, filename=None, xlimit=None):
    "Produce a pretty plot of supply and demand."
    gen = context.generation
    spill = context.spill
    # aggregate demand
    demand = context.demand.sum(axis=0)

    genlookup = {}
    for i, g in enumerate(context.generators):
        genlookup[g] = i

    fig = plt.figure()
    plt.ylabel('MW')
    plt.xlabel('Hour')
    title = 'NEM supply/demand for 2010\nRegions: %s' % str(context.regions)
    plt.suptitle(title)
    plt.xlim(0, hours)
    ymax = (spill.max() + demand.max()) * 1.05 if spills else demand.max() * 1.05
    plt.ylim(0, ymax)

    if xlimit is not None:
        plt.xlim(xlimit)

    # The ::-1 slicing reverses the 'gens' list so that the legend
    # appears in "merit order".
    f = plt.figlegend([Patch('black', 'red')] +
                      [g.patch for g in context.generators[::-1] if g.region in context.regions],
                      ['unserved'] + [g.label for g in context.generators[::-1] if g.region in context.regions],
                      'upper right')
    plt.setp(f.get_texts(), fontsize='small')

    ax = fig.add_subplot(111)
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(_format_date))
    fig.autofmt_xdate()

    # Plot demand first.
    xdata = np.arange(hours)
    plt.plot(xdata, demand, color='black', linewidth=2)
    if spills:
        peakdemand = np.empty_like(demand)
        peakdemand.fill(demand.max())
        plt.plot(xdata, peakdemand, color='black', linestyle='dashed')

    accum = np.zeros(hours)
    prev = accum.copy()
    for g in [g for g in context.generators if g.region in context.regions]:
        accum += context.generation[genlookup[g]]
        assert(np.trunc(accum) > np.trunc(demand)).sum() == 0
        plt.plot(xdata, accum, color='black', linewidth=0.5)
        plt.fill_between(xdata, prev, accum, facecolor=g.patch.get_fc())
        prev = accum.copy()
    # Unmet demand is shaded red.
    plt.fill_between(xdata, accum, demand, facecolor='red')

    if spills:
        prev = demand.copy()
        for g in [g for g in context.generators if g.region in context.regions]:
            accum += spill[genlookup[g]]
            plt.plot(xdata, accum, color='black')
            plt.fill_between(xdata, prev, accum, facecolor=g.patch.get_fc(), alpha=0.3)
            prev = accum.copy()

    for h in np.argwhere(context.unserved):
        plt.plot([h[0]], [ymax], "yv", markersize=15, color='red')

    if not filename:
        plt.show()
    else:
        plt.savefig(filename)


def run(context, starthour=0, endhour=hours):
    "Run the simulation without a plot."

    if not isinstance(context.regions, list):
        raise ValueError('regions is not a list')
    _sim(context, starthour, endhour)

    # Calculate some summary statistics.
    agg_demand = context.demand.sum(axis=0)
    context.spilled_energy = context.spill.sum()
    context.accum = context.generation.sum(axis=0)
    context.unserved_energy = (agg_demand - context.accum).sum()
    context.unserved_energy = max(0, round(context.unserved_energy, 0))
    context.unserved = (agg_demand - context.accum) > 0.1
    context.unserved_hours = context.unserved.sum()
    context.unserved_percent = float(context.unserved_energy / agg_demand.sum()) * 100

    shortfall = [agg_demand[hr] - context.accum[hr]
                 for hr in np.argwhere(context.unserved)]
    if len(shortfall) == 0:
        context.shortfalls = (None, None)
    else:
        context.shortfalls = (round(min(shortfall)), round(max(shortfall)))
    return context


def _format_date(x, pos=None):
    "Pretty printer for dates/times."
    import datetime
    delta = datetime.timedelta(hours=x)
    t = datetime.datetime(2010, 1, 1) + delta
    return t.strftime('%b %d %Hh')
